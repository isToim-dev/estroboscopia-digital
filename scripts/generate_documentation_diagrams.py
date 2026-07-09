from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def draw_box(ax, xy, width, height, title, body, color="#E7F0FF"):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.2,
        edgecolor="#2F5597",
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(xy[0] + width / 2, xy[1] + height * 0.68, title, ha="center", va="center", fontsize=10.5, weight="bold", color="#172033")
    ax.text(xy[0] + width / 2, xy[1] + height * 0.34, body, ha="center", va="center", fontsize=8.2, color="#344054", linespacing=1.15)


def arrow(ax, start, end, color="#4B5A6A"):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.35,
            color=color,
        )
    )


def setup_canvas(title):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.955, title, ha="center", va="center", fontsize=17, weight="bold", color="#123C69")
    return fig, ax


def save(fig, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / filename, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def module_flow():
    fig, ax = setup_canvas("Fluxo dos Módulos do Aplicativo")
    boxes = [
        ((0.05, 0.73), "Entrada", "Streamlit\nstroboscopic_app.py", "#F7FAFC"),
        ((0.29, 0.73), "Estado", "app_state.py\napp_config.py", "#F7FAFC"),
        ((0.53, 0.73), "Amostras", "sample_videos.py\nminiaturas e FPS", "#F7FAFC"),
        ((0.77, 0.73), "Interface", "ui_controls.py\nseletores visuais", "#F7FAFC"),
        ((0.05, 0.43), "Calibração", "Dois pontos ou\nhomografia métrica", "#EAF7EA"),
        ((0.29, 0.43), "Rastreamento", "OpenCV CSRT\nvideo_processing.py", "#EAF7EA"),
        ((0.53, 0.43), "Cinemática", "posição, velocidade\ne aceleração", "#EAF7EA"),
        ((0.77, 0.43), "Filtro", "Savitzky-Golay\nreverso", "#EAF7EA"),
        ((0.17, 0.13), "Visualização", "gráficos, vetores e\nimagem estroboscópica", "#FFF4E5"),
        ((0.43, 0.13), "Dados", "CSV com contrato\ncinemático", "#FFF4E5"),
        ((0.69, 0.13), "Relatório", "PDF didático\nreport_generation.py", "#FFF4E5"),
    ]
    for xy, title, body, color in boxes:
        draw_box(ax, xy, 0.18, 0.14, title, body, color)
    for x in [0.23, 0.47, 0.71]:
        arrow(ax, (x, 0.80), (x + 0.05, 0.80))
    for x in [0.14, 0.38, 0.62, 0.86]:
        arrow(ax, (x, 0.73), (x, 0.57))
    for x in [0.23, 0.47, 0.71]:
        arrow(ax, (x, 0.50), (x + 0.05, 0.50))
    arrow(ax, (0.38, 0.43), (0.26, 0.27))
    arrow(ax, (0.62, 0.43), (0.52, 0.27))
    arrow(ax, (0.86, 0.43), (0.78, 0.27))
    ax.text(0.5, 0.055, "Contrato central: tabela com frame, tempo, posições, velocidades e acelerações.", ha="center", fontsize=10, color="#45515F")
    save(fig, "fluxo_modulos_app.png")


def method_flow():
    fig, ax = setup_canvas("Método Matemático da Estroboscopia Digital")
    boxes = [
        ((0.08, 0.74), "1. Vídeo", "Upload ou galeria\nFPS e intervalo", "#E7F0FF"),
        ((0.32, 0.74), "2. Objeto", "caixa inicial\ncentro do objeto", "#E7F0FF"),
        ((0.56, 0.74), "3. Escala", "dois pontos ou\nplano métrico", "#E7F0FF"),
        ((0.08, 0.48), "4. Rastreio", "CSRT em frames\nnão distorcidos", "#EAF7EA"),
        ((0.32, 0.48), "5. Coordenadas", "pixels -> unidade real\nX(t), Y(t)", "#EAF7EA"),
        ((0.56, 0.48), "6. Suavização", "Savitzky-Golay\nw e d otimizados", "#EAF7EA"),
        ((0.20, 0.20), "7. Derivadas", "v = ds/dt\na = d²s/dt²", "#FFF4E5"),
        ((0.50, 0.20), "8. Modelos", "linear/quadrático\nR², RMSE e gravidade", "#FFF4E5"),
        ((0.78, 0.20), "9. Produtos", "imagem, gráficos\nCSV e PDF", "#FFF4E5"),
    ]
    for xy, title, body, color in boxes:
        draw_box(ax, xy, 0.19, 0.14, title, body, color)
    arrow(ax, (0.27, 0.81), (0.31, 0.81))
    arrow(ax, (0.51, 0.81), (0.55, 0.81))
    arrow(ax, (0.17, 0.74), (0.17, 0.62))
    arrow(ax, (0.41, 0.74), (0.41, 0.62))
    arrow(ax, (0.65, 0.74), (0.65, 0.62))
    arrow(ax, (0.27, 0.55), (0.31, 0.55))
    arrow(ax, (0.51, 0.55), (0.55, 0.55))
    arrow(ax, (0.41, 0.48), (0.31, 0.34))
    arrow(ax, (0.65, 0.48), (0.59, 0.34))
    arrow(ax, (0.39, 0.27), (0.49, 0.27))
    arrow(ax, (0.69, 0.27), (0.77, 0.27))
    ax.text(0.5, 0.07, "A robustez do método matemático depende da preservação destes contratos entre blocos.", ha="center", fontsize=10, color="#45515F")
    save(fig, "fluxo_metodo_matematico.png")


def data_contract_flow():
    fig, ax = setup_canvas("Contrato de Dados: da Medição ao Relatório")
    draw_box(ax, (0.08, 0.68), 0.22, 0.15, "Entrada bruta", "frame\npos_x_px\npos_y_px\nis_stamp", "#E7F0FF")
    draw_box(ax, (0.39, 0.68), 0.22, 0.15, "Calibração", "scale_factor\norigem\nhomografia opcional", "#EAF7EA")
    draw_box(ax, (0.70, 0.68), 0.22, 0.15, "Cinemática", "tempo_s\npos_x_um\npos_y_um", "#EAF7EA")
    draw_box(ax, (0.24, 0.34), 0.22, 0.15, "Derivadas", "vx_um_s\nvy_um_s\nax_um_s2\nay_um_s2", "#FFF4E5")
    draw_box(ax, (0.56, 0.34), 0.22, 0.15, "Saídas", "gráficos\nCSV\nPDF\nimagens", "#FFF4E5")
    arrow(ax, (0.30, 0.755), (0.39, 0.755))
    arrow(ax, (0.61, 0.755), (0.70, 0.755))
    arrow(ax, (0.81, 0.68), (0.69, 0.49))
    arrow(ax, (0.46, 0.415), (0.56, 0.415))
    ax.text(0.5, 0.18, "Qualquer novo rastreador ou biblioteca deve entregar a mesma tabela cinemática.", ha="center", fontsize=10.5, color="#45515F")
    save(fig, "contrato_dados_pipeline.png")


if __name__ == "__main__":
    module_flow()
    method_flow()
    data_contract_flow()
    print(f"Diagramas gerados em: {OUTPUT_DIR}")
