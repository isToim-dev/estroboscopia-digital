import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from app_config import APP_DIR, VIDEO_EXTENSIONS


def discover_validation_dir():
    candidates = [
        APP_DIR / "videos_validacao",
        APP_DIR / "Video - Validação",
        APP_DIR.parent / "Video - Validação",
        APP_DIR.parent.parent / "Video - Validação",
    ]
    for path in candidates:
        if path.exists() and any(p.suffix.lower() in VIDEO_EXTENSIONS for p in path.glob("*")):
            return path

    for base in [APP_DIR, APP_DIR.parent, APP_DIR.parent.parent]:
        if not base.exists():
            continue
        for path in base.iterdir():
            if not path.is_dir():
                continue
            normalized_name = unicodedata.normalize("NFKD", path.name).encode("ascii", "ignore").decode("ascii").lower()
            if "video" in normalized_name and any(p.suffix.lower() in VIDEO_EXTENSIONS for p in path.glob("*")):
                return path
    return None


def read_video_metadata(video_path):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return fps, frame_count, width, height


def fps_from_filename(video_path):
    match = re.search(r"fps[_\s-]*(\d+)", video_path.stem, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


@lru_cache(maxsize=16)
def make_video_thumbnail(video_path_str):
    video_path = Path(video_path_str)
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    target_frame = max(0, min(total_frames - 1, total_frames // 3)) if total_frames else 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    success, frame = cap.read()
    if not success:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        success, frame = cap.read()
    cap.release()

    if not success:
        thumb = np.full((220, 360, 3), 238, dtype=np.uint8)
        cv2.putText(thumb, "Sem miniatura", (64, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (70, 84, 100), 2)
        return thumb

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width = frame_rgb.shape[:2]
    target_width = 420
    target_height = 250
    scale = max(target_width / width, target_height / height)
    resized = cv2.resize(frame_rgb, (int(width * scale), int(height * scale)))
    y0 = max(0, (resized.shape[0] - target_height) // 2)
    x0 = max(0, (resized.shape[1] - target_width) // 2)
    return resized[y0:y0 + target_height, x0:x0 + target_width]


def list_validation_videos():
    validation_dir = discover_validation_dir()
    if not validation_dir:
        return []

    videos = []
    for path in validation_dir.glob("*"):
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        fps, frame_count, width, height = read_video_metadata(path)
        fps_label = fps_from_filename(path) or round(fps, 2)
        videos.append({
            "path": path,
            "name": path.stem.replace("_", " "),
            "fps_label": fps_label,
            "fps_detected": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "size_kb": path.stat().st_size / 1024,
        })
    return sorted(videos, key=lambda video: (float(video["fps_label"]), video["path"].name))
