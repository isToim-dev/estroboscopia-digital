import os
import tempfile
from io import BytesIO

import cv2
import numpy as np
import pandas as pd

from savgol_reverse import apply_savgol_kinematics, optimize_savgol_parameters
from visualization import plotar_graficos


def calcular_ajuste_teorico(t, y, grau):
    coefs = np.polyfit(t, y, grau)
    p = np.poly1d(coefs)
    y_pred = p(t)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return p, y_pred, r2, coefs


def processar_video(
    video_bytes,
    initial_frame,
    start_frame_idx,
    end_frame_idx,
    bbox_coords_opencv,
    fator_distancia,
    scale_factor,
    origin_coords,
    status_text_element,
    window_size=11,
    poly_order=2,
    matriz_homografia=None,
    dimensao_homografia=None,
    auto_savgol=False,
    savgol_profile="balanced",
):
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(video_bytes)
    tfile.close()
    video_path = tfile.name

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for _ in range(start_frame_idx):
        cap.read()

    tracker = cv2.TrackerCSRT_create()
    tracker.init(initial_frame, bbox_coords_opencv)

    imagem_estroboscopica = initial_frame.copy()
    altura_frame, largura_frame, _ = initial_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    temp_video_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_video_out.close()
    out_video = cv2.VideoWriter(temp_video_out.name, fourcc, fps, (largura_frame, altura_frame))

    carimbos_data = []
    posicao_ultimo_carimbo_px = (
        bbox_coords_opencv[0] + bbox_coords_opencv[2] / 2,
        bbox_coords_opencv[1] + bbox_coords_opencv[3] / 2,
    )
    if matriz_homografia is not None:
        posicao_ultimo_carimbo_px = tuple(
            cv2.perspectiveTransform(
                np.array([[posicao_ultimo_carimbo_px]], dtype=np.float32),
                matriz_homografia,
            )[0, 0]
        )

    contador_frames_processados = 0
    while True:
        frame_atual_idx = start_frame_idx + contador_frames_processados
        if frame_atual_idx > end_frame_idx or frame_atual_idx >= total_frames:
            break

        success, frame_atual = cap.read()
        if not success:
            break

        status_text_element.text(f"Processando e Rastreando frame {frame_atual_idx}/{end_frame_idx}...")
        success_track, bbox_atual = tracker.update(frame_atual)
        frame_video_out = frame_atual.copy()

        if success_track:
            centro_atual_px = (bbox_atual[0] + bbox_atual[2] / 2, bbox_atual[1] + bbox_atual[3] / 2)
            centro_medida_px = centro_atual_px
            if matriz_homografia is not None:
                centro_medida_px = tuple(
                    cv2.perspectiveTransform(
                        np.array([[centro_atual_px]], dtype=np.float32),
                        matriz_homografia,
                    )[0, 0]
                )
            dist_pixels = np.sqrt(
                (centro_medida_px[0] - posicao_ultimo_carimbo_px[0]) ** 2
                + (centro_medida_px[1] - posicao_ultimo_carimbo_px[1]) ** 2
            )

            (x, y, w, h) = [int(v) for v in bbox_atual]
            cv2.rectangle(frame_video_out, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame_video_out, (int(centro_atual_px[0]), int(centro_atual_px[1])), 4, (0, 0, 255), -1)

            carimbos_data.append([frame_atual_idx, centro_medida_px[0], centro_medida_px[1]])

            is_stamp = False
            if contador_frames_processados == 0 or (dist_pixels * scale_factor >= fator_distancia):
                is_stamp = True
                x_s, y_s = max(x, 0), max(y, 0)
                x_e, y_e = min(x + w, largura_frame), min(y + h, altura_frame)
                regiao = frame_atual[y_s:y_e, x_s:x_e]
                if regiao.size > 0:
                    imagem_estroboscopica[y_s:y_e, x_s:x_e] = regiao
                posicao_ultimo_carimbo_px = centro_medida_px

            carimbos_data[-1].append(is_stamp)

        out_video.write(frame_video_out)
        contador_frames_processados += 1

    cap.release()
    out_video.release()
    os.remove(video_path)

    if len(carimbos_data) < 2:
        status_text_element.error(
            "Erro crítico: o algoritmo perdeu o objeto. Verifique contraste, enquadramento e caixa inicial de rastreio."
        )
        return None

    with open(temp_video_out.name, "rb") as f:
        video_track_bytes = f.read()
    os.remove(temp_video_out.name)

    df_carimbos = pd.DataFrame(carimbos_data, columns=["frame", "pos_x_px", "pos_y_px", "is_stamp"])
    df_carimbos["tempo_s"] = (df_carimbos["frame"] - start_frame_idx) / fps
    df_carimbos["pos_x_um"] = (df_carimbos["pos_x_px"] - origin_coords[0]) * scale_factor
    df_carimbos["pos_y_um"] = -(df_carimbos["pos_y_px"] - origin_coords[1]) * scale_factor

    savgol_metadata = {
        "auto_savgol": bool(auto_savgol),
        "profile": savgol_profile,
        "window_size": int(window_size),
        "poly_order": int(poly_order),
        "message": "Parâmetros definidos manualmente.",
    }

    if auto_savgol:
        optimization = optimize_savgol_parameters(
            df_carimbos["tempo_s"].to_numpy(),
            df_carimbos["pos_x_um"].to_numpy(),
            df_carimbos["pos_y_um"].to_numpy(),
            profile=savgol_profile,
        )
        if optimization is not None:
            window_size = optimization.window_length
            poly_order = optimization.polyorder
            savgol_metadata.update({
                "window_size": int(window_size),
                "poly_order": int(poly_order),
                "window_min": int(optimization.window_min),
                "window_max": int(optimization.window_max),
                "poly_order_min": int(optimization.polyorder_min),
                "poly_order_max": int(optimization.polyorder_max),
                "recommended_window_min": int(optimization.recommended_window_range[0]),
                "recommended_window_max": int(optimization.recommended_window_range[1]),
                "recommended_poly_order_min": int(optimization.recommended_polyorder_range[0]),
                "recommended_poly_order_max": int(optimization.recommended_polyorder_range[1]),
                "score": float(optimization.score),
                "minimum_error_score": float(optimization.minimum_error_score),
                "selected_error_score": float(optimization.selected_error_score),
                "compute_cost": float(optimization.compute_cost),
                "error_tolerance": float(optimization.error_tolerance),
                "message": optimization.message,
            })
        else:
            savgol_metadata["message"] = "Amostra curta demais para otimização; usados parâmetros manuais."

    df_carimbos = apply_savgol_kinematics(df_carimbos, fps, window_size, poly_order)
    df_final = df_carimbos.fillna(0)
    status_text_element.success(f"Processamento concluído! {len(df_final)} pontos extraídos.")

    _, buffer_img_estrob = cv2.imencode(".PNG", imagem_estroboscopica)
    img_estrob_bytes = BytesIO(buffer_img_estrob).getvalue()
    figura_graficos = plotar_graficos(df_final)

    return img_estrob_bytes, df_final, figura_graficos, video_track_bytes, savgol_metadata
