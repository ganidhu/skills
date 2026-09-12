---
name: reverse-animate
description: >
  Ingests a screen recording or video clip of a UI/motion-graphics animation
  and reconstructs it as runnable GSAP, CSS, Framer Motion, or JSX plus a
  fidelity score. Use when the user asks to recreate this animation, rebuild
  this motion graphic, reverse engineer this UI animation, clone this
  animation 1:1, or extract easing/timing from a video.
license: MIT
metadata:
  version: "1.0.0"
  author: ganidhu
---

# reverse-animate

7-stage pipeline: stages 1–3 are deterministic signal processing (no model).
Stage 4 is the only VLM call, and it only sees curated keyframes plus numeric
timing. Stages 5–7 codegen, render-back, and iterate until SSIM ≥ 0.92 or 3
passes.

```
video.mp4
  → [1] probe & segment     segment_report.json
  → [2] motion profile      motion_profile.json (easing, loop, stagger)
  → [3] keyframe curation   keyframes.json + pngs (8–24 frames)
  → [4] VLM analysis        animation_spec.json
  → [5] codegen             out/{gsap,css,framer}
  → [6] render-back & diff  fidelity_report.json
  → [7] refine              patch spec, repeat 5→6
```

Scripts live in `scripts/` next to this file. Run them from there, or run
the orchestrator as the entrypoint.

## When to use

- User drops a screen recording / motion graphic and wants a 1:1 rebuild
- User wants easing, duration, stagger, or loop extracted from a clip
- Targets: GSAP, CSS keyframes, Framer Motion. Lottie is spec-only unless
  a Lottie-web render harness is added

## Setup

System: `ffmpeg`, `ffprobe`.

```bash
python3 -m pip install -r scripts/../requirements.txt
python3 -m playwright install chromium
```

Stage 4's `call_vlm()` is a stub. Wire it to Gemini, Claude vision, or a
local `qwen2.5-vl` via Ollama before the first real run. Force JSON output.

## How to run

Default: one entrypoint.

```bash
python3 scripts/07_orchestrator.py /path/to/clip.mp4
```

That writes `./reanimate_out/` (`SUMMARY.json`, `out/animation.gsap.js`,
`out/animation.css`, `out/animation.framer.jsx`).

To keep the main conversation small, run stages 1–3 in a subagent and only
bring `animation_spec.json` plus `motion_profile.json` back.

If the user only wants timing/easing, stop after stage 2. Do not call a VLM.

## Stage contract

| Stage | Script | Writes | Notes |
| --- | --- | --- | --- |
| 1 | `scripts/01_probe_segment.py` | `segment_report.json` | fps, duration, scene cuts, freezes |
| 2 | `scripts/02_motion_profile.py` | `motion_profile.json` | optical-flow energy → cubic-bezier; loop + stagger |
| 3 | `scripts/03_keyframe_curation.py` | `keyframes.json` | pHash dedupe, max 20 frames |
| 4 | `scripts/04_vlm_analyze.py` | `animation_spec.json` | visual structure only; do not re-guess timing |
| 5 | `scripts/05_codegen.py` | `out/*` | templates, not freeform |
| 6 | `scripts/06_render_diff.py` | `fidelity_report.json` | Playwright record + SSIM |
| 7 | `scripts/07_orchestrator.py` | `SUMMARY.json` | cap at 3 iters |

Stage 4 prompt rule: easing, loop, and stagger from stage 2 are ground
truth. If an element does not match, set `"easing": "unmatched"`.

## Done when

- `SUMMARY.json` exists with `fidelity_score` and `output_dir`
- Requested targets exist under `out/`
- Score ≥ 0.92, or 3 refinement iters completed and the remaining SSIM-weak
  windows are reported instead of guessed

## Limits

- Low-contrast / heavy grade: normalize contrast before stage 2
- Multi-segment eases (spring-then-settle) stay `"unmatched"` unless the
  curve is split at an inflection first
- Stage 6 only covers web-renderable targets (CSS / GSAP / Framer)
