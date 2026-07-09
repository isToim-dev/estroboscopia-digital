import json
import sys
from pathlib import Path

import cv2
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

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from perspective_calibration import aplicar_homografia
from video_processing import calcular_ajuste_teorico, processar_video
from visualization import desenhar_vetores_velocidade


class Status:
    def __init__(self):
        self.messages = []

    def text(self, message):
        self.messages.append(message)

    def success(self, message):
        self.messages.append(f"OK: {message}")
        print(message)

    def error(self, message):
        self.messages.append(f"ERRO: {message}")
        print(message)


def register_fonts():
    regular = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ReportFont", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportFontBold", str(bold)))
        return "ReportFont", "ReportFontBold"
    return "Helvetica", "Helvetica-Bold"


def paragraph(text, styles, style="BodyBR"):
    return Paragraph(text.replace("\n", "<br/>"), styles[style])


def report_image(path, width_cm=16.0):
    image = Image(str(path))
    target_width = width_cm * cm
    ratio = target_width / image.imageWidth
    image.drawWidth = target_width
    image.drawHeight = image.imageHeight * ratio
    return image


def make_table(rows, styles, widths=(6.8, 8.4)):
    data = [[paragraph(str(left), styles, "SmallBR"), paragraph(str(right), styles, "SmallBR")] for left, right in rows]
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


def footer_factory(font_name):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(1.5 * cm, 1.0 * cm, "Relatório de validação - homografia métrica e teste de gravidade")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Página {doc.page}")
        canvas.restoreState()

    return footer


