from io import BytesIO

import cv2
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline


def _numeric_xy(df, x_col, y_col):
    x = df[x_col].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    return x[valid], y[valid]


def _numeric_time_series(df, y_col):
    t = df["tempo_s"].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    valid = np.isfinite(t) & np.isfinite(y)
    return t[valid], y[valid]


def _plot_empty_axis(ax, message):
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, color="#667085")
    ax.set_xticks([])
    ax.set_yticks([])


def _plot_trajectory(ax, x, y):
    if x.size == 0:
        _plot_empty_axis(ax, "Dados insuficientes para gerar a trajetória.")
        return

    ax.scatter(x, y, label="Pontos observados", color="blue", alpha=0.6, s=10)
    if x.size <= 3:
        ax.plot(x, y, label="Linha de trajetória", color="red", linewidth=2, alpha=0.8)
        return

    try:
        distance = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
        keep = np.concatenate([[True], np.diff(distance) > 1e-9])
        s = distance[keep]
        x_s = x[keep]
        y_s = y[keep]
        if s.size <= 3 or np.isclose(s[-1], s[0]):
            raise ValueError("Trajetória sem variação suficiente para spline paramétrica.")
        spline_order = min(3, s.size - 1)
        s_grid = np.linspace(s.min(), s.max(), 500)
        spline_x = make_interp_spline(s, x_s, k=spline_order)
        spline_y = make_interp_spline(s, y_s, k=spline_order)
        ax.plot(spline_x(s_grid), spline_y(s_grid), label="Curva de trajetória (spline)", color="red", linewidth=2)
    except Exception:
        ax.plot(x, y, label="Linha de trajetória", color="red", linewidth=2, alpha=0.8)


def _plot_time_series(ax, df, column, label, color, marker, linestyle):
    t, values = _numeric_time_series(df, column)
    if t.size == 0:
        _plot_empty_axis(ax, "Dados insuficientes para este gráfico.")
        return
    ax.plot(t, values, label=label, color=color, marker=marker, linestyle=linestyle)
    ax.legend()


def plotar_graficos(df):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(15, 18), constrained_layout=True)
    gs = gridspec.GridSpec(3, 2, figure=fig)

    ax1 = fig.add_subplot(gs[0, :])
    x, y = _numeric_xy(df, "pos_x_um", "pos_y_um")
    _plot_trajectory(ax1, x, y)
    ax1.set_title("Gráfico de trajetória físico-espacial", fontsize=16)
    ax1.set_xlabel("Posição X (u.m.)")
    ax1.set_ylabel("Posição Y (u.m.)")
    ax1.legend()
    if x.size > 1 and y.size > 1 and np.ptp(x) > 0 and np.ptp(y) > 0:
        ax1.set_aspect("equal", adjustable="datalim")

    ax2 = fig.add_subplot(gs[1, 0])
    _plot_time_series(ax2, df, "vx_um_s", "Velocidade em X", "green", "o", "--")
    ax2.set_title("Velocidade na direção X vs. tempo", fontsize=16)
    ax2.set_xlabel("Tempo (s)")
    ax2.set_ylabel("Velocidade (u.m./s)")

    ax3 = fig.add_subplot(gs[1, 1])
    _plot_time_series(ax3, df, "vy_um_s", "Velocidade em Y", "orange", "o", "--")
    ax3.set_title("Velocidade na direção Y vs. tempo", fontsize=16)
    ax3.set_xlabel("Tempo (s)")
    ax3.set_ylabel("Velocidade (u.m./s)")

    ax4 = fig.add_subplot(gs[2, 0])
    _plot_time_series(ax4, df, "ax_um_s2", "Aceleração em X", "purple", "^", "-")
    ax4.set_title("Aceleração na direção X vs. tempo", fontsize=16)
    ax4.set_xlabel("Tempo (s)")
    ax4.set_ylabel("Aceleração (u.m./s²)")

    ax5 = fig.add_subplot(gs[2, 1])
    _plot_time_series(ax5, df, "ay_um_s2", "Aceleração em Y", "brown", "^", "-")
    ax5.set_title("Aceleração na direção Y vs. tempo", fontsize=16)
    ax5.set_xlabel("Tempo (s)")
    ax5.set_ylabel("Aceleração (u.m./s²)")

    return fig


def desenhar_grade_cartesiana(frame, intervalo=100):
    frame_com_grade = frame.copy()
    altura, largura, _ = frame_com_grade.shape
    cor_linha, cor_texto = (0, 255, 0, 200), (0, 255, 0)
    fonte, escala_fonte = cv2.FONT_HERSHEY_SIMPLEX, 0.5
    for x in range(intervalo, largura, intervalo):
        cv2.line(frame_com_grade, (x, 0), (x, altura), cor_linha, 1)
        cv2.putText(frame_com_grade, str(x), (x - 10, altura - 10), fonte, escala_fonte, cor_texto, 1)
    for y in range(intervalo, altura, intervalo):
        pos_y_imagem = altura - y
        cv2.line(frame_com_grade, (0, pos_y_imagem), (largura, pos_y_imagem), cor_linha, 1)
        cv2.putText(frame_com_grade, str(y), (10, pos_y_imagem + 5), fonte, escala_fonte, cor_texto, 1)
    return frame_com_grade


def desenhar_vetores_velocidade(imagem_estroboscopica_original, df_analisado, scale_vetor, max_len_vetor, cor_vetor, espessura_vetor):
    imagem_com_vetores = imagem_estroboscopica_original.copy()
    x_col = "view_x_px" if "view_x_px" in df_analisado.columns else "pos_x_px"
    y_col = "view_y_px" if "view_y_px" in df_analisado.columns else "pos_y_px"
    if {"view_x_px", "view_y_px", "tempo_s"}.issubset(df_analisado.columns) and len(df_analisado) > 1:
        df_analisado = df_analisado.copy()
        time = df_analisado["tempo_s"].to_numpy(dtype=float)
        if np.ptp(time) > 0:
            df_analisado["_vx_view_px_s"] = np.gradient(df_analisado["view_x_px"].to_numpy(dtype=float), time)
            df_analisado["_vy_view_px_s"] = np.gradient(df_analisado["view_y_px"].to_numpy(dtype=float), time)

    height, width = imagem_com_vetores.shape[:2]
    for _, row in df_analisado.iterrows():
        p_start_px = (int(row[x_col]), int(row[y_col]))
        if not (0 <= p_start_px[0] < width and 0 <= p_start_px[1] < height):
            continue
        if "_vx_view_px_s" in df_analisado.columns and "_vy_view_px_s" in df_analisado.columns:
            vx, vy = row["_vx_view_px_s"], row["_vy_view_px_s"]
            invert_y = False
        else:
            vx, vy = row["vx_um_s"], row["vy_um_s"]
            invert_y = True
        vel_magnitude = np.sqrt(vx**2 + vy**2)
        if not np.isnan(vx) and not np.isnan(vy) and vel_magnitude > 0:
            arrow_length_pixels = min(max_len_vetor, vel_magnitude * scale_vetor)
            direction_x, direction_y = vx / vel_magnitude, vy / vel_magnitude
            y_direction = -direction_y if invert_y else direction_y
            p_end_px = (
                int(p_start_px[0] + direction_x * arrow_length_pixels),
                int(p_start_px[1] + y_direction * arrow_length_pixels),
            )
            cv2.arrowedLine(imagem_com_vetores, p_start_px, p_end_px, cor_vetor, espessura_vetor, tipLength=0.3)

    _, buffer = cv2.imencode(".PNG", imagem_com_vetores)
    return BytesIO(buffer).getvalue()
