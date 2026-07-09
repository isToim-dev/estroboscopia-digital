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


def _fig_to_png_bytes(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


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


def _footer(font_name):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(1.5 * cm, 1.0 * cm, "Relatório de análise - estroboscopia digital")
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
    gravity = 2 * fits["y_quadratic"]["coeffs"][0]

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
                    ("Centro do objeto", "p_x = x_caixa + largura/2; p_y = y_caixa + altura/2"),
                    ("Tempo", "t = (frame - frame inicial) / FPS"),
                    ("Escala espacial", "S = distância real / distância em pixels"),
                    ("Conversão de coordenadas", "X = (p_x - origem_x) S; Y = -(p_y - origem_y) S"),
                    ("Movimento horizontal", "X(t) = v_x t + X_0, quando a velocidade horizontal é aproximadamente constante"),
                    ("Movimento vertical", "Y(t) = a t² + b t + c; a_y = 2a"),
                    ("Savitzky-Golay", "A trajetória local é aproximada por um polinômio; suas derivadas estimam velocidade e aceleração."),
                ],
                styles,
                widths=(4.7, 10.5),
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
            Spacer(1, 0.25 * cm),
            _image_from_bytes(stroboscopic_image_bytes, 15.5),
            PageBreak(),
            _paragraph("3. Gráficos cinemáticos", styles, "SectionBR"),
            _paragraph("A série rastreada é convertida para posição, velocidade e aceleração nos eixos X e Y.", styles),
            _image_from_bytes(_fig_to_png_bytes(kinematic_figure), 15.5),
            PageBreak(),
            _paragraph("4. Modelos ajustados", styles, "SectionBR"),
            _paragraph("Foram comparados modelos linear e quadrático em cada eixo para interpretar o movimento.", styles),
            _image_from_bytes(_fig_to_png_bytes(models_figure), 15.5),
            Spacer(1, 0.25 * cm),
            _table(
                [
                    ("X(t) linear", f"{_format_model('X', fits['x_linear'])}; R²={fits['x_linear']['r2']:.6f}; RMSE={fits['x_linear']['rmse']:.6f}"),
                    ("X(t) quadrático", f"{_format_model('X', fits['x_quadratic'])}; R²={fits['x_quadratic']['r2']:.6f}; RMSE={fits['x_quadratic']['rmse']:.6f}"),
                    ("Y(t) linear", f"{_format_model('Y', fits['y_linear'])}; R²={fits['y_linear']['r2']:.6f}; RMSE={fits['y_linear']['rmse']:.6f}"),
                    ("Y(t) quadrático", f"{_format_model('Y', fits['y_quadratic'])}; R²={fits['y_quadratic']['r2']:.6f}; RMSE={fits['y_quadratic']['rmse']:.6f}"),
                ],
                styles,
                widths=(4.2, 11.0),
            ),
            Spacer(1, 0.2 * cm),
            _paragraph(
                f"Leitura: em X, o modelo linear descreve velocidade aproximadamente constante "
                f"({fits['x_linear']['coeffs'][0]:.4f} u.m./s). Em Y, o modelo quadrático é o mais significativo "
                f"para lançamento sob aceleração constante.",
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
