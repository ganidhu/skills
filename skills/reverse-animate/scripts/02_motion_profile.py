"""02_motion_profile.py
Optical-flow based motion energy + automatic easing-curve fitting.
"""
import cv2, numpy as np, json
from scipy.optimize import curve_fit
from pathlib import Path

def motion_energy_series(video_path: str) -> np.ndarray:
    cap = cv2.VideoCapture(video_path)
    ok, prev = cap.read()
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    energies = [0.0]
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        energies.append(float(mag.mean()))
        prev_gray = gray
    cap.release()
    return np.array(energies)

def cubic_bezier(t, x1, y1, x2, y2):
    # De Casteljau approximation for a 1D progress curve driven by a
    # standard CSS cubic-bezier(x1,y1,x2,y2) timing function.
    def bezier(t, p0, p1, p2, p3):
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + \
               3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return bezier(t, 0, y1, y2, 1)

def fit_easing(velocity_curve: np.ndarray) -> dict:
    t = np.linspace(0, 1, len(velocity_curve))
    progress = np.cumsum(velocity_curve)
    progress = (progress - progress.min()) / (progress.max() - progress.min() + 1e-9)
    try:
        popt, _ = curve_fit(cubic_bezier, t, progress,
                             p0=[0.25, 0.1, 0.25, 1.0], maxfev=5000)
        x1, y1, x2, y2 = [round(float(v), 3) for v in popt]
    except Exception:
        x1, y1, x2, y2 = 0.25, 0.1, 0.25, 1.0  # ease-in-out fallback
    return {"cubic_bezier": [x1, y1, x2, y2],
            "css_name": nearest_named_easing(x1, y1, x2, y2)}

NAMED_EASINGS = {
    "linear": (0, 0, 1, 1), "ease": (0.25, 0.1, 0.25, 1),
    "ease-in": (0.42, 0, 1, 1), "ease-out": (0, 0, 0.58, 1),
    "ease-in-out": (0.42, 0, 0.58, 1),
    "back-out": (0.34, 1.56, 0.64, 1), "elastic-approx": (0.68, -0.55, 0.27, 1.55),
}

def nearest_named_easing(x1, y1, x2, y2) -> str:
    best, best_d = "custom", 0.12
    for name, (a, b, c, d) in NAMED_EASINGS.items():
        dist = ((x1 - a) ** 2 + (y1 - b) ** 2 + (x2 - c) ** 2 + (y2 - d) ** 2) ** 0.5
        if dist < best_d:
            best, best_d = name, dist
    return best

def detect_loop(energies: np.ndarray, fps: float) -> dict:
    """Autocorrelation to find periodic/looping motion (spinners, pulses)."""
    ac = np.correlate(energies - energies.mean(), energies - energies.mean(), "full")
    ac = ac[len(ac) // 2:]
    peaks = [i for i in range(2, len(ac) - 1) if ac[i] > ac[i - 1] and ac[i] > ac[i + 1]]
    if not peaks:
        return {"loops": False}
    period_frames = peaks[0]
    return {"loops": True, "period_seconds": round(period_frames / fps, 3)}

def run(video: str, fps: float, out_dir: str):
    energies = motion_energy_series(video)
    easing = fit_easing(energies)
    loop = detect_loop(energies, fps)
    stagger_candidates = detect_stagger(energies, fps)
    report = {"motion_energy": energies.tolist(), "easing": easing,
              "loop": loop, "stagger_candidates": stagger_candidates}
    Path(out_dir, "motion_profile.json").write_text(json.dumps(report, indent=2))
    return report

def detect_stagger(energies: np.ndarray, fps: float, min_gap=0.03) -> list:
    """Finds repeated local-maxima clusters spaced evenly — signature of
    staggered element entrances (list items animating in sequence)."""
    peaks = [i for i in range(1, len(energies) - 1)
             if energies[i] > energies[i - 1] and energies[i] > energies[i + 1]
             and energies[i] > energies.mean() * 1.3]
    gaps = np.diff([p / fps for p in peaks])
    if len(gaps) >= 2 and np.std(gaps) < min_gap:
        return [{"count": len(peaks), "interval_seconds": round(float(np.mean(gaps)), 3)}]
    return []
