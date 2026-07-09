from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


@dataclass(frozen=True)
class SavgolCandidate:
    window_length: int
    polyorder: int
    loo_rmse: float
    acceleration_roughness: float
    complexity: float
    residual_rmse: float
    score: float
    error_score: float
    compute_cost: float


@dataclass(frozen=True)
class SavgolOptimizationResult:
    window_length: int
    polyorder: int
    window_min: int
    window_max: int
    polyorder_min: int
    polyorder_max: int
    score: float
    minimum_error_score: float
    selected_error_score: float
    compute_cost: float
    error_tolerance: float
    candidates: Tuple[SavgolCandidate, ...]
    recommended_window_range: Tuple[int, int]
    recommended_polyorder_range: Tuple[int, int]
    message: str


PROFILE_CONFIG: Dict[str, Dict[str, float]] = {
    "balanced": {"loo": 0.40, "roughness": 0.40, "residual": 0.20, "tolerance": 0.010, "roughness_tolerance": 0.50},
    "constant_acceleration": {"loo": 0.12, "roughness": 0.80, "residual": 0.08, "tolerance": 0.005, "roughness_tolerance": 0.05},
    "fast_event": {"loo": 0.70, "roughness": 0.05, "residual": 0.25, "tolerance": 0.004, "roughness_tolerance": 5.00},
}


def _make_odd(value: int, direction: str = "down") -> int:
    if value % 2 == 1:
        return value
    return value - 1 if direction == "down" else value + 1


def _safe_range_scale(*arrays: np.ndarray) -> float:
    values = np.concatenate([np.asarray(a, dtype=float) for a in arrays])
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 1.0
    scale = float(np.percentile(values, 95) - np.percentile(values, 5))
    return scale if scale > 1e-12 else 1.0


