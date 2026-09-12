"""04_vlm_analyze.py"""
import json, base64
from pathlib import Path

ANIMATION_SPEC_SCHEMA = {
  "type": "object",
  "required": ["scenes"],
  "properties": {
    "scenes": {"type": "array", "items": {
      "type": "object",
      "required": ["elements", "start_time", "end_time"],
      "properties": {
        "start_time": {"type": "number"}, "end_time": {"type": "number"},
        "background": {"type": "string"},
        "elements": {"type": "array", "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "type": {"enum": ["text", "shape", "image", "icon", "container"]},
            "initial_state": {"type": "object",
              "properties": {"x": {}, "y": {}, "opacity": {}, "scale": {}, "rotate": {}}},
            "final_state": {"type": "object",
              "properties": {"x": {}, "y": {}, "opacity": {}, "scale": {}, "rotate": {}}},
            "duration_seconds": {"type": "number"},
            "delay_seconds": {"type": "number"},
            "easing": {"type": "string"},
            "loop": {"type": "boolean"},
          }
        }}
      }
    }}
  }
}

SYSTEM_PROMPT = """You are a motion-graphics forensics engine. You will be
given: (1) a sequence of timestamped keyframes from a screen recording, and
(2) precomputed numeric motion data (velocity-derived easing curve as a
cubic-bezier, detected loop period, detected stagger interval). Do NOT
re-estimate timing or easing yourself — those numbers are ground truth from
optical-flow analysis. Your job is purely visual: identify every distinct
animating element across the frames, its role (text/shape/image/icon/
container), its start and end transform state (position, opacity, scale,
rotation), and which of the provided easing/loop/stagger values applies to
it. Return ONLY JSON matching the provided schema. If an element's motion
doesn't match any provided easing value, say so under "easing":"unmatched"
rather than inventing one."""

def build_request(keyframes: list[dict], motion_profile: dict) -> dict:
    images_b64 = []
    for kf in keyframes:
        with open(kf["path"], "rb") as f:
            images_b64.append({
                "timestamp": kf["frame_index"],
                "data": base64.b64encode(f.read()).decode()
            })
    return {
        "system": SYSTEM_PROMPT,
        "schema": ANIMATION_SPEC_SCHEMA,
        "numeric_context": {
            "easing_candidates": [motion_profile["easing"]],
            "loop": motion_profile["loop"],
            "stagger_candidates": motion_profile["stagger_candidates"],
        },
        "images": images_b64,
    }

def call_vlm(request: dict, provider: str = "gemini") -> dict:
    """Stub — swap in your actual client (Gemini/Claude/local Qwen2.5-VL).
    Must be called with response_format=json / tool-forced JSON output."""
    raise NotImplementedError(
        "Wire this to your VLM client of choice: "
        "google-genai (Gemini 3), anthropic (Claude vision), "
        "or an Ollama-served qwen2.5-vl:72b for a fully local run."
    )

def validate_and_repair(spec: dict, schema: dict, call_vlm_fn) -> dict:
    """One repair pass if the model returns malformed/incomplete JSON."""
    import jsonschema
    try:
        jsonschema.validate(spec, schema)
        return spec
    except jsonschema.ValidationError as e:
        repair_req = {"broken_json": spec, "error": str(e), "schema": schema}
        return call_vlm_fn(repair_req)

def run(keyframes_json: str, motion_profile_json: str, out_dir: str, provider="gemini"):
    keyframes = json.loads(Path(keyframes_json).read_text())
    profile = json.loads(Path(motion_profile_json).read_text())
    req = build_request(keyframes, profile)
    spec = call_vlm(req, provider)
    spec = validate_and_repair(spec, ANIMATION_SPEC_SCHEMA, lambda r: call_vlm(r, provider))
    Path(out_dir, "animation_spec.json").write_text(json.dumps(spec, indent=2))
    return spec
