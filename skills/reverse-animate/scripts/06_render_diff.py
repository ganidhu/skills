"""06_render_diff.py"""
import subprocess, json, sys, numpy as np
from pathlib import Path
from skimage.metrics import structural_similarity as ssim
import cv2
from importlib import import_module

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
motion_mod = import_module("02_motion_profile")

def record_html(html_path: str, out_video: str, duration_s: float, fps: int = 30):
    """Uses Playwright to load the generated animation and screen-record it."""
    script = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={{"width":1280,"height":720}},
            record_video_dir="{Path(out_video).parent}",
            record_video_size={{"width":1280,"height":720}})
        await page.goto("file://{Path(html_path).resolve()}")
        await page.wait_for_timeout({int(duration_s * 1000)})
        await browser.close()

asyncio.run(main())
"""
    tmp = Path(out_video).resolve().parent / "_record_tmp.py"
    tmp.write_text(script)
    subprocess.run(["python3", str(tmp)], check=True)

def resample(video_path: str, fps: int, size=(1280, 720)) -> np.ndarray:
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(f, size))
    cap.release()
    return np.array(frames)

def compare(orig_frames: np.ndarray, rendered_frames: np.ndarray) -> dict:
    n = min(len(orig_frames), len(rendered_frames))
    scores = [ssim(orig_frames[i], rendered_frames[i], channel_axis=2)
              for i in range(n)]
    timing_delta = abs(len(orig_frames) - len(rendered_frames))
    return {"mean_ssim": float(np.mean(scores)), "min_ssim": float(np.min(scores)),
            "frame_count_delta": int(timing_delta),
            "per_frame_ssim": [float(s) for s in scores]}

def run(original_video: str, rendered_video: str, out_dir: str, fps: int = 30) -> dict:
    orig = resample(original_video, fps)
    rend = resample(rendered_video, fps)
    report = compare(orig, rend)
    Path(out_dir, "fidelity_report.json").write_text(json.dumps(report, indent=2))
    return report