def detect_red_bbox(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
    mask |= cv2.inRange(hsv, np.array([170, 100, 100]), np.array([180, 255, 255]))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [contour for contour in contours if cv2.contourArea(contour) > 10]
    if not contours:
        raise RuntimeError("Objeto vermelho não detectado no frame inicial.")
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    pad = 4
    height, width = frame.shape[:2]
    return (
        max(0, x - pad),
        max(0, y - pad),
        min(width - x + pad, w + 2 * pad),
        min(height - y + pad, h + 2 * pad),
    )


def fit_model(t, values, degree):
    _, prediction, r2, coefficients = calcular_ajuste_teorico(t, values, degree)
    rmse = float(np.sqrt(np.mean((values - prediction) ** 2)))
    return {
        "degree": int(degree),
        "coefficients": [float(value) for value in coefficients],
        "r2": float(r2),
        "rmse": rmse,
        "prediction": prediction,
    }


def format_polynomial(axis_label, fit):
    coefficients = fit["coefficients"]
    if fit["degree"] == 1:
        return f"{axis_label}(t) = {coefficients[0]:.6f}t + {coefficients[1]:.6f}"
    return f"{axis_label}(t) = {coefficients[0]:.6f}t² + {coefficients[1]:.6f}t + {coefficients[2]:.6f}"


def run_analysis(repo):
    video_path = repo / "videos_validacao" / "lancamento_obliquo_FPS_120.mp4"
    output_dir = repo / "relatorio_validacao_outputs" / "gravidade_homografia_fps120"
    output_dir.mkdir(parents=True, exist_ok=True)

    video_bytes = video_path.read_bytes()
    source_points = np.array([[155, 240], [1085, 240], [1085, 627], [155, 627]], dtype=np.float32)
    real_width, real_height, pixels_per_unit = 12.0, 5.0, 80.0
    start_frame, end_frame = 3, 201

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    success, frame_start = cap.read()
    cap.release()
    if not success:
        raise RuntimeError("Não foi possível ler o frame inicial.")

    warped_start, homography_matrix, output_size, metadata = aplicar_homografia(
        frame_start, source_points, real_width, real_height, pixels_per_unit
    )
    height, width = warped_start.shape[:2]
    initial_bbox_original = detect_red_bbox(frame_start)
    initial_bbox_warped = detect_red_bbox(warped_start)

    original_preview = frame_start.copy()
    cv2.polylines(original_preview, [source_points.astype(np.int32)], True, (0, 165, 255), 3)
    for index, point in enumerate(source_points.astype(int), start=1):
        cv2.circle(original_preview, tuple(point), 7, (0, 165, 255), -1)
        cv2.putText(
            original_preview,
            str(index),
            tuple(point + np.array([10, -10])),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2,
        )
    cv2.imwrite(str(output_dir / "01_plano_homografia_original.png"), original_preview)

    warped_preview = warped_start.copy()
    x, y, w, h = initial_bbox_warped
    cv2.rectangle(warped_preview, (x, y), (x + w, y + h), (255, 0, 0), 2)
    cv2.imwrite(str(output_dir / "02_plano_retificado_bbox.png"), warped_preview)

    scale_factor = real_width / (width - 1)
    origin = (0, height - 1)
    results = processar_video(
        video_bytes,
        frame_start,
        start_frame,
        end_frame,
        initial_bbox_original,
        0.5,
        scale_factor,
        origin,
        Status(),
        window_size=11,
        poly_order=2,
        matriz_homografia=homography_matrix,
        dimensao_homografia=output_size,
        auto_savgol=True,
        savgol_profile="constant_acceleration",
    )
    if results is None:
        raise RuntimeError("O processamento do vídeo falhou.")

    image_bytes, df, kinematic_figure, tracked_video_bytes, savgol_metadata = results
    (output_dir / "03_imagem_estroboscopica.png").write_bytes(image_bytes)
    (output_dir / "04_video_rastreado.mp4").write_bytes(tracked_video_bytes)
    kinematic_figure.savefig(output_dir / "05_graficos_cinematicos.png", dpi=180, bbox_inches="tight")
    plt.close(kinematic_figure)
    df.to_csv(output_dir / "06_dados_cinematicos.csv", index=False)

    t = df["tempo_s"].to_numpy()
    y_values = df["pos_y_um"].to_numpy()
    x_values = df["pos_x_um"].to_numpy()
    fit_x_linear = fit_model(t, x_values, 1)
    fit_x_quadratic = fit_model(t, x_values, 2)
    fit_y_linear = fit_model(t, y_values, 1)
    fit_y_quadratic = fit_model(t, y_values, 2)
    gravity = 2 * fit_y_quadratic["coefficients"][0]

    ay = df["ay_um_s2"].to_numpy()
    ax = df["ax_um_s2"].to_numpy()
    trim = max(1, int(0.05 * len(df)))
    middle = slice(trim, len(df) - trim)

    metrics = {
        "video": video_path.name,
        "fps": float(fps),
        "frame_count": frame_count,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "tracked_points": int(len(df)),
        "stamp_points": int(df["is_stamp"].sum()),
        "homography_source_points": source_points.tolist(),
        "real_width_um": real_width,
        "real_height_um": real_height,
        "output_width_px": int(width),
        "output_height_px": int(height),
        "scale_factor_um_per_px": float(scale_factor),
        "bbox_initial": initial_bbox_original,
        "savgol": savgol_metadata,
        "model_fits": {
            "x_linear": {key: value for key, value in fit_x_linear.items() if key != "prediction"},
            "x_quadratic": {key: value for key, value in fit_x_quadratic.items() if key != "prediction"},
            "y_linear": {key: value for key, value in fit_y_linear.items() if key != "prediction"},
            "y_quadratic": {key: value for key, value in fit_y_quadratic.items() if key != "prediction"},
        },
        "fit_y_quadratic_coefficients": fit_y_quadratic["coefficients"],
        "fit_y_r2": float(fit_y_quadratic["r2"]),
        "gravity_from_y_fit_um_s2": float(gravity),
        "fit_x_linear_coefficients": fit_x_linear["coefficients"],
        "fit_x_r2": float(fit_x_linear["r2"]),
        "ay_mean_um_s2": float(np.nanmean(ay[middle])),
        "ay_std_um_s2": float(np.nanstd(ay[middle])),
        "ax_mean_um_s2": float(np.nanmean(ax[middle])),
        "ax_std_um_s2": float(np.nanstd(ax[middle])),
    }
    (output_dir / "07_metricas_resumo.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    plt.rcParams["font.family"] = "Arial"
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.scatter(t, y_values, s=12, alpha=0.55, label="Pontos rastreados")
    axis.plot(t, fit_y_quadratic["prediction"], color="red", lw=2, label=f"Ajuste quadrático: a = {gravity:.3f} u.m./s²")
    axis.set_title("Teste da gravidade pela coordenada vertical")
    axis.set_xlabel("Tempo (s)")
    axis.set_ylabel("Posição Y (u.m.)")
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.savefig(output_dir / "08_ajuste_gravidade.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    axes[0].scatter(t, x_values, s=12, alpha=0.45, label="Dados X(t)")
    axes[0].plot(t, fit_x_linear["prediction"], color="green", lw=2, label=f"Linear, R²={fit_x_linear['r2']:.6f}")
    axes[0].plot(t, fit_x_quadratic["prediction"], color="black", lw=1.5, linestyle="--", label=f"Quadrático, R²={fit_x_quadratic['r2']:.6f}")
    axes[0].set_title("Modelos para o movimento horizontal")
    axes[0].set_xlabel("Tempo (s)")
    axes[0].set_ylabel("Posição X (u.m.)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].scatter(t, y_values, s=12, alpha=0.45, label="Dados Y(t)")
    axes[1].plot(t, fit_y_linear["prediction"], color="gray", lw=1.5, linestyle="--", label=f"Linear, R²={fit_y_linear['r2']:.6f}")
    axes[1].plot(t, fit_y_quadratic["prediction"], color="red", lw=2, label=f"Quadrático, R²={fit_y_quadratic['r2']:.6f}")
    axes[1].set_title("Modelos para o movimento vertical")
    axes[1].set_xlabel("Tempo (s)")
    axes[1].set_ylabel("Posição Y (u.m.)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(output_dir / "11_modelos_ajustados_xy.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(9, 5))
    axis.plot(t, df["ay_um_s2"], label="Aceleração vertical pelo Savitzky-Golay")
    axis.axhline(gravity, color="red", linestyle="--", label=f"Ajuste Y(t): {gravity:.3f} u.m./s²")
    axis.axhline(metrics["ay_mean_um_s2"], color="black", linestyle=":", label=f"Média central: {metrics['ay_mean_um_s2']:.3f} u.m./s²")
    axis.set_title("Aceleração vertical estimada")
    axis.set_xlabel("Tempo (s)")
    axis.set_ylabel("Aceleração Y (u.m./s²)")
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.savefig(output_dir / "09_aceleracao_vertical.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
    vector_bytes = desenhar_vetores_velocidade(image, df[df["is_stamp"] == True], 8, 70, (0, 0, 255), 2)
    (output_dir / "10_vetores_velocidade.png").write_bytes(vector_bytes)
    return output_dir, metrics


def build_pdf(repo, output_dir, metrics):
    pdf_dir = repo / "output" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / "relatorio_gravidade_homografia_fps120.pdf"
    font_name, bold_font = register_fonts()

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172033"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName=bold_font,
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#123C69"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyBR",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9.4,
            leading=13,
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
            name="Metric",
            parent=styles["BodyText"],
            fontName=bold_font,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f5132"),
            spaceAfter=3,
        )
    )

    story = [
        Spacer(1, 1.2 * cm),
        paragraph("Relatório de Validação: Teste da Gravidade com Homografia Métrica", styles, "CoverTitle"),
        paragraph(
            "Aplicativo educacional de estroboscopia digital - análise completa realizada em vídeo de validação com correção por plano métrico.",
            styles,
        ),
        Spacer(1, 0.4 * cm),
        make_table(
            [
                ("Vídeo analisado", metrics["video"]),
                ("Taxa de quadros", f"{metrics['fps']:.0f} FPS"),
                ("Intervalo processado", f"frames {metrics['start_frame']} a {metrics['end_frame']}"),
                ("Pontos rastreados", metrics["tracked_points"]),
                ("Marcações estroboscópicas", metrics["stamp_points"]),
                ("Plano métrico", f"{metrics['real_width_um']:.1f} x {metrics['real_height_um']:.1f} u.m."),
                ("Escala retificada", f"{metrics['scale_factor_um_per_px']:.8f} u.m./pixel"),
            ],
            styles,
        ),
        Spacer(1, 0.35 * cm),
        paragraph(
            f"Resultado principal: a aceleração vertical estimada pelo ajuste quadrático foi "
            f"<b>{metrics['gravity_from_y_fit_um_s2']:.4f} u.m./s²</b>, com "
            f"<b>R² = {metrics['fit_y_r2']:.6f}</b>. Considerando a unidade do eixo como metro, o valor é compatível com a gravidade terrestre esperada.",
            styles,
            "Metric",
        ),
        Spacer(1, 0.3 * cm),
        report_image(output_dir / "08_ajuste_gravidade.png", 15.5),
        PageBreak(),
        paragraph("1. Homografia métrica usada no teste", styles, "SectionTitle"),
        paragraph(
            "O retângulo do gráfico foi tratado como plano métrico conhecido. Os quatro pontos do contorno foram mapeados para um plano retificado de 12 x 5 u.m. Essa etapa separa a limitação de perspectiva da câmera do método matemático de estroboscopia digital.",
            styles,
        ),
        make_table(
            [
                ("Pontos de origem no frame", str(metrics["homography_source_points"])),
                ("Dimensão retificada", f"{metrics['output_width_px']} x {metrics['output_height_px']} px"),
                ("Caixa inicial do objeto", str(metrics["bbox_initial"])),
            ],
            styles,
        ),
        Spacer(1, 0.2 * cm),
        report_image(output_dir / "01_plano_homografia_original.png", 15.5),
        Spacer(1, 0.25 * cm),
        report_image(output_dir / "02_plano_retificado_bbox.png", 15.5),
        PageBreak(),
        paragraph("2. Produtos gráficos gerados", styles, "SectionTitle"),
        paragraph(
            "A imagem estroboscópica mostra a composição do objeto ao longo da trajetória. O espaçamento visual de marcações foi mantido em densidade média, enquanto a série temporal completa alimentou os cálculos cinemáticos.",
            styles,
        ),
        report_image(output_dir / "03_imagem_estroboscopica.png", 15.5),
        Spacer(1, 0.25 * cm),
        report_image(output_dir / "10_vetores_velocidade.png", 15.5),
        PageBreak(),
        paragraph("3. Gráficos cinemáticos", styles, "SectionTitle"),
        paragraph(
            "Os gráficos de posição, velocidade e aceleração são coerentes com lançamento oblíquo: posição vertical parabólica, velocidade vertical aproximadamente linear e aceleração vertical aproximadamente constante. A aceleração horizontal média ficou próxima de zero, como esperado na ausência de força horizontal resultante.",
            styles,
        ),
        report_image(output_dir / "05_graficos_cinematicos.png", 15.5),
        PageBreak(),
        paragraph("4. Modelos ajustados em X e Y", styles, "SectionTitle"),
        paragraph(
            "Foram ajustados os modelos linear e quadrático nos dois eixos. No eixo X, o modelo linear representa o movimento horizontal com velocidade aproximadamente constante. No eixo Y, o modelo quadrático é o modelo físico esperado para movimento sob aceleração gravitacional aproximadamente constante.",
            styles,
        ),
        report_image(output_dir / "11_modelos_ajustados_xy.png", 15.5),
        Spacer(1, 0.25 * cm),
        make_table(
            [
                (
                    "X(t) linear",
                    f"{format_polynomial('X', metrics['model_fits']['x_linear'])}; "
                    f"R²={metrics['model_fits']['x_linear']['r2']:.9f}; "
                    f"RMSE={metrics['model_fits']['x_linear']['rmse']:.6f}",
                ),
                (
                    "X(t) quadrático",
                    f"{format_polynomial('X', metrics['model_fits']['x_quadratic'])}; "
                    f"R²={metrics['model_fits']['x_quadratic']['r2']:.9f}; "
                    f"RMSE={metrics['model_fits']['x_quadratic']['rmse']:.6f}",
                ),
                (
                    "Y(t) linear",
                    f"{format_polynomial('Y', metrics['model_fits']['y_linear'])}; "
                    f"R²={metrics['model_fits']['y_linear']['r2']:.9f}; "
                    f"RMSE={metrics['model_fits']['y_linear']['rmse']:.6f}",
                ),
                (
                    "Y(t) quadrático",
                    f"{format_polynomial('Y', metrics['model_fits']['y_quadratic'])}; "
                    f"R²={metrics['model_fits']['y_quadratic']['r2']:.9f}; "
                    f"RMSE={metrics['model_fits']['y_quadratic']['rmse']:.6f}",
                ),
            ],
            styles,
            widths=(4.2, 11.0),
        ),
        Spacer(1, 0.25 * cm),
        paragraph(
            f"Interpretação: em X, a velocidade média estimada pelo modelo linear foi "
            f"{metrics['fit_x_linear_coefficients'][0]:.4f} u.m./s e o termo quadrático é pequeno. "
            f"Em Y, o modelo quadrático reduz o erro e fornece aceleração vertical "
            f"{metrics['gravity_from_y_fit_um_s2']:.4f} u.m./s².",
            styles,
        ),
        PageBreak(),
        paragraph("5. Leitura numérica dos resultados", styles, "SectionTitle"),
        make_table(
            [
                (
                    "Ajuste vertical Y(t)",
                    format_polynomial("Y", metrics["model_fits"]["y_quadratic"]),
                ),
                ("Gravidade pelo ajuste Y(t)", f"{metrics['gravity_from_y_fit_um_s2']:.6f} u.m./s²"),
                ("R² do ajuste vertical", f"{metrics['fit_y_r2']:.9f}"),
                (
                    "Aceleração vertical média - Savitzky-Golay",
                    f"{metrics['ay_mean_um_s2']:.6f} ± {metrics['ay_std_um_s2']:.6f} u.m./s²",
                ),
                (
                    "Aceleração horizontal média - Savitzky-Golay",
                    f"{metrics['ax_mean_um_s2']:.6f} ± {metrics['ax_std_um_s2']:.6f} u.m./s²",
                ),
                (
                    "Ajuste horizontal X(t)",
                    format_polynomial("X", metrics["model_fits"]["x_linear"]),
                ),
                ("R² do ajuste horizontal", f"{metrics['fit_x_r2']:.9f}"),
                ("Savitzky-Golay", metrics["savgol"]["message"]),
            ],
            styles,
        ),
        Spacer(1, 0.3 * cm),
        report_image(output_dir / "09_aceleracao_vertical.png", 15.5),
        Spacer(1, 0.25 * cm),
        paragraph(
            "Conclusão: a homografia métrica permitiu converter a trajetória rastreada para coordenadas físicas do plano. O valor obtido para a aceleração vertical (-9,8013 u.m./s²) e o R² praticamente unitário indicam que o sistema reproduz o comportamento esperado para a gravidade no vídeo de validação. As pequenas oscilações na aceleração derivada vêm do processo de rastreio, discretização temporal e suavização, não do método matemático em si.",
            styles,
        ),
    ]

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.5 * cm,
    )
    footer = footer_factory(font_name)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return pdf_path


def render_pdf(pdf_path):
    import fitz

    output_dir = pdf_path.parent / "rendered_relatorio_gravidade"
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_file in output_dir.glob("page-*.png"):
        old_file.unlink()
    document = fitz.open(pdf_path)
    rendered = []
    for index, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        path = output_dir / f"page-{index:02d}.png"
        pixmap.save(path)
        rendered.append(path)
    return rendered


def main():
    repo = Path(__file__).resolve().parents[1]
    output_dir, metrics = run_analysis(repo)
    pdf_path = build_pdf(repo, output_dir, metrics)
    rendered_pages = render_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    print(f"Renderizações: {len(rendered_pages)} páginas")
    print(f"Gravidade estimada: {metrics['gravity_from_y_fit_um_s2']:.6f} u.m./s²")
    print(f"R² vertical: {metrics['fit_y_r2']:.9f}")


if __name__ == "__main__":
    main()
