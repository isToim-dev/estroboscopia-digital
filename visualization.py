from io import BytesIO

import cv2
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline


def plotar_graficos(df):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(15, 18))
    gs = gridspec.GridSpec(3, 2, figure=fig)
    fig.tight_layout(pad=6.0)

    ax1 = fig.add_subplot(gs[0, :])
    x, y = df["pos_x_um"].to_numpy(), df["pos_y_um"].to_numpy()
    ax1.scatter(x, y, label="Pontos observados", color="blue", alpha=0.6, s=10)
    if len(x) > 3:
        try:
            sorted_indices = np.argsort(x)
            x_s, y_s = x[sorted_indices], y[sorted_indices]
            spline = make_interp_spline(x_s, y_s)
            x_grid = np.linspace(x_s.min(), x_s.max(), 500)
            ax1.plot(x_grid, spline(x_grid), label="Curva de trajetória (spline)", color="red", linewidth=2)
        except Exception:
            ax1.plot(x, y, label="Linha de trajetória", color="red", linewidth=2, alpha=0.8)
    ax1.set_title("Gráfico de trajetória físico-espacial", fontsize=16)
    ax1.set_xlabel("Posição X (u.m.)")
    ax1.set_ylabel("Posição Y (u.m.)")
    ax1.legend()
    ax1.set_aspect("equal", adjustable="box")

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(df["tempo_s"], df["vx_um_s"], label="Velocidade em X", color="green", marker="o", linestyle="--")
    ax2.set_title("Velocidade na direção X vs. tempo", fontsize=16)
    ax2.set_xlabel("Tempo (s)")
    ax2.set_ylabel("Velocidade (u.m./s)")
    ax2.legend()

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df["tempo_s"], df["vy_um_s"], label="Velocidade em Y", color="orange", marker="o", linestyle="--")
    ax3.set_title("Velocidade na direção Y vs. tempo", fontsize=16)
    ax3.set_xlabel("Tempo (s)")
    ax3.set_ylabel("Velocidade (u.m./s)")
    ax3.legend()

    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(df["tempo_s"], df["ax_um_s2"], label="Aceleração em X", color="purple", marker="^", linestyle="-")
    ax4.set_title("Aceleração na direção X vs. tempo", fontsize=16)
    ax4.set_xlabel("Tempo (s)")
    ax4.set_ylabel("Aceleração (u.m./s²)")
    ax4.legend()

    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(df["tempo_s"], df["ay_um_s2"], label="Aceleração em Y", color="brown", marker="^", linestyle="-")
    ax5.set_title("Aceleração na direção Y vs. tempo", fontsize=16)
    ax5.set_xlabel("Tempo (s)")
    ax5.set_ylabel("Aceleração (u.m./s²)")
    ax5.legend()

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
    for _, row in df_analisado.iterrows():
        p_start_px = (int(row["pos_x_px"]), int(row["pos_y_px"]))
        vx, vy = row["vx_um_s"], row["vy_um_s"]
        vel_magnitude = np.sqrt(vx**2 + vy**2)
        if not np.isnan(vx) and not np.isnan(vy) and vel_magnitude > 0:
            arrow_length_pixels = min(max_len_vetor, vel_magnitude * scale_vetor)
            direction_x, direction_y = vx / vel_magnitude, vy / vel_magnitude
            p_end_px = (
                int(p_start_px[0] + direction_x * arrow_length_pixels),
                int(p_start_px[1] - direction_y * arrow_length_pixels),
            )
            cv2.arrowedLine(imagem_com_vetores, p_start_px, p_end_px, cor_vetor, espessura_vetor, tipLength=0.3)

    _, buffer = cv2.imencode(".PNG", imagem_com_vetores)
    return BytesIO(buffer).getvalue()
