"""01_probe_segment.py
Deterministic video segmentation. No model calls. Exact numbers only.
"""
import json, subprocess, shlex, sys
from pathlib import Path

def ffprobe_meta(video: str) -> dict:
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries ' \
          f'stream=width,height,r_frame_rate,duration,nb_frames -of json {shlex.quote(video)}'
    out = subprocess.check_output(shlex.split(cmd))
    meta = json.loads(out)["streams"][0]
    num, den = meta["r_frame_rate"].split("/")
    meta["fps"] = round(int(num) / int(den), 4)
    meta["duration"] = float(meta.get("duration", 0))
    return meta

def detect_cuts(video: str, threshold: float = 0.28) -> list[float]:
    """Scene-cut timestamps via ffmpeg's scdet filter (exact, deterministic)."""
    cmd = (f'ffmpeg -i {shlex.quote(video)} -filter:v '
           f'"select=\'gt(scene,{threshold})\',showinfo" -f null -')
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    cuts = []
    for line in proc.stderr.splitlines():
        if "pts_time:" in line:
            ts = line.split("pts_time:")[1].split()[0]
            cuts.append(float(ts))
    return cuts

def detect_freezes(video: str, noise: str = "0.001", duration: float = 0.3) -> list[tuple]:
    """Segments where nothing moves — used later to detect animation holds/loops."""
    cmd = (f'ffmpeg -i {shlex.quote(video)} -vf '
           f'"freezedetect=n={noise}:d={duration}" -map 0:v:0 -f null -')
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    freezes, start = [], None
    for line in proc.stderr.splitlines():
        if "freeze_start:" in line:
            start = float(line.split("freeze_start:")[1].strip())
        if "freeze_end:" in line and start is not None:
            end = float(line.split("freeze_end:")[1].split()[0].strip())
            freezes.append((start, end))
            start = None
    return freezes

def run(video: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    result = {
        "meta": ffprobe_meta(video),
        "scene_cuts": detect_cuts(video),
        "freezes": detect_freezes(video),
    }
    Path(out_dir, "segment_report.json").write_text(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
