from dataclasses import dataclass
from typing import Iterable, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class MetricHomography:
    matrix: np.ndarray
    output_size: Tuple[int, int]
    pixels_per_unit: float
    scale_factor: float
    real_width: float
    real_height: float
    destination_points: np.ndarray


def polygon_area(points: Iterable[Iterable[float]]) -> float:
    pts = np.asarray(points, dtype=float)
    x = pts[:, 0]
    y = pts[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def build_metric_homography(
    source_points: Iterable[Iterable[float]],
    real_width: float,
    real_height: float,
    pixels_per_unit: float = 80.0,
    max_output_side: int = 3200,
) -> MetricHomography:
    """Build a homography that maps an oblique court rectangle to metric plane pixels.

    The four source points must be ordered as upper-left, upper-right,
    lower-right, lower-left in image coordinates. The destination plane uses
    pixels_per_unit pixels for each real-world unit supplied by the user.
    """
    pts_src = np.asarray(source_points, dtype=np.float32)
    if pts_src.shape != (4, 2):
        raise ValueError("A homografia exige exatamente quatro pontos 2D.")
    if polygon_area(pts_src) < 10:
        raise ValueError("Os quatro pontos marcados estão degenerados ou próximos demais.")
    if real_width <= 0 or real_height <= 0:
        raise ValueError("Largura e altura reais devem ser positivas.")
    if pixels_per_unit <= 0:
        raise ValueError("A resolução em pixels por unidade deve ser positiva.")

    width_px = max(2, int(round(real_width * pixels_per_unit)))
    height_px = max(2, int(round(real_height * pixels_per_unit)))

    largest_side = max(width_px, height_px)
    if largest_side > max_output_side:
        reduction = max_output_side / largest_side
        pixels_per_unit *= reduction
        width_px = max(2, int(round(real_width * pixels_per_unit)))
        height_px = max(2, int(round(real_height * pixels_per_unit)))

    pts_dst = np.array(
        [
            [0, 0],
            [width_px - 1, 0],
            [width_px - 1, height_px - 1],
            [0, height_px - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
    scale_factor = real_width / (width_px - 1) if width_px > 1 else 1.0 / pixels_per_unit

    return MetricHomography(
        matrix=matrix,
        output_size=(width_px, height_px),
        pixels_per_unit=float(pixels_per_unit),
        scale_factor=float(scale_factor),
        real_width=float(real_width),
        real_height=float(real_height),
        destination_points=pts_dst,
    )


def estimate_pixels_per_unit(
    source_points: Iterable[Iterable[float]],
    real_width: float,
    real_height: float,
    min_pixels_per_unit: int = 20,
    max_pixels_per_unit: int = 180,
    max_output_side: int = 1800,
) -> int:
    """Estimate a practical plane resolution from the marked quadrilateral.

    The value is the density of the rectified metric plane in pixels per
    real-world unit. It controls only the working resolution of the metric
    plane, not the mathematical homography itself.
    """
    pts = np.asarray(source_points, dtype=float)
    if pts.shape != (4, 2) or real_width <= 0 or real_height <= 0:
        return 80

    top = np.linalg.norm(pts[1] - pts[0]) / real_width
    bottom = np.linalg.norm(pts[2] - pts[3]) / real_width
    right = np.linalg.norm(pts[2] - pts[1]) / real_height
    left = np.linalg.norm(pts[3] - pts[0]) / real_height
    candidates = [value for value in (top, bottom, right, left) if np.isfinite(value) and value > 0]
    if not candidates:
        return 80

    estimated = float(np.median(candidates))
    if max(real_width, real_height) > 0:
        estimated = min(estimated, max_output_side / max(real_width, real_height))
    return int(round(np.clip(estimated, min_pixels_per_unit, max_pixels_per_unit)))


def warp_metric_plane(frame: np.ndarray, calibration: MetricHomography) -> np.ndarray:
    return cv2.warpPerspective(frame, calibration.matrix, calibration.output_size)


def aplicar_homografia(frame, pts_origem, largura_real, altura_real, pixels_por_unidade=80.0):
    """Corrige a perspectiva e preserva escala métrica no plano retificado."""
    calibration = build_metric_homography(
        pts_origem,
        largura_real,
        altura_real,
        pixels_per_unit=pixels_por_unidade,
    )
    frame_corrigido = warp_metric_plane(frame, calibration)
    meta = {
        "real_width": calibration.real_width,
        "real_height": calibration.real_height,
        "pixels_per_unit": calibration.pixels_per_unit,
        "scale_factor": calibration.scale_factor,
        "output_width": calibration.output_size[0],
        "output_height": calibration.output_size[1],
    }
    return frame_corrigido, calibration.matrix, calibration.output_size, meta
