import streamlit as st


VIDEO_STATE_KEYS = [
    "video_bytes", "video_name", "video_source", "video_fps", "video_frame_count",
    "preview_idx", "start_idx", "end_idx", "raw_initial_frame", "frame_trabalho",
    "start_frame_for_analysis", "end_frame_for_analysis", "results", "csv_header",
    "matriz_H", "dim_H", "homography_meta", "homography_real_width",
    "homography_real_height", "homography_pixels_per_unit", "homography_signature", "scale_source",
    "dist_real", "img_vetores", "stamp_density_key", "calibration_mode", "last_click",
    "report_team_count", "report_analysis_date", "report_pdf_bytes",
    "orig_x", "orig_y", "x1", "y1", "x2", "y2", "obj_x", "obj_y", "obj_w", "obj_h",
    "hx1", "hy1", "hx2", "hy2", "hx3", "hy3", "hx4", "hy4",
]


def reset_video_state():
    for key in VIDEO_STATE_KEYS:
        if key in st.session_state:
            del st.session_state[key]
    for key in list(st.session_state.keys()):
        if key.startswith("report_student_name_") or key.startswith("report_student_grade_"):
            del st.session_state[key]
    st.session_state.step = "upload"


def load_selected_video(video_bytes, name, source, fps=None, frame_count=None):
    reset_video_state()
    st.session_state.video_bytes = video_bytes
    st.session_state.video_name = name
    st.session_state.video_source = source
    st.session_state.video_fps = fps
    st.session_state.video_frame_count = frame_count
    st.session_state.step = "frame_selection"
    st.session_state.results = None
