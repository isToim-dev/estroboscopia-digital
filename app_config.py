from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}


@dataclass(frozen=True)
class StampDensityPreset:
    key: str
    label: str
    spacing_units: float
    point_count: int
    description: str


STAMP_DENSITY_PRESETS = {
    "poucos": StampDensityPreset(
        key="poucos",
        label="Poucos pontos",
        spacing_units=1.0,
        point_count=5,
        description="Maior distância entre marcações; imagem mais limpa.",
    ),
    "media": StampDensityPreset(
        key="media",
        label="Densidade média",
        spacing_units=0.5,
        point_count=9,
        description="Equilíbrio entre leitura visual e continuidade da curva.",
    ),
    "alta": StampDensityPreset(
        key="alta",
        label="Muitos pontos",
        spacing_units=0.2,
        point_count=17,
        description="Menor distância entre marcações; curva mais contínua.",
    ),
}


DEFAULT_APP_CSS = """
<style>
.stButton > button {
    background-color: #0072C6;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    border: 1px solid #005A9E;
    padding: 0.5em 1em;
    transition: background-color 0.3s;
}
.stButton > button:hover {
    background-color: #005A9E;
    color: white;
    border-color: #003B65;
}
.stDownloadButton > button {
    background-color: #1E8A42;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    border: 1px solid #176B34;
    padding: 0.5em 1em;
    transition: background-color 0.3s;
}
.stDownloadButton > button:hover {
    background-color: #176B34;
    color: white;
    border-color: #104A23;
}
.direct-download-link {
    display: block;
    width: 100%;
    box-sizing: border-box;
    background-color: #1E8A42;
    color: white !important;
    font-weight: bold;
    text-align: center;
    text-decoration: none !important;
    border-radius: 5px;
    border: 1px solid #176B34;
    padding: 0.55em 1em;
    margin: 0.35rem 0;
    transition: background-color 0.3s;
}
.direct-download-link:hover {
    background-color: #176B34;
    color: white !important;
    border-color: #104A23;
}
.sample-video-card {
    border: 1px solid #D7E0EA;
    border-radius: 8px;
    padding: 12px 12px 14px 12px;
    background: #F8FAFD;
    min-height: 100%;
}
.sample-video-title {
    font-weight: 700;
    color: #172033;
    margin: 4px 0 2px 0;
}
.sample-video-meta {
    color: #516070;
    font-size: 0.92rem;
    margin-bottom: 8px;
}
.upload-choice-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #172033;
    margin-bottom: 0.35rem;
}
.institutional-footer {
    background: #F7FAFC;
    border: 1px solid #D7E0EA;
    border-radius: 8px;
    color: #172033;
    margin-top: 2.25rem;
    padding: 0.85rem 1rem;
}
.institutional-footer__title {
    color: #172033;
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.institutional-footer__line {
    color: #344054;
    font-size: 0.9rem;
    line-height: 1.45;
    margin: 0;
}
</style>
"""
