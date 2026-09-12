"""03_keyframe_curation.py"""
import cv2, imagehash, numpy as np
from PIL import Image
from pathlib import Path
import json

def extract_all_frames(video_path: str, tmp_dir: str) -> list[str]:
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    paths, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        p = f"{tmp_dir}/f{i:05d}.png"
        cv2.imwrite(p, frame)
        paths.append(p)
        i += 1
    cap.release()
    return paths

def curate(frame_paths: list[str], motion_energy: list[float],
           max_frames: int = 20, hash_threshold: int = 4) -> list[dict]:
    """Bins the timeline into coverage windows, keeps the highest-motion,
    least-redundant frame in each bin (perceptual hash de-dup)."""
    n = len(frame_paths)
    bins = np.array_split(range(n), max_frames)
    kept, seen_hashes = [], []
    for b in bins:
        if len(b) == 0:
            continue
        best_idx = max(b, key=lambda i: motion_energy[i] if i < len(motion_energy) else 0)
        img = Image.open(frame_paths[best_idx])
        h = imagehash.phash(img)
        if all(h - seen > hash_threshold for seen in seen_hashes):
            seen_hashes.append(h)
            kept.append({"frame_index": int(best_idx), "path": frame_paths[best_idx],
                         "motion_energy": float(motion_energy[best_idx]) if best_idx < len(motion_energy) else 0})
    return kept

def run(video: str, tmp_dir: str, motion_profile_json: str, out_dir: str, max_frames=20):
    frames = extract_all_frames(video, tmp_dir)
    profile = json.loads(Path(motion_profile_json).read_text())
    keyframes = curate(frames, profile["motion_energy"], max_frames)
    Path(out_dir, "keyframes.json").write_text(json.dumps(keyframes, indent=2))
    return keyframes