def _rms(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("inf")
    return float(np.sqrt(np.mean(values**2)))


def _normalize_metric(values: List[float]) -> List[float]:
    finite = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if finite.size == 0:
        return [1.0 for _ in values]
    low, high = float(np.min(finite)), float(np.max(finite))
    if high - low < 1e-12:
        return [0.0 if np.isfinite(v) else 1.0 for v in values]
    return [float((v - low) / (high - low)) if np.isfinite(v) else 1.0 for v in values]


def estimate_savgol_bounds(
    n_points: int,
    min_window: int = 5,
    max_window: int = 51,
    min_polyorder: int = 2,
    max_polyorder: int = 4,
) -> Optional[Tuple[int, int, int, int]]:
    """Return admissible bounds for Savitzky-Golay parameters.

    The app estimates acceleration, so the recommended minimum polynomial
    order is 2. Window length must be odd, greater than the polynomial order,
    and not larger than the number of sampled points.
    """
    if n_points < 5:
        return None

    window_min = max(5, int(min_window))
    window_min = _make_odd(window_min, "up")

    window_max = min(int(max_window), int(n_points))
    window_max = _make_odd(window_max, "down")

    if window_max < window_min:
        return None

    polyorder_min = max(0, int(min_polyorder))
    polyorder_max = min(int(max_polyorder), window_max - 1)

    if polyorder_max < polyorder_min:
        return None

    return window_min, window_max, polyorder_min, polyorder_max


def candidate_grid(
    n_points: int,
    min_window: int = 5,
    max_window: int = 51,
    min_polyorder: int = 2,
    max_polyorder: int = 4,
) -> List[Tuple[int, int]]:
    bounds = estimate_savgol_bounds(
        n_points,
        min_window=min_window,
        max_window=max_window,
        min_polyorder=min_polyorder,
        max_polyorder=max_polyorder,
    )
    if bounds is None:
        return []

    window_min, window_max, polyorder_min, polyorder_max = bounds
    candidates: List[Tuple[int, int]] = []
    for w in range(window_min, window_max + 1, 2):
        for d in range(polyorder_min, min(polyorder_max, w - 1) + 1):
            if w > d:
                candidates.append((w, d))
    return candidates


def _local_leave_one_out_rmse(values: np.ndarray, window_length: int, polyorder: int) -> float:
    values = np.asarray(values, dtype=float)
    n = values.size
    m = window_length // 2
    if n < window_length or window_length <= polyorder:
        return float("inf")

    offsets = np.arange(-m, m + 1, dtype=float)
    keep = offsets != 0
    vandermonde = np.vander(offsets[keep], polyorder + 1, increasing=True)
    errors = []

    for i in range(m, n - m):
        segment = values[i - m : i + m + 1]
        if not np.all(np.isfinite(segment)):
            continue
        coeffs, *_ = np.linalg.lstsq(vandermonde, segment[keep], rcond=None)
        prediction = coeffs[0]
        errors.append(values[i] - prediction)

    return _rms(np.asarray(errors, dtype=float))


def _candidate_raw_metrics(
    x: np.ndarray,
    y: np.ndarray,
    dt: float,
    window_length: int,
    polyorder: int,
) -> Tuple[float, float, float, float]:
    loo_x = _local_leave_one_out_rmse(x, window_length, polyorder)
    loo_y = _local_leave_one_out_rmse(y, window_length, polyorder)
    loo_rmse = float(np.sqrt(np.nanmean([loo_x**2, loo_y**2])))

    sx = savgol_filter(x, window_length=window_length, polyorder=polyorder, deriv=0)
    sy = savgol_filter(y, window_length=window_length, polyorder=polyorder, deriv=0)
    ax = savgol_filter(x, window_length=window_length, polyorder=polyorder, deriv=2, delta=dt)
    ay = savgol_filter(y, window_length=window_length, polyorder=polyorder, deriv=2, delta=dt)

    residual_rmse = float(np.sqrt(np.mean((x - sx) ** 2 + (y - sy) ** 2)))
    jerk_x = np.diff(ax) / dt if ax.size > 1 else np.array([0.0])
    jerk_y = np.diff(ay) / dt if ay.size > 1 else np.array([0.0])
    acceleration_roughness = float(np.sqrt(np.mean(jerk_x**2 + jerk_y**2)))
    complexity = float((polyorder + 1) / window_length)
    return loo_rmse, acceleration_roughness, complexity, residual_rmse


def _compute_cost(window_length: int, polyorder: int) -> float:
    """Approximate relative cost for one Savitzky-Golay pass.

    The filter solves local polynomial fits; for comparison among candidates
    in the same video, cost grows mainly with window size and polynomial order.
    """
    return float(window_length * (polyorder + 1) ** 2)


def optimize_savgol_parameters(
    t: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    profile: str = "balanced",
    min_window: int = 5,
    max_window: int = 51,
    min_polyorder: int = 2,
    max_polyorder: int = 4,
    near_best_tolerance: Optional[float] = None,
) -> Optional[SavgolOptimizationResult]:
    """Estimate Savitzky-Golay parameters from the raw tracked trajectory.

    The optimizer uses a two-stage decision:
    1. estimate the numerical/physical error of each candidate;
    2. choose the lowest computational cost among candidates whose error is
       effectively indistinguishable from the minimum error for the loaded video.
    """
    t = np.asarray(t, dtype=float)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(t) & np.isfinite(x) & np.isfinite(y)
    t, x, y = t[valid], x[valid], y[valid]

    if t.size < 5:
        return None

    bounds = estimate_savgol_bounds(
        t.size,
        min_window=min_window,
        max_window=max_window,
        min_polyorder=min_polyorder,
        max_polyorder=max_polyorder,
    )
    if bounds is None:
        return None

    diffs = np.diff(t)
    dt = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else 1.0
    dt = dt if dt > 0 else 1.0

    grid = candidate_grid(
        t.size,
        min_window=min_window,
        max_window=max_window,
        min_polyorder=min_polyorder,
        max_polyorder=max_polyorder,
    )
    if not grid:
        return None

    span = _safe_range_scale(x, y)
    raw_metrics = []
    for w, d in grid:
        try:
            loo, rough, complexity, residual = _candidate_raw_metrics(x, y, dt, w, d)
            raw_metrics.append((w, d, loo / span, rough, complexity, residual / span))
        except Exception:
            raw_metrics.append((w, d, float("inf"), float("inf"), float("inf"), float("inf")))

    loo_norm = _normalize_metric([row[2] for row in raw_metrics])
    rough_norm = _normalize_metric([row[3] for row in raw_metrics])
    residual_norm = _normalize_metric([row[5] for row in raw_metrics])

    config = PROFILE_CONFIG.get(profile, PROFILE_CONFIG["balanced"])
    error_tolerance = config["tolerance"] if near_best_tolerance is None else float(near_best_tolerance)
    candidates: List[SavgolCandidate] = []
    for row, loo_s, rough_s, residual_s in zip(raw_metrics, loo_norm, rough_norm, residual_norm):
        w, d, loo, rough, complexity, residual = row
        error_score = config["loo"] * loo_s + config["roughness"] * rough_s + config["residual"] * residual_s
        compute_cost = _compute_cost(w, d)
        candidates.append(
            SavgolCandidate(
                window_length=w,
                polyorder=d,
                loo_rmse=loo,
                acceleration_roughness=rough,
                complexity=complexity,
                residual_rmse=residual,
                score=float(error_score),
                error_score=float(error_score),
                compute_cost=float(compute_cost),
            )
        )

    candidates = [c for c in candidates if np.isfinite(c.error_score)]
    if not candidates:
        return None

    candidates.sort(key=lambda c: (c.error_score, c.compute_cost, c.window_length, c.polyorder))
    minimum_error = candidates[0].error_score
    threshold = minimum_error * (1.0 + error_tolerance) + 1e-12
    equivalent_error = [candidate for candidate in candidates if candidate.error_score <= threshold]
    finite_roughness = [candidate.acceleration_roughness for candidate in candidates if np.isfinite(candidate.acceleration_roughness)]
    minimum_roughness = min(finite_roughness) if finite_roughness else float("inf")
    roughness_threshold = minimum_roughness * (1.0 + config["roughness_tolerance"]) + 1e-12
    stable_equivalent_error = [
        candidate for candidate in equivalent_error
        if candidate.acceleration_roughness <= roughness_threshold
    ]
    selectable = stable_equivalent_error or equivalent_error
    best = sorted(selectable, key=lambda c: (c.compute_cost, c.error_score, c.window_length, c.polyorder))[0]

    window_range = (best.window_length, best.window_length)
    polyorder_range = (best.polyorder, best.polyorder)
    window_min, window_max, poly_min, poly_max = bounds
    message = (
        f"Par ótimo exato para este vídeo: janela {best.window_length} e ordem {best.polyorder}. "
        f"Critério: menor custo computacional mantendo erro dentro de {error_tolerance:.1%} do mínimo observado "
        "e aceleração estável para o perfil selecionado."
    )

    return SavgolOptimizationResult(
        window_length=best.window_length,
        polyorder=best.polyorder,
        window_min=window_min,
        window_max=window_max,
        polyorder_min=poly_min,
        polyorder_max=poly_max,
        score=best.score,
        minimum_error_score=float(minimum_error),
        selected_error_score=float(best.error_score),
        compute_cost=float(best.compute_cost),
        error_tolerance=float(error_tolerance),
        candidates=tuple(candidates),
        recommended_window_range=window_range,
        recommended_polyorder_range=polyorder_range,
        message=message,
    )


def apply_savgol_kinematics(
    df: pd.DataFrame,
    fps: float,
    window_length: int,
    polyorder: int,
) -> pd.DataFrame:
    """Apply smoothing and numerical derivatives to a tracked trajectory."""
    df = df.copy()
    n = len(df)
    dt = 1.0 / fps if fps and fps > 0 else 1.0
    window_length = int(window_length)
    polyorder = int(polyorder)

    if window_length % 2 == 0:
        window_length -= 1
    if n < window_length or window_length <= polyorder:
        delta_t = df["tempo_s"].diff()
        df["vx_um_s"] = df["pos_x_um"].diff() / delta_t
        df["vy_um_s"] = df["pos_y_um"].diff() / delta_t
        df["ax_um_s2"] = df["vx_um_s"].diff() / delta_t
        df["ay_um_s2"] = df["vy_um_s"].diff() / delta_t
        return df

    pos_x_raw = df["pos_x_um"].to_numpy(dtype=float)
    pos_y_raw = df["pos_y_um"].to_numpy(dtype=float)

    df["vx_um_s"] = savgol_filter(
        pos_x_raw, window_length=window_length, polyorder=polyorder, deriv=1, delta=dt
    )
    df["vy_um_s"] = savgol_filter(
        pos_y_raw, window_length=window_length, polyorder=polyorder, deriv=1, delta=dt
    )
    df["ax_um_s2"] = savgol_filter(
        pos_x_raw, window_length=window_length, polyorder=polyorder, deriv=2, delta=dt
    )
    df["ay_um_s2"] = savgol_filter(
        pos_y_raw, window_length=window_length, polyorder=polyorder, deriv=2, delta=dt
    )
    df["pos_x_um"] = savgol_filter(
        pos_x_raw, window_length=window_length, polyorder=polyorder, deriv=0
    )
    df["pos_y_um"] = savgol_filter(
        pos_y_raw, window_length=window_length, polyorder=polyorder, deriv=0
    )
    return df
