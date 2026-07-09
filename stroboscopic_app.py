import os
import tempfile
from io import BytesIO

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

from app_config import DEFAULT_APP_CSS
from app_state import load_selected_video, reset_video_state
from perspective_calibration import aplicar_homografia, estimate_pixels_per_unit
from sample_videos import list_validation_videos, make_video_thumbnail
from savgol_reverse import estimate_savgol_bounds
from ui_controls import render_stamp_density_selector
from video_processing import calcular_ajuste_teorico, processar_video
from visualization import desenhar_grade_cartesiana, desenhar_vetores_velocidade


st.set_page_config(layout="wide", page_title="Análise de Movimento por Vídeo")
st.markdown(DEFAULT_APP_CSS, unsafe_allow_html=True)


def rerun():
    st.rerun()


def read_video_frame(video_bytes, frame_idx):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_file.write(video_bytes)
    temp_file.close()
    try:
        cap = cv2.VideoCapture(temp_file.name)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_idx = int(max(0, min(frame_idx, max(total_frames - 1, 0))))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        cap.release()
        return success, frame, total_frames
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def detect_validation_object_bbox(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
    mask |= cv2.inRange(hsv, np.array([170, 100, 100]), np.array([180, 255, 255]))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [contour for contour in contours if cv2.contourArea(contour) > 10]
    if not contours:
        return None

    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    pad = 10
    min_size = 42
    height, width = frame.shape[:2]
    center_x = x + w / 2
    center_y = y + h / 2
    box_size = int(round(max(w + 2 * pad, h + 2 * pad, min_size)))
    x0 = int(round(max(0, min(width - box_size, center_x - box_size / 2))))
    y0 = int(round(max(0, min(height - box_size, center_y - box_size / 2))))
    return x0, y0, box_size, box_size


def init_configuration_defaults(frame):
    height, width = frame.shape[:2]
    suggested_bbox = None
    if st.session_state.get("video_source") == "amostra de validação":
        suggested_bbox = detect_validation_object_bbox(frame)

    if suggested_bbox:
        obj_x, obj_y_cv, obj_w, obj_h = suggested_bbox
        obj_y = int(height - obj_y_cv - obj_h)
    else:
        obj_x = int(width * 0.45)
        obj_y = int(height * 0.45)
        obj_w = max(20, int(width * 0.08))
        obj_h = max(20, int(height * 0.08))

    defaults = {
        "orig_x": 0,
        "orig_y": 0,
        "x1": int(width * 0.1),
        "y1": 0,
        "x2": int(width * 0.4),
        "y2": 0,
        "obj_x": int(obj_x),
        "obj_y": int(obj_y),
        "obj_w": int(obj_w),
        "obj_h": int(obj_h),
        "hx1": int(width * 0.2),
        "hy1": int(height * 0.2),
        "hx2": int(width * 0.8),
        "hy2": int(height * 0.2),
        "hx3": int(width * 0.8),
        "hy3": int(height * 0.8),
        "hx4": int(width * 0.2),
        "hy4": int(height * 0.8),
        "dist_real": 1.0,
        "homography_real_width": 1.0,
        "homography_real_height": 1.0,
        "homography_pixels_per_unit": 80,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def preview_savgol_pair(n_points, profile):
    if n_points < 5:
        return 5, 2

    def odd(value):
        value = int(round(value))
        if value % 2 == 0:
            value += 1
        return max(5, min(value, n_points if n_points % 2 else n_points - 1))

    if profile == "constant_acceleration":
        window = odd(max(11, min(51, n_points * 0.14)))
        order = 3 if window >= 7 else 2
    elif profile == "fast_event":
        window = odd(7 if n_points >= 21 else 5)
        order = min(4, window - 1)
    else:
        window = odd(max(7, min(21, n_points * 0.06)))
        order = 2

    return window, order


def render_contact_footer():
    st.markdown(
        """
        <footer class="institutional-footer">
            <p class="institutional-footer__line">
                Orientando: Prof. Antônio M. S. Leite
            </p>
            <p class="institutional-footer__line">
                Orientador: Prof. Dr. Rafael Alves Figueiredo
            </p>
            <p class="institutional-footer__line">
                PROFMAT | Universidade Federal de Uberlândia (UFU)
            </p>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def render_upload_step():
    st.markdown("# Análise de Movimento por Vídeo")
    st.markdown("### Envie seu vídeo ou use a galeria para testar.")

    upload_col, samples_col = st.columns([0.95, 2.05])
    with upload_col:
        st.markdown("## 1. Meu vídeo")
        video_file = st.file_uploader(
            "Arraste ou selecione um arquivo",
            type=["mp4", "avi", "mov", "mkv", "webm", "m4v"],
            help="Depois do envio, você escolhe o frame inicial e final antes da calibração.",
        )
        st.caption("Escolha o vídeo, marque o intervalo e calibre a cena.")
        if video_file:
            load_selected_video(video_file.getvalue(), video_file.name, "upload")
            rerun()

    with samples_col:
        st.markdown("## 2. Galeria de vídeos")
        st.caption("Amostras prontas para testar.")
        validation_videos = list_validation_videos()
        if not validation_videos:
            st.warning("Nenhum vídeo de validação foi encontrado em `videos_validacao`.")
            return

        columns = st.columns(min(3, len(validation_videos)))
        for index, sample in enumerate(validation_videos):
            with columns[index % len(columns)]:
                st.image(make_video_thumbnail(str(sample["path"])), use_container_width=True)
                fps = sample["fps_detected"] or 0
                duration = sample["frame_count"] / fps if fps else 0
                st.markdown(f"**{sample['fps_label']} FPS**")
                st.caption(f"{sample['frame_count']} frames | {duration:.2f}s | {sample['width']}x{sample['height']}")
                if st.button("Usar este vídeo", key=f"use_sample_{sample['path'].name}", use_container_width=True):
                    load_selected_video(
                        sample["path"].read_bytes(),
                        sample["path"].name,
                        "amostra de validação",
                        fps=sample["fps_detected"],
                        frame_count=sample["frame_count"],
                    )
                    rerun()


def render_frame_selection():
    st.markdown("## Passo 2: seleção do intervalo")
    st.caption(
        f"Vídeo atual: {st.session_state.get('video_name', 'vídeo selecionado')} "
        f"({st.session_state.get('video_source', 'upload')})."
    )

    success, frame, total_frames = read_video_frame(st.session_state.video_bytes, st.session_state.get("preview_idx", 0))
    if total_frames <= 0:
        st.error("Não foi possível ler os frames do vídeo selecionado.")
        return

    st.session_state.setdefault("preview_idx", 0)
    st.session_state.setdefault("start_idx", 0)
    st.session_state.setdefault("end_idx", total_frames - 1)

    new_preview = st.slider("Linha do tempo do vídeo", 0, total_frames - 1, st.session_state.preview_idx)
    if new_preview != st.session_state.preview_idx:
        st.session_state.preview_idx = new_preview
        rerun()

    nav_cols = st.columns(4)
    if nav_cols[0].button("<< -5 frames", use_container_width=True):
        st.session_state.preview_idx = max(0, st.session_state.preview_idx - 5)
        rerun()
    if nav_cols[1].button("< anterior", use_container_width=True):
        st.session_state.preview_idx = max(0, st.session_state.preview_idx - 1)
        rerun()
    if nav_cols[2].button("próximo >", use_container_width=True):
        st.session_state.preview_idx = min(total_frames - 1, st.session_state.preview_idx + 1)
        rerun()
    if nav_cols[3].button("+5 frames >>", use_container_width=True):
        st.session_state.preview_idx = min(total_frames - 1, st.session_state.preview_idx + 5)
        rerun()

    success, frame, _ = read_video_frame(st.session_state.video_bytes, st.session_state.preview_idx)
    if success:
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption=f"Frame {st.session_state.preview_idx} / {total_frames - 1}")

    start_col, end_col = st.columns(2)
    with start_col:
        st.markdown(f"**Frame inicial:** `{st.session_state.start_idx}`")
        if st.button("Marcar preview como inicial", use_container_width=True):
            st.session_state.start_idx = st.session_state.preview_idx
            st.session_state.end_idx = max(st.session_state.end_idx, st.session_state.start_idx)
            rerun()
    with end_col:
        st.markdown(f"**Frame final:** `{st.session_state.end_idx}`")
        if st.button("Marcar preview como final", use_container_width=True):
            st.session_state.end_idx = st.session_state.preview_idx
            st.session_state.start_idx = min(st.session_state.start_idx, st.session_state.end_idx)
            rerun()

    if st.button("Confirmar intervalo e iniciar configuração", type="primary", use_container_width=True):
        success, frame, _ = read_video_frame(st.session_state.video_bytes, st.session_state.start_idx)
        if not success:
            st.error("Erro na leitura do frame inicial.")
            return
        st.session_state.raw_initial_frame = frame
        st.session_state.frame_trabalho = frame
        st.session_state.start_frame_for_analysis = st.session_state.start_idx
        st.session_state.end_frame_for_analysis = st.session_state.end_idx
        st.session_state.step = "configuration"
        rerun()


def draw_configuration_overlay(frame, calibration_mode, ferramenta_ativa):
    frame_com_grade = desenhar_grade_cartesiana(frame)
    height, width = frame_com_grade.shape[:2]
    preview = frame_com_grade.copy()

    if calibration_mode == "Plano (homografia métrica)":
        pts = [
            (int(st.session_state.hx1), int(st.session_state.hy1)),
            (int(st.session_state.hx2), int(st.session_state.hy2)),
            (int(st.session_state.hx3), int(st.session_state.hy3)),
            (int(st.session_state.hx4), int(st.session_state.hy4)),
        ]
        cv2.polylines(preview, [np.array(pts, dtype=np.int32)], isClosed=True, color=(0, 165, 255), thickness=2)
        for idx, point in enumerate(pts, start=1):
            cv2.circle(preview, point, 6, (0, 165, 255), -1)
            cv2.putText(preview, str(idx), (point[0] + 10, point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

    if calibration_mode == "Dois pontos" and "Perspectiva" not in ferramenta_ativa:
        oy_cv = int(height - st.session_state.orig_y)
        y1_cv = int(height - st.session_state.y1)
        y2_cv = int(height - st.session_state.y2)
        cv2.circle(preview, (int(st.session_state.orig_x), oy_cv), 9, (255, 0, 255), -1)
        cv2.putText(preview, "(0,0)", (int(st.session_state.orig_x) + 14, oy_cv), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        cv2.circle(preview, (int(st.session_state.x1), y1_cv), 5, (0, 255, 255), -1)
        cv2.circle(preview, (int(st.session_state.x2), y2_cv), 5, (0, 255, 255), -1)
        cv2.line(preview, (int(st.session_state.x1), y1_cv), (int(st.session_state.x2), y2_cv), (0, 255, 255), 2)

    obj_y_cv = int(height - st.session_state.obj_y - st.session_state.obj_h)
    cv2.rectangle(
        preview,
        (int(st.session_state.obj_x), obj_y_cv),
        (int(st.session_state.obj_x + st.session_state.obj_w), int(obj_y_cv + st.session_state.obj_h)),
        (255, 0, 0),
        2,
    )
    return preview


def set_tool_point_from_image_coords(ferramenta_ativa, x_click, y_click, width, height):
    x_click = int(max(0, min(width - 1, x_click)))
    y_click = int(max(0, min(height - 1, y_click)))
    y_inv = int(height - y_click)

    updates = {
        "Origem (0,0)": ("orig_x", "orig_y", x_click, y_inv),
        "Calibração: ponto 1": ("x1", "y1", x_click, y_inv),
        "Calibração: ponto 2": ("x2", "y2", x_click, y_inv),
        "Perspectiva: sup. esq. (1)": ("hx1", "hy1", x_click, y_click),
        "Perspectiva: sup. dir. (2)": ("hx2", "hy2", x_click, y_click),
        "Perspectiva: inf. dir. (3)": ("hx3", "hy3", x_click, y_click),
        "Perspectiva: inf. esq. (4)": ("hx4", "hy4", x_click, y_click),
    }
    if ferramenta_ativa == "Objeto: canto inferior esquerdo":
        st.session_state.obj_x = int(max(0, min(width - st.session_state.obj_w, x_click)))
        st.session_state.obj_y = int(max(0, min(height - st.session_state.obj_h, y_inv)))
        return True
    if ferramenta_ativa in updates:
        key_x, key_y, new_x, new_y = updates[ferramenta_ativa]
        st.session_state[key_x] = new_x
        st.session_state[key_y] = new_y
        if ferramenta_ativa.startswith("Perspectiva"):
            st.session_state.pop("matriz_H", None)
            st.session_state.pop("dim_H", None)
            st.session_state.pop("homography_meta", None)
            st.session_state.pop("homography_signature", None)
        return True
    return False


def apply_click(value, scale, width, height, ferramenta_ativa):
    click_signature = (ferramenta_ativa, value)
    if value is None or st.session_state.get("last_click") == click_signature:
        return
    st.session_state.last_click = click_signature
    x_click = int(value["x"] * scale)
    y_click = int(value["y"] * scale)
    if set_tool_point_from_image_coords(ferramenta_ativa, x_click, y_click, width, height):
        rerun()


def get_tool_point_image_coords(ferramenta_ativa, height):
    points = {
        "Origem (0,0)": (st.session_state.orig_x, height - st.session_state.orig_y),
        "Calibração: ponto 1": (st.session_state.x1, height - st.session_state.y1),
        "Calibração: ponto 2": (st.session_state.x2, height - st.session_state.y2),
        "Objeto: canto inferior esquerdo": (st.session_state.obj_x, height - st.session_state.obj_y),
        "Perspectiva: sup. esq. (1)": (st.session_state.hx1, st.session_state.hy1),
        "Perspectiva: sup. dir. (2)": (st.session_state.hx2, st.session_state.hy2),
        "Perspectiva: inf. dir. (3)": (st.session_state.hx3, st.session_state.hy3),
        "Perspectiva: inf. esq. (4)": (st.session_state.hx4, st.session_state.hy4),
    }
    return points.get(ferramenta_ativa)


def render_point_magnifier(frame, ferramenta_ativa):
    height, width = frame.shape[:2]
    point = get_tool_point_image_coords(ferramenta_ativa, height)
    if point is None:
        st.info("Escolha uma ferramenta de ponto para ativar a lupa.")
        return

    x, y = [int(round(value)) for value in point]
    radius = 38
    x0, x1 = max(0, x - radius), min(width, x + radius)
    y0, y1 = max(0, y - radius), min(height, y + radius)
    crop = frame[y0:y1, x0:x1].copy()
    if crop.size:
        zoom = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
        cx = int((x - x0) * 4)
        cy = int((y - y0) * 4)
        cv2.line(zoom, (cx, 0), (cx, zoom.shape[0] - 1), (0, 0, 255), 1)
        cv2.line(zoom, (0, cy), (zoom.shape[1] - 1, cy), (0, 0, 255), 1)
        st.image(cv2.cvtColor(zoom, cv2.COLOR_BGR2RGB), caption="Lupa do ponto ativo", use_container_width=True)

    step = st.number_input("Ajuste fino (px)", min_value=1, max_value=20, value=2, step=1)
    top = st.columns([1, 1, 1])
    middle = st.columns([1, 1, 1])
    if top[1].button("↑", use_container_width=True):
        set_tool_point_from_image_coords(ferramenta_ativa, x, y - step, width, height)
        rerun()
    if middle[0].button("←", use_container_width=True):
        set_tool_point_from_image_coords(ferramenta_ativa, x - step, y, width, height)
        rerun()
    if middle[2].button("→", use_container_width=True):
        set_tool_point_from_image_coords(ferramenta_ativa, x + step, y, width, height)
        rerun()
    bottom = st.columns([1, 1, 1])
    if bottom[1].button("↓", use_container_width=True):
        set_tool_point_from_image_coords(ferramenta_ativa, x, y + step, width, height)
        rerun()


def render_homography_controls():
    with st.expander("Homografia métrica para vídeos não ortogonais", expanded=True):
        st.caption("Marque quatro cantos de um retângulo real no plano do movimento. A imagem original permanece sem distorção; a homografia só converte as coordenadas rastreadas para escala métrica.")
        cols = st.columns(4)
        labels = [
            ("hx1", "hy1", "Superior esquerdo"),
            ("hx2", "hy2", "Superior direito"),
            ("hx3", "hy3", "Inferior direito"),
            ("hx4", "hy4", "Inferior esquerdo"),
        ]
        for col, (key_x, key_y, label) in zip(cols, labels):
            with col:
                st.session_state[key_x] = st.number_input(f"{label} X", value=int(st.session_state[key_x]), step=10)
                st.session_state[key_y] = st.number_input(f"{label} Y", value=int(st.session_state[key_y]), step=10)

        dim_cols = st.columns(2)
        largura_real = dim_cols[0].number_input("Largura real do retângulo (u.m.)", min_value=0.01, value=float(st.session_state.homography_real_width), format="%.4f")
        altura_real = dim_cols[1].number_input("Altura real do retângulo (u.m.)", min_value=0.01, value=float(st.session_state.homography_real_height), format="%.4f")
        points = [
            [st.session_state.hx1, st.session_state.hy1],
            [st.session_state.hx2, st.session_state.hy2],
            [st.session_state.hx3, st.session_state.hy3],
            [st.session_state.hx4, st.session_state.hy4],
        ]
        pixels_por_unidade = estimate_pixels_per_unit(points, largura_real, altura_real)
        st.session_state.homography_real_width = largura_real
        st.session_state.homography_real_height = altura_real
        st.session_state.homography_pixels_per_unit = pixels_por_unidade
        current_signature = tuple(
            int(value)
            for point in points
            for value in point
        ) + (
            round(float(largura_real), 6),
            round(float(altura_real), 6),
            int(pixels_por_unidade),
        )
        if "homography_meta" in st.session_state and current_signature != st.session_state.get("homography_signature"):
            st.session_state.pop("matriz_H", None)
            st.session_state.pop("dim_H", None)
            st.session_state.pop("homography_meta", None)
            st.warning("O plano foi alterado. Aplique novamente o plano métrico antes da análise.")
        st.metric("Resolução automática da planta", f"{pixels_por_unidade} px/u.m.")
        st.caption("Esse valor define quantos pixels representarão cada unidade real no plano retificado. O app estima automaticamente para preservar detalhe sem gerar uma imagem métrica grande demais.")

        if st.button("Aplicar plano métrico", use_container_width=True):
            try:
                _, matrix, size, meta = aplicar_homografia(
                    st.session_state.raw_initial_frame,
                    points,
                    largura_real,
                    altura_real,
                    pixels_por_unidade,
                )
                st.session_state.matriz_H = matrix
                st.session_state.dim_H = size
                st.session_state.homography_meta = meta
                st.session_state.homography_signature = current_signature
                st.session_state.homography_pixels_per_unit = int(round(meta["pixels_per_unit"]))
                st.session_state.scale_source = "homografia_métrica"
                rerun()
            except ValueError as exc:
                st.error(f"Não foi possível calcular a homografia: {exc}")


def render_configuration_step():
    st.markdown("## Passo 3: configuração e análise")
    init_configuration_defaults(st.session_state.raw_initial_frame)

    calibration_mode = st.radio(
        "Tipo de calibração espacial",
        ["Dois pontos", "Plano (homografia métrica)"],
        horizontal=True,
        help="Use dois pontos quando o vídeo for aproximadamente ortogonal. Use plano quando houver perspectiva e linhas reais do cenário.",
    )
    st.session_state.calibration_mode = calibration_mode

    if calibration_mode == "Dois pontos":
        tools = ["Nenhum (apenas visualizar)", "Origem (0,0)", "Calibração: ponto 1", "Calibração: ponto 2", "Objeto: canto inferior esquerdo"]
    else:
        tools = [
            "Nenhum (apenas visualizar)",
            "Objeto: canto inferior esquerdo",
            "Perspectiva: sup. esq. (1)",
            "Perspectiva: sup. dir. (2)",
            "Perspectiva: inf. dir. (3)",
            "Perspectiva: inf. esq. (4)",
        ]
    ferramenta_ativa = st.radio("Ponto definido pelo clique na imagem", tools, horizontal=True)

    frame_ativo = st.session_state.raw_initial_frame.copy()
    overlay = draw_configuration_overlay(frame_ativo, calibration_mode, ferramenta_ativa)
    height, width = overlay.shape[:2]
    target_width = 900
    scale = width / target_width if width > target_width else 1.0
    display = cv2.resize(overlay, (target_width, int(height / scale))) if scale > 1 else overlay

    image_col, loupe_col = st.columns([3, 1])
    with image_col:
        value = streamlit_image_coordinates(cv2.cvtColor(display, cv2.COLOR_BGR2RGB), key="image_click")
        apply_click(value, scale, width, height, ferramenta_ativa)
    with loupe_col:
        render_point_magnifier(overlay, ferramenta_ativa)

    _, buffer = cv2.imencode(".PNG", overlay)
    st.session_state.calibration_image_bytes = BytesIO(buffer).getvalue()
    st.download_button("Baixar imagem de configuração", st.session_state.calibration_image_bytes, "imagem_configuracao.png", "image/png", use_container_width=True)

    if calibration_mode == "Plano (homografia métrica)":
        render_homography_controls()
    if calibration_mode == "Plano (homografia métrica)" and "homography_meta" in st.session_state:
        meta = st.session_state.homography_meta
        st.success(
            f"Plano retificado ativo: {meta['output_width']}x{meta['output_height']} px, "
            f"{meta['pixels_per_unit']:.2f} px/u.m., escala {meta['scale_factor']:.6f} u.m./px."
        )

    if calibration_mode == "Dois pontos":
        col_scale, col_track, col_algorithm = st.columns(3)
        with col_scale:
            st.markdown("#### 1. Escala")
            st.session_state.orig_x = st.number_input("Origem X", value=int(st.session_state.orig_x), step=10)
            st.session_state.orig_y = st.number_input("Origem Y", value=int(st.session_state.orig_y), step=10)
            st.session_state.x1 = st.number_input("Ponto 1 - X", value=int(st.session_state.x1), step=10)
            st.session_state.y1 = st.number_input("Ponto 1 - Y", value=int(st.session_state.y1), step=10)
            st.session_state.x2 = st.number_input("Ponto 2 - X", value=int(st.session_state.x2), step=10)
            st.session_state.y2 = st.number_input("Ponto 2 - Y", value=int(st.session_state.y2), step=10)
            distancia_real = st.number_input("Distância real (u.m.)", min_value=0.01, value=float(st.session_state.dist_real), format="%.4f", key="dist_real_input")
            st.session_state.dist_real = distancia_real
    else:
        col_track, col_algorithm = st.columns(2)
        distancia_real = None

    with col_track:
        st.markdown("#### 2. Objeto")
        st.session_state.obj_x = st.number_input("Canto esquerdo - X", value=int(st.session_state.obj_x), step=10)
        st.session_state.obj_y = st.number_input("Canto inferior - Y", value=int(st.session_state.obj_y), step=10)
        st.session_state.obj_w = st.number_input("Largura da caixa", min_value=1, value=int(st.session_state.obj_w), step=10)
        st.session_state.obj_h = st.number_input("Altura da caixa", min_value=1, value=int(st.session_state.obj_h), step=10)

    with col_algorithm:
        st.markdown("#### 3. Algoritmo")
        stamp_density = render_stamp_density_selector()
        total_frames_corte = st.session_state.end_frame_for_analysis - st.session_state.start_frame_for_analysis + 1
        max_janela = total_frames_corte if total_frames_corte % 2 else total_frames_corte - 1
        max_janela = max(5, int(max_janela))

        st.markdown("**Suavização:**")
        auto_savgol = st.checkbox("Escolher filtro automaticamente", value=True)
        perfil_label = st.radio(
            "Objetivo",
            ["Geral", "Gravidade", "Impacto"],
            horizontal=True,
            help="Define o critério usado para escolher janela e ordem do Savitzky-Golay.",
        )
        perfil_map = {
            "Geral": "balanced",
            "Gravidade": "constant_acceleration",
            "Impacto": "fast_event",
        }
        savgol_profile = perfil_map[perfil_label]
        window_size, poly_order = preview_savgol_pair(total_frames_corte, savgol_profile)
        if auto_savgol:
            st.caption(f"Prévia para este objetivo: `w={window_size}` e `d={poly_order}`. O valor final é confirmado após o rastreio.")
        else:
            with st.expander("Ajuste manual do filtro", expanded=True):
                bounds = estimate_savgol_bounds(total_frames_corte)
                if bounds:
                    st.caption(f"Limites: janela {bounds[0]}-{bounds[1]}, ordem {bounds[2]}-{bounds[3]}.")
                else:
                    st.caption("Corte curto demais para otimização automática.")
                window_size = st.slider("Janela (w)", min_value=5, max_value=int(max_janela), value=min(11, int(max_janela)), step=2)
                poly_order = st.slider("Ordem (d)", min_value=2, max_value=4, value=2)

    if st.button("Iniciar análise", type="primary", use_container_width=True):
        homography_matrix = None
        homography_size = None
        if calibration_mode == "Plano (homografia métrica)":
            if "homography_meta" not in st.session_state or "matriz_H" not in st.session_state:
                st.error("Aplique o plano métrico antes de iniciar a análise.")
                return
            meta = st.session_state.homography_meta
            scale_factor = float(meta["scale_factor"])
            origin_coords = (0, int(meta["output_height"] - 1))
            homography_matrix = st.session_state.get("matriz_H")
            homography_size = st.session_state.get("dim_H")
        else:
            oy_cv = int(height - st.session_state.orig_y)
            y1_cv = int(height - st.session_state.y1)
            y2_cv = int(height - st.session_state.y2)
            length_pixels = float(np.sqrt((st.session_state.x2 - st.session_state.x1) ** 2 + (y2_cv - y1_cv) ** 2))
            if length_pixels <= 0:
                st.error("A distância da calibração não pode ser zero.")
                return
            scale_factor = distancia_real / length_pixels
            origin_coords = (int(st.session_state.orig_x), oy_cv)

        obj_y_cv = int(height - st.session_state.obj_y - st.session_state.obj_h)
        bbox = (int(st.session_state.obj_x), obj_y_cv, int(st.session_state.obj_w), int(st.session_state.obj_h))
        st.session_state.csv_header = (
            f"# Análise de Movimento - {pd.Timestamp.now()}\n"
            f"# Frame inicial: {st.session_state.start_frame_for_analysis}\n"
            f"# Frame final: {st.session_state.end_frame_for_analysis}\n"
            f"# Origem em pixels: {origin_coords}\n"
            f"# Fator de escala: {scale_factor:.6f} u.m./pixel\n"
            f"# Tipo de calibração espacial: {calibration_mode}\n"
            f"# Densidade estroboscópica: {stamp_density.label}\n"
            f"# Espaçamento mínimo entre marcações: {stamp_density.spacing_units:.4f} u.m.\n"
            "# ---\n"
        )
        st.session_state.analysis_context = {
            "video_name": st.session_state.get("video_name", "vídeo analisado"),
            "video_source": st.session_state.get("video_source", "-"),
            "start_frame": st.session_state.start_frame_for_analysis,
            "end_frame": st.session_state.end_frame_for_analysis,
            "origin": origin_coords,
            "scale_factor": scale_factor,
            "calibration_mode": calibration_mode,
            "stamp_density": stamp_density.label,
            "stamp_spacing": stamp_density.spacing_units,
        }
        if calibration_mode == "Plano (homografia métrica)" and "homography_meta" in st.session_state:
            meta = st.session_state.homography_meta
            st.session_state.analysis_context["homography"] = meta
            st.session_state.csv_header += (
                "# Homografia métrica ativa: True\n"
                f"# Retângulo real da homografia: {meta['real_width']:.6f} x {meta['real_height']:.6f} u.m.\n"
                f"# Resolução da homografia: {meta['pixels_per_unit']:.6f} px/u.m.\n"
                f"# Dimensão retificada: {meta['output_width']} x {meta['output_height']} px\n"
                f"# Escala da homografia: {meta['scale_factor']:.8f} u.m./pixel\n"
                f"# Fonte da escala: {st.session_state.get('scale_source', 'calibração manual')}\n"
                "# ---\n"
            )

        status_text = st.empty()
        with st.spinner("Extraindo cinemática..."):
            results = processar_video(
                st.session_state.video_bytes,
                frame_ativo,
                st.session_state.start_frame_for_analysis,
                st.session_state.end_frame_for_analysis,
                bbox,
                stamp_density.spacing_units,
                scale_factor,
                origin_coords,
                status_text,
                window_size,
                poly_order,
                homography_matrix,
                homography_size,
                auto_savgol,
                savgol_profile,
            )
        if results:
            savgol_meta = results[4]
            st.session_state.csv_header += (
                f"# Savitzky-Golay automático: {savgol_meta.get('auto_savgol')}\n"
                f"# Perfil Savitzky-Golay: {savgol_meta.get('profile')}\n"
                f"# Janela Savitzky-Golay: {savgol_meta.get('window_size')}\n"
                f"# Ordem Savitzky-Golay: {savgol_meta.get('poly_order')}\n"
                "# ---\n"
            )
            st.session_state.results = results
            rerun()


def render_results():
    st.markdown("## Resultados da análise")
    img_estrob_bytes, df_final, figura_graficos, video_track_bytes, savgol_metadata = st.session_state.results
    st.success(
        "Filtro aplicado: "
        f"`w={savgol_metadata.get('window_size')}` e `d={savgol_metadata.get('poly_order')}`."
    )
    if savgol_metadata.get("auto_savgol") and "recommended_window_min" in savgol_metadata:
        st.caption(
            f"{savgol_metadata.get('message', '')} "
            f"erro selecionado `{savgol_metadata.get('selected_error_score', 0):.6g}`, "
            f"erro mínimo observado `{savgol_metadata.get('minimum_error_score', 0):.6g}`, "
            f"custo relativo `{savgol_metadata.get('compute_cost', 0):.0f}`."
        )

    with st.expander("Imagens, gráficos e tabela", expanded=True):
        img_col, download_col = st.columns(2)
        with img_col:
            st.image(img_estrob_bytes, caption="Imagem estroboscópica")
        with download_col:
            st.download_button("Baixar vídeo com rastreio", video_track_bytes, "video_rastreado.mp4", "video/mp4", use_container_width=True)
            st.download_button("Baixar imagem composta", img_estrob_bytes, "imagem_estroboscopica.png", "image/png", use_container_width=True)
        st.pyplot(figura_graficos)
        try:
            from report_generation import generate_student_report_pdf

            report_bytes = generate_student_report_pdf(
                st.session_state.get("analysis_context", {}),
                st.session_state.get("calibration_image_bytes", img_estrob_bytes),
                img_estrob_bytes,
                df_final,
                figura_graficos,
                savgol_metadata,
                st.session_state.get("img_vetores"),
            )
            st.download_button(
                "Exportar relatório da análise (PDF)",
                report_bytes,
                "relatorio_analise_movimento.pdf",
                "application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.warning(f"Não foi possível gerar o relatório PDF: {exc}")
        st.dataframe(df_final)
        csv_final = (st.session_state.get("csv_header", "") + df_final.to_csv(index=False)).encode("utf-8-sig")
        st.download_button(
            "Baixar tabela CSV",
            csv_final,
            "dados_analise.csv",
            "text/csv",
            use_container_width=True,
        )

    with st.expander("Ajuste de curvas teóricas", expanded=True):
        col_axis, col_model = st.columns(2)
        eixo = col_axis.selectbox("Eixo de análise", ["Posição Y", "Posição X"])
        modelo = col_model.selectbox("Modelo físico", ["Linear", "Quadrático"])
        y_data = df_final["pos_y_um"] if eixo == "Posição Y" else df_final["pos_x_um"]
        t_data = df_final["tempo_s"]
        grau = 1 if modelo == "Linear" else 2
        _, y_pred, r2, coefs = calcular_ajuste_teorico(t_data, y_data, grau)
        st.markdown(f"**R²:** `{r2:.4f}`")
        if grau == 1:
            st.markdown(f"**Equação:** S(t) = {coefs[0]:.4f}t + ({coefs[1]:.4f})")
        else:
            st.markdown(f"**Equação:** S(t) = {coefs[0]:.4f}t² + {coefs[1]:.4f}t + ({coefs[2]:.4f})")
            st.markdown(f"**Aceleração constante estimada:** `{2 * coefs[0]:.4f} u.m./s²`")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(t_data, y_data, color="blue", alpha=0.5, label="Dados reais")
        ax.plot(t_data, y_pred, color="red", linewidth=2, label=f"Ajuste {modelo}")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel(eixo)
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

    with st.expander("Vetores de velocidade", expanded=True):
        colors = {
            "Vermelho": (0, 0, 255),
            "Azul": (255, 0, 0),
            "Amarelo": (0, 255, 255),
            "Verde": (0, 255, 0),
            "Branco": (255, 255, 255),
        }
        color_col, width_col = st.columns(2)
        color_name = color_col.selectbox("Cor do vetor", list(colors.keys()))
        thickness = width_col.slider("Espessura", 1, 5, 2)
        scale_col, max_col = st.columns(2)
        vector_scale = scale_col.slider("Escala do vetor", 1, 200, 50)
        max_length = max_col.slider("Comprimento máximo (px)", 10, 200, 100)
        if st.button("Gerar imagem com vetores", use_container_width=True):
            imagem = cv2.imdecode(np.frombuffer(img_estrob_bytes, np.uint8), 1)
            stamped = df_final[df_final["is_stamp"] == True]
            st.session_state.img_vetores = desenhar_vetores_velocidade(imagem, stamped, vector_scale, max_length, colors[color_name], thickness)
        if st.session_state.get("img_vetores"):
            st.image(st.session_state.img_vetores, caption="Imagem com vetores de velocidade")
            st.download_button("Baixar imagem com vetores", st.session_state.img_vetores, "imagem_com_vetores.png", "image/png", use_container_width=True)

    if st.button("Analisar outro vídeo", use_container_width=True):
        reset_video_state()
        rerun()


def main():
    st.session_state.setdefault("step", "upload")
    st.session_state.setdefault("results", None)

    if st.session_state.step == "upload":
        render_upload_step()
    elif st.session_state.step == "frame_selection":
        render_frame_selection()
    elif st.session_state.step == "configuration":
        render_configuration_step()

    if st.session_state.results:
        st.markdown("---")
        render_results()

    if st.session_state.step == "upload" and not st.session_state.results:
        render_contact_footer()


if __name__ == "__main__":
    main()
