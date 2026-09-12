"""07_orchestrator.py — the skill's entrypoint."""
import json, sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import importlib
S1 = importlib.import_module("01_probe_segment")
S2 = importlib.import_module("02_motion_profile")
S3 = importlib.import_module("03_keyframe_curation")
S4 = importlib.import_module("04_vlm_analyze")
S5 = importlib.import_module("05_codegen")
S6 = importlib.import_module("06_render_diff")

FIDELITY_THRESHOLD = 0.92
MAX_ITERS = 3

def reanimate(video: str, work_dir: str = "./reanimate_out",
              targets=("gsap", "css", "framer"), provider="gemini") -> dict:
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    seg = S1.run(video, work_dir)
    fps = seg["meta"]["fps"]

    profile = S2.run(video, fps, work_dir)

    keyframes = S3.run(video, f"{work_dir}/frames", f"{work_dir}/motion_profile.json",
                        work_dir, max_frames=20)

    spec = S4.run(f"{work_dir}/keyframes.json", f"{work_dir}/motion_profile.json",
                   work_dir, provider=provider)

    S5.run(f"{work_dir}/animation_spec.json", f"{work_dir}/motion_profile.json",
            f"{work_dir}/out", targets=targets)

    best_score, iters = 0.0, 0
    while iters < MAX_ITERS:
        # Render the generated CSS/JS to video and diff against the source.
        html_stub = build_preview_html(f"{work_dir}/out", targets)
        S6.record_html(html_stub, f"{work_dir}/rendered.webm", seg["meta"]["duration"], int(fps))
        report = S6.run(video, f"{work_dir}/rendered.webm", work_dir, int(fps))
        best_score = report["mean_ssim"]
        if best_score >= FIDELITY_THRESHOLD:
            break
        spec = patch_spec_from_diff(spec, report, S4)
        S5.run(f"{work_dir}/animation_spec.json", f"{work_dir}/motion_profile.json",
                f"{work_dir}/out", targets=targets)
        iters += 1

    summary = {"fidelity_score": best_score, "iterations": iters,
               "output_dir": f"{work_dir}/out", "scenes": len(spec.get("scenes", []))}
    Path(work_dir, "SUMMARY.json").write_text(json.dumps(summary, indent=2))
    return summary

def build_preview_html(out_dir: str, targets) -> str:
    css_link = f'<link rel="stylesheet" href="{out_dir}/animation.css">' if "css" in targets else ""
    gsap_script = (f'<script src="https://unpkg.com/gsap@3/dist/gsap.min.js"></script>'
                   f'<script src="{out_dir}/animation.gsap.js"></script>') if "gsap" in targets else ""
    html = f"<html><head>{css_link}</head><body>{gsap_script}</body></html>"
    p = f"{out_dir}/preview.html"
    Path(p).write_text(html)
    return p

def patch_spec_from_diff(spec: dict, fidelity_report: dict, S4_module) -> dict:
    """Sends only the weak-SSIM time windows back to the VLM for a
    targeted correction instead of re-analyzing the whole clip."""
    weak_frames = [i for i, s in enumerate(fidelity_report["per_frame_ssim"]) if s < 0.85]
    patch_request = {"current_spec": spec, "weak_frame_indices": weak_frames,
                      "instruction": "Only correct elements active during these frame "
                                     "indices; leave all other elements unchanged."}
    return S4_module.call_vlm(patch_request)

if __name__ == "__main__":
    result = reanimate(sys.argv[1])
    print(json.dumps(result, indent=2))
