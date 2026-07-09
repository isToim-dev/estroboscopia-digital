from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_fonts():
    regular = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ReportFont", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportFontBold", str(bold)))
        return "ReportFont", "ReportFontBold"
    return "Helvetica", "Helvetica-Bold"


def _styles():
    font_name, bold_font = _register_fonts()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleBR",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172033"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionBR",
            parent=styles["Heading1"],
            fontName=bold_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#123C69"),
            spaceBefore=8,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyBR",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9.2,
            leading=12.5,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#172033"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallBR",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#45515f"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetricBR",
            parent=styles["BodyText"],
            fontName=bold_font,
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#0f5132"),
            spaceAfter=5,
        )
    )
    return styles, font_name


def _paragraph(text, styles, style="BodyBR"):
    return Paragraph(str(text).replace("\n", "<br/>"), styles[style])


def _image_from_bytes(image_bytes, width_cm=16.0):
    image = Image(BytesIO(image_bytes))
    target_width = width_cm * cm
    ratio = target_width / image.imageWidth
    image.drawWidth = target_width
    image.drawHeight = image.imageHeight * ratio
    return image


def _image_cell(image_bytes, width_cm):
    image = _image_from_bytes(image_bytes, width_cm)
    image.hAlign = "CENTER"
    return image


def _fig_to_png_bytes(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def _latex_to_png_bytes(expression, width=7.2, height=0.9, fontsize=13):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off")
    ax.text(0.5, 0.5, expression, ha="center", va="center", fontsize=fontsize)
    fig.tight_layout(pad=0.05)
    image_bytes = _fig_to_png_bytes(fig)
    plt.close(fig)
    return image_bytes


def _table(rows, styles, widths=(5.5, 9.7)):
    data = [[_paragraph(left, styles, "SmallBR"), _paragraph(right, styles, "SmallBR")] for left, right in rows]
    table = Table(data, colWidths=[widths[0] * cm, widths[1] * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7F0FF")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _math_table(rows, styles, widths=(4.7, 10.5)):
    data = []
    for label, expression in rows:
        data.append([
            _paragraph(label, styles, "SmallBR"),
            _image_cell(_latex_to_png_bytes(expression, width=6.8, height=0.55, fontsize=11.5), widths[1] - 0.8),
        ])
    table = Table(data, colWidths=[widths[0] * cm, widths[1] * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7F0FF")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _formula_list(rows, styles):
    data = []
    for number, name, expression in rows:
        data.append(
            [
                _paragraph(f"<b>({number}) {name}</b>", styles, "SmallBR"),
                _image_cell(_latex_to_png_bytes(expression, width=9.4, height=1.0, fontsize=18), 10.2),
            ]
        )
    table = Table(data, colWidths=[4.6 * cm, 10.6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F6FC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _fit_model(t, values, degree):
    coeffs = np.polyfit(t, values, degree)
    poly = np.poly1d(coeffs)
    prediction = poly(t)
    ss_res = np.sum((values - prediction) ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    rmse = float(np.sqrt(np.mean((values - prediction) ** 2)))
    return {
        "degree": degree,
        "coeffs": coeffs,
        "prediction": prediction,
        "r2": float(r2),
        "rmse": rmse,
    }


def _format_model(axis_label, fit):
    coeffs = fit["coeffs"]
    if fit["degree"] == 1:
        return f"{axis_label}(t) = {coeffs[0]:.5f}t + {coeffs[1]:.5f}"
    return f"{axis_label}(t) = {coeffs[0]:.5f}t² + {coeffs[1]:.5f}t + {coeffs[2]:.5f}"


def _format_model_latex(axis_label, fit):
    coeffs = fit["coeffs"]
    if fit["degree"] == 1:
        return rf"${axis_label}(t) = {coeffs[0]:.5f}t {coeffs[1]:+.5f}$"
    return rf"${axis_label}(t) = {coeffs[0]:.5f}t^2 {coeffs[1]:+.5f}t {coeffs[2]:+.5f}$"


def _format_model_plain_latex(axis_label, fit):
    coeffs = fit["coeffs"]
    if fit["degree"] == 1:
        return rf"{axis_label}(t) = {coeffs[0]:.5f}t {coeffs[1]:+.5f}"
    return rf"{axis_label}(t) = {coeffs[0]:.5f}t^2 {coeffs[1]:+.5f}t {coeffs[2]:+.5f}"


def _build_models_figure(df):
    t = df["tempo_s"].to_numpy(dtype=float)
    x = df["pos_x_um"].to_numpy(dtype=float)
    y = df["pos_y_um"].to_numpy(dtype=float)

    fits = {
        "x_linear": _fit_model(t, x, 1),
        "x_quadratic": _fit_model(t, x, 2),
        "y_linear": _fit_model(t, y, 1),
        "y_quadratic": _fit_model(t, y, 2),
    }

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes[0].scatter(t, x, s=10, alpha=0.45, label="Dados X(t)")
    axes[0].plot(t, fits["x_linear"]["prediction"], color="green", lw=2, label=f"Linear, R²={fits['x_linear']['r2']:.5f}")
    axes[0].plot(t, fits["x_quadratic"]["prediction"], color="black", lw=1.4, linestyle="--", label=f"Quadrático, R²={fits['x_quadratic']['r2']:.5f}")
    axes[0].set_title("Movimento horizontal")
    axes[0].set_xlabel("Tempo (s)")
    axes[0].set_ylabel("Posição X (u.m.)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)

    axes[1].scatter(t, y, s=10, alpha=0.45, label="Dados Y(t)")
    axes[1].plot(t, fits["y_linear"]["prediction"], color="gray", lw=1.4, linestyle="--", label=f"Linear, R²={fits['y_linear']['r2']:.5f}")
    axes[1].plot(t, fits["y_quadratic"]["prediction"], color="red", lw=2, label=f"Quadrático, R²={fits['y_quadratic']['r2']:.5f}")
    axes[1].set_title("Movimento vertical")
    axes[1].set_xlabel("Tempo (s)")
    axes[1].set_ylabel("Posição Y (u.m.)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    return fig, fits


def _build_single_model_figures(df, fits):
    t = df["tempo_s"].to_numpy(dtype=float)
    x = df["pos_x_um"].to_numpy(dtype=float)
    y = df["pos_y_um"].to_numpy(dtype=float)
    configs = [
        ("x_linear", "X(t) linear", "X", x, "#0f7b3d"),
        ("x_quadratic", "X(t) quadrático", "X", x, "#1f2937"),
        ("y_linear", "Y(t) linear", "Y", y, "#6b7280"),
        ("y_quadratic", "Y(t) quadrático", "Y", y, "#c1121f"),
    ]
    figures = {}
    for key, title, axis_label, values, color in configs:
        fig, ax = plt.subplots(figsize=(5.4, 3.35))
        ax.scatter(t, values, s=12, alpha=0.5, color="#2f6f9f", label="Dados rastreados")
        ax.plot(t, fits[key]["prediction"], color=color, lw=2.1, label="Modelo ajustado")
        ax.set_title(title)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel(f"Posição {axis_label} (u.m.)")
        ax.text(
            0.03,
            0.94,
            _format_model_latex(axis_label, fits[key]),
            transform=ax.transAxes,
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#d0d7de", "alpha": 0.9, "boxstyle": "round,pad=0.25"},
        )
        ax.text(
            0.03,
            0.08,
            rf"$R^2={fits[key]['r2']:.5f}$   RMSE={fits[key]['rmse']:.5f}",
            transform=ax.transAxes,
            fontsize=8.5,
            bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.9, "boxstyle": "round,pad=0.2"},
        )
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=7.5, loc="best")
        fig.tight_layout()
        figures[key] = fig
    return figures


def _build_acceleration_y_study(df):
    t = df["tempo_s"].to_numpy(dtype=float)
    ay = df["ay_um_s2"].to_numpy(dtype=float)
    valid = np.isfinite(t) & np.isfinite(ay)
    t = t[valid]
    ay = ay[valid]
    if ay.size == 0:
        ay = np.array([0.0])
        t = np.array([0.0])

    mean = float(np.mean(ay))
    median = float(np.median(ay))
    std = float(np.std(ay, ddof=1)) if ay.size > 1 else 0.0
    variance = float(std**2)
    minimum = float(np.min(ay))
    maximum = float(np.max(ay))

    fig, ax = plt.subplots(figsize=(10.8, 4.2))
    ax.plot(t, ay, marker="o", markersize=4, color="#b91c1c", lw=1.5, label="Aceleração vertical estimada")
    ax.axhline(mean, color="#0f766e", lw=2.0, label=f"Média = {mean:.4f}")
    ax.axhline(median, color="#7c3aed", lw=1.8, linestyle="--", label=f"Mediana = {median:.4f}")
    if std > 0:
        ax.fill_between(t, mean - std, mean + std, color="#0f766e", alpha=0.13, label="Média ± 1 desvio padrão")
    ax.set_title("Estudo estatístico da aceleração vertical")
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Aceleração em Y (u.m./s²)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig, {
        "mean": mean,
        "median": median,
        "std": std,
        "variance": variance,
        "min": minimum,
        "max": maximum,
        "n": int(ay.size),
    }


def _figures_grid(figures, styles):
    order = ["x_linear", "x_quadratic", "y_linear", "y_quadratic"]
    labels = ["X(t) linear", "X(t) quadrático", "Y(t) linear", "Y(t) quadrático"]
    cells = []
    for key, label in zip(order, labels):
        cells.append([_paragraph(f"<b>{label}</b>", styles, "SmallBR"), _image_cell(_fig_to_png_bytes(figures[key]), 7.1)])
    grid = Table(
        [
            [cells[0], cells[1]],
            [cells[2], cells[3]],
        ],
        colWidths=[7.6 * cm, 7.6 * cm],
    )
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E4E9F0")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBFCFE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return grid


def _savgol_cost_summary(savgol_metadata):
    cost = float(savgol_metadata.get("compute_cost") or 0)
    w_min = int(savgol_metadata.get("window_min") or savgol_metadata.get("window_size") or 5)
    w_max = int(savgol_metadata.get("window_max") or max(w_min, savgol_metadata.get("window_size") or w_min))
    d_min = int(savgol_metadata.get("poly_order_min") or 2)
    d_max = int(savgol_metadata.get("poly_order_max") or max(d_min, savgol_metadata.get("poly_order") or d_min))
    min_cost = float(w_min * (d_min + 1) ** 2)
    max_cost = float(w_max * (d_max + 1) ** 2)
    if max_cost <= min_cost:
        max_cost = max(min_cost, cost, 1.0)
    low_limit = min_cost + (max_cost - min_cost) / 3
    medium_limit = min_cost + 2 * (max_cost - min_cost) / 3
    if cost <= low_limit:
        label = "baixo"
    elif cost <= medium_limit:
        label = "médio"
    else:
        label = "alto"
    return {
        "cost": cost,
        "min_cost": min_cost,
        "low_limit": low_limit,
        "medium_limit": medium_limit,
        "max_cost": max_cost,
        "label": label,
    }


def _footer(font_name):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(1.5 * cm, 1.0 * cm, "Relatório de análise - ESTROBOSCOPIA DIGITAL")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Página {doc.page}")
        canvas.restoreState()

    return draw


def generate_student_report_pdf(
    context,
    calibration_image_bytes,
    stroboscopic_image_bytes,
    df,
    kinematic_figure,
    savgol_metadata,
    vector_image_bytes=None,
):
    styles, font_name = _styles()
    story = []
    models_figure, fits = _build_models_figure(df)
    model_figures = _build_single_model_figures(df, fits)
    acceleration_y_figure, acceleration_y_stats = _build_acceleration_y_study(df)
    gravity = 2 * fits["y_quadratic"]["coeffs"][0]
    cost_summary = _savgol_cost_summary(savgol_metadata)
    report_team = context.get("report_team") or []
    analysis_date = context.get("analysis_date") or "-"

    story.extend(
        [
            _paragraph("Relatório de Análise do Movimento", styles, "TitleBR"),
            _paragraph(
                f"Vídeo: <b>{context.get('video_name', 'vídeo analisado')}</b>. "
                "Produto gerado automaticamente a partir da imagem de calibração, rastreio, gráficos e modelos físicos.",
                styles,
            ),
            _table(
                [
                    ("Intervalo", f"Frames {context.get('start_frame')} a {context.get('end_frame')}"),
                    ("Fonte", context.get("video_source", "-")),
                    ("Escala", f"{context.get('scale_factor', 0):.6f} u.m./pixel"),
                    ("Densidade estroboscópica", context.get("stamp_density", "-")),
                    ("Savitzky-Golay", f"janela {savgol_metadata.get('window_size')}, ordem {savgol_metadata.get('poly_order')}"),
                ],
                styles,
            ),
            Spacer(1, 0.18 * cm),
            _table(
                [
                    ("Data da análise", analysis_date),
                    (
                        "Equipe",
                        "<br/>".join(
                            f"{member.get('name', '-')} - {member.get('grade', '-')}"
                            for member in report_team
                            if member.get("name") or member.get("grade")
                        )
                        or "Não informada",
                    ),
                ],
                styles,
            ),
            _paragraph(
                "Como ler estes quadros: eles documentam a equipe, a data e as condições do experimento. Isso transforma o relatório "
                "em um registro técnico da prática, permitindo comparar diferentes grupos, vídeos e escolhas de calibração.",
                styles,
                "SmallBR",
            ),
            Spacer(1, 0.25 * cm),
            _paragraph(
                f"Resultado físico de destaque: o ajuste vertical quadrático estima aceleração "
                f"<b>{gravity:.4f} u.m./s²</b>, com R² = <b>{fits['y_quadratic']['r2']:.6f}</b>.",
                styles,
                "MetricBR",
            ),
            PageBreak(),
            _paragraph("1. Como a análise é calculada", styles, "SectionBR"),
            _paragraph(
                "O relatório separa o método matemático das escolhas computacionais. O rastreador fornece posições em pixels; "
                "a calibração converte essas posições para unidade métrica; o tempo vem da taxa de quadros; e os modelos físicos "
                "interpretam a trajetória.",
                styles,
            ),
            _table(
                [
                    ("Centro do objeto", "Localiza o centro da caixa rastreada em cada frame."),
                    ("Tempo", "Converte o número do frame em segundos usando o FPS do vídeo."),
                    ("Escala espacial", "Converte distâncias em pixels para a unidade real escolhida."),
                    ("Conversão de coordenadas", "Transforma as posições rastreadas em coordenadas físicas X e Y."),
                    ("Movimento horizontal", "Modelo esperado quando a velocidade horizontal é aproximadamente constante."),
                    ("Movimento vertical", "Modelo esperado quando há aceleração vertical aproximadamente constante."),
                    ("Savitzky-Golay", "Ajuste polinomial local usado para suavizar posição e estimar derivadas."),
                ],
                styles,
                widths=(4.7, 10.5),
            ),
            Spacer(1, 0.18 * cm),
            _paragraph("Fórmulas principais do método:", styles, "SmallBR"),
            _formula_list(
                [
                    (1, "Centro do objeto", r"$p_x=x_{caixa}+\frac{w}{2},\qquad p_y=y_{caixa}+\frac{h}{2}$"),
                    (2, "Tempo do frame", r"$t=\frac{frame-frame_{inicial}}{FPS}$"),
                    (3, "Escala espacial", r"$S=\frac{d_{real}}{d_{px}}$"),
                    (4, "Coordenadas físicas", r"$X=(p_x-O_x)S,\qquad Y=-(p_y-O_y)S$"),
                    (5, "Modelo horizontal", r"$X(t)=v_x t+X_0$"),
                    (6, "Modelo vertical", r"$Y(t)=at^2+bt+c,\qquad a_y=2a$"),
                    (7, "Savitzky-Golay local", r"$\hat{s}(t)=\sum_{k=0}^{d} c_k t^k$"),
                ],
                styles,
            ),
            Spacer(1, 0.25 * cm),
            _paragraph(
                "Leitura física: em um lançamento oblíquo ideal, X(t) tende a ser linear e Y(t) tende a ser quadrático. "
                "Por isso, o valor de aceleração mais importante vem do coeficiente quadrático de Y(t). Valores de R² próximos "
                "de 1 indicam que o modelo representa bem os dados rastreados.",
                styles,
            ),
            PageBreak(),
            _paragraph("2. Calibração e imagem estroboscópica", styles, "SectionBR"),
            _paragraph("A calibração define origem, escala, objeto de rastreio e, quando ativada, o plano métrico retificado.", styles),
            _image_from_bytes(calibration_image_bytes, 15.5),
            _paragraph(
                "Na imagem de calibração, o aluno deve verificar se o objeto escolhido está bem delimitado e se os pontos de escala "
                "ou do plano foram marcados em posições coerentes. Pequenos erros nesta etapa aparecem depois como erro nas medidas "
                "de posição, velocidade e aceleração.",
                styles,
                "SmallBR",
            ),
            Spacer(1, 0.25 * cm),
            _image_from_bytes(stroboscopic_image_bytes, 15.5),
            _paragraph(
                "A imagem estroboscópica sintetiza o movimento em uma única figura: cada marcação corresponde a uma posição do objeto "
                "em tempos sucessivos. Espaçamentos maiores entre marcações indicam maior deslocamento naquele intervalo de tempo.",
                styles,
                "SmallBR",
            ),
            PageBreak(),
            _paragraph("3. Gráficos cinemáticos", styles, "SectionBR"),
            _paragraph("A série rastreada é convertida para posição, velocidade e aceleração nos eixos X e Y.", styles),
            _image_from_bytes(_fig_to_png_bytes(kinematic_figure), 15.5),
            _paragraph(
                "Nesta etapa, observe a forma das curvas: posição descreve a trajetória acumulada; velocidade mostra como a posição "
                "varia com o tempo; e aceleração indica a mudança da velocidade. Em lançamentos oblíquos, a aceleração vertical deve "
                "ser o principal indicador físico comparável à gravidade, respeitando a escala adotada.",
                styles,
                "SmallBR",
            ),
            PageBreak(),
            _paragraph("Estudo estatístico da aceleração vertical", styles, "SectionBR"),
            _paragraph(
                "O gráfico de aceleração vertical recebe destaque porque é nele que o estudante avalia a aproximação experimental da "
                "gravidade. A linha de média resume a tendência central; a mediana mostra o valor central ordenado; e a faixa de um "
                "desvio padrão indica a dispersão típica dos dados em torno da média.",
                styles,
            ),
            _image_from_bytes(_fig_to_png_bytes(acceleration_y_figure), 15.5),
            Spacer(1, 0.2 * cm),
            _table(
                [
                    ("Média", f"{acceleration_y_stats['mean']:.6f} u.m./s² - soma dos valores dividida pela quantidade de pontos."),
                    ("Mediana", f"{acceleration_y_stats['median']:.6f} u.m./s² - valor central, menos sensível a pontos extremos."),
                    ("Desvio padrão", f"{acceleration_y_stats['std']:.6f} u.m./s² - dispersão típica em torno da média."),
                    ("Variância", f"{acceleration_y_stats['variance']:.6f} (u.m./s²)² - quadrado do desvio padrão; aumenta quando há maior espalhamento."),
                    ("Amplitude observada", f"{acceleration_y_stats['min']:.6f} a {acceleration_y_stats['max']:.6f} u.m./s² em {acceleration_y_stats['n']} pontos."),
                ],
                styles,
                widths=(4.0, 11.2),
            ),
            _paragraph(
                "Interpretação: quanto menor o desvio padrão, mais estável foi a estimativa de aceleração ao longo do vídeo. "
                "Uma variância alta indica que o rastreio, a calibração, o FPS ou o ruído do movimento produziram oscilações maiores "
                "na aceleração calculada.",
                styles,
                "SmallBR",
            ),
            PageBreak(),
            _paragraph("4. Modelos ajustados", styles, "SectionBR"),
            _paragraph(
                "Foram comparados modelos linear e quadrático em cada eixo para interpretar o movimento. Cada imagem abaixo mostra "
                "os dados rastreados e a curva prevista por um dos quatro modelos listados na tabela.",
                styles,
            ),
            _figures_grid(model_figures, styles),
            Spacer(1, 0.25 * cm),
            _table(
                [
                    ("X(t) linear", f"{_format_model_plain_latex('X', fits['x_linear'])}; R²={fits['x_linear']['r2']:.6f}; RMSE={fits['x_linear']['rmse']:.6f}"),
                    ("X(t) quadrático", f"{_format_model_plain_latex('X', fits['x_quadratic'])}; R²={fits['x_quadratic']['r2']:.6f}; RMSE={fits['x_quadratic']['rmse']:.6f}"),
                    ("Y(t) linear", f"{_format_model_plain_latex('Y', fits['y_linear'])}; R²={fits['y_linear']['r2']:.6f}; RMSE={fits['y_linear']['rmse']:.6f}"),
                    ("Y(t) quadrático", f"{_format_model_plain_latex('Y', fits['y_quadratic'])}; R²={fits['y_quadratic']['r2']:.6f}; RMSE={fits['y_quadratic']['rmse']:.6f}"),
                ],
                styles,
                widths=(4.2, 11.0),
            ),
            Spacer(1, 0.2 * cm),
            _paragraph(
                f"Leitura: em X, o modelo linear descreve velocidade aproximadamente constante "
                f"({fits['x_linear']['coeffs'][0]:.4f} u.m./s). Em Y, o modelo quadrático é o mais significativo "
                f"para lançamento sob aceleração constante. Compare R² e RMSE: R² maior indica melhor explicação da variação dos dados, "
                f"enquanto RMSE menor indica menor erro médio entre a curva e os pontos rastreados.",
                styles,
            ),
            PageBreak(),
            _paragraph("5. Dados e parâmetros da análise", styles, "SectionBR"),
            _table(
                [
                    ("Pontos rastreados", len(df)),
                    ("Marcações estroboscópicas", int(df["is_stamp"].sum()) if "is_stamp" in df else "-"),
                    ("Aceleração vertical pelo ajuste", f"{gravity:.6f} u.m./s²"),
                    ("R² vertical quadrático", f"{fits['y_quadratic']['r2']:.9f}"),
                    ("Mensagem Savitzky-Golay", savgol_metadata.get("message", "-")),
                    ("Custo relativo do filtro", f"{savgol_metadata.get('compute_cost', 0):.0f}"),
                ],
                styles,
            ),
            _paragraph(
                "O custo relativo do filtro Savitzky-Golay estima o esforço computacional para suavizar a trajetória neste vídeo. "
                "Ele cresce principalmente com a janela <i>w</i> e com a ordem polinomial <i>d</i>, segundo a aproximação "
                "<b>C = w(d+1)²</b>. Esse valor não mede diretamente o erro físico; ele compara o custo entre candidatos possíveis "
                "para o mesmo vídeo. O algoritmo escolhe o menor custo que mantém o erro dentro da tolerância aceita.",
                styles,
            ),
            _table(
                [
                    ("Baixo", f"{cost_summary['min_cost']:.0f} ≤ C ≤ {cost_summary['low_limit']:.0f}"),
                    ("Médio", f"{cost_summary['low_limit']:.0f} < C ≤ {cost_summary['medium_limit']:.0f}"),
                    ("Alto", f"{cost_summary['medium_limit']:.0f} < C ≤ {cost_summary['max_cost']:.0f}"),
                    ("Classificação deste vídeo", f"C = {cost_summary['cost']:.0f}, custo {cost_summary['label']}"),
                ],
                styles,
                widths=(4.7, 10.5),
            ),
            _paragraph(
                "Use esta escala para interpretar a escolha automática: custo baixo indica uma solução mais simples e rápida; custo médio "
                "indica uma suavização mais exigente; custo alto indica que o vídeo exigiu janelas maiores ou polinômios mais complexos "
                "para manter estabilidade numérica.",
                styles,
                "SmallBR",
            ),
        ]
    )

    if vector_image_bytes:
        story.extend(
            [
                Spacer(1, 0.35 * cm),
                _paragraph("Vetores de velocidade", styles, "SectionBR"),
                _image_from_bytes(vector_image_bytes, 15.5),
            ]
        )

    plt.close(models_figure)
    plt.close(acceleration_y_figure)
    for fig in model_figures.values():
        plt.close(fig)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.5 * cm,
    )
    footer = _footer(font_name)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer.getvalue()
