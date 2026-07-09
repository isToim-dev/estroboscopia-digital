from functools import lru_cache

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

from app_config import STAMP_DENSITY_PRESETS


@lru_cache(maxsize=8)
def make_parabola_density_icon(point_count: int, active: bool = False):
    width, height = 360, 180
    bg = "#F8FAFD" if not active else "#E7F0FF"
    line = "#2E6DB4" if active else "#6F8298"
    point = "#D02C2C" if active else "#46515E"
    border = "#2E6DB4" if active else "#D7E0EA"

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([3, 3, width - 4, height - 4], radius=18, outline=border, width=5 if active else 3)

    xs = np.linspace(36, width - 36, 120)
    t = np.linspace(-1, 1, 120)
    ys = 132 - 78 * (1 - t**2)
    curve = list(zip(xs, ys))
    draw.line(curve, fill=line, width=5)

    sample_t = np.linspace(-1, 1, point_count)
    sample_x = np.linspace(36, width - 36, point_count)
    sample_y = 132 - 78 * (1 - sample_t**2)
    radius = 7 if point_count <= 9 else 5
    for x, y in zip(sample_x, sample_y):
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=point)

    return img


def render_stamp_density_selector():
    st.markdown("**Densidade da imagem estroboscópica:**")
    preset_keys = list(STAMP_DENSITY_PRESETS.keys())
    selected_key = st.select_slider(
        "Quantidade de marcações na trajetória",
        options=preset_keys,
        value=st.session_state.get("stamp_density_key", "media"),
        format_func=lambda key: STAMP_DENSITY_PRESETS[key].label,
        help="Controla a distância mínima entre as marcações do objeto na imagem composta.",
    )
    st.session_state.stamp_density_key = selected_key

    cols = st.columns(3)
    for index, key in enumerate(preset_keys):
        preset = STAMP_DENSITY_PRESETS[key]
        with cols[index]:
            st.image(make_parabola_density_icon(preset.point_count, active=key == selected_key), use_container_width=True)

    return STAMP_DENSITY_PRESETS[selected_key]
