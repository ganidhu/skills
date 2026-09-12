"""05_codegen.py"""
import json
from pathlib import Path
from string import Template

GSAP_TEMPLATE = Template("""
gsap.timeline()
$tweens
""")

GSAP_TWEEN = Template(
'''  .fromTo("$selector",
    { x: $x0, y: $y0, opacity: $o0, scale: $s0, rotate: $r0 },
    { x: $x1, y: $y1, opacity: $o1, scale: $s1, rotate: $r1,
      duration: $dur, delay: $delay, ease: "$ease"$repeat }
  )''')

CSS_KEYFRAMES_TEMPLATE = Template("""
@keyframes $name {
  from { transform: translate($x0px, $y0px) scale($s0) rotate($r0deg); opacity: $o0; }
  to   { transform: translate($x1px, $y1px) scale($s1) rotate($r1deg); opacity: $o1; }
}
.$name {
  animation: $name $dur s $easing $delay s $iter forwards;
}
""")

FRAMER_MOTION_TEMPLATE = Template(
'''<motion.$tag
  initial={{ x: $x0, y: $y0, opacity: $o0, scale: $s0, rotate: $r0 }}
  animate={{ x: $x1, y: $y1, opacity: $o1, scale: $s1, rotate: $r1 }}
  transition={{ duration: $dur, delay: $delay, ease: [$bezier] }}
>''')

def cssify_bezier(easing_name: str, bezier: list) -> str:
    named = {"linear": "linear", "ease-in-out": "ease-in-out",
             "ease-in": "ease-in", "ease-out": "ease-out"}
    return named.get(easing_name, f"cubic-bezier({','.join(map(str, bezier))})")

def emit_gsap(spec: dict) -> str:
    tweens = []
    for scene in spec["scenes"]:
        for el in scene["elements"]:
            i, f = el["initial_state"], el["final_state"]
            repeat = ", repeat: -1" if el.get("loop") else ""
            tweens.append(GSAP_TWEEN.substitute(
                selector=f".{el['name']}", x0=i.get("x", 0), y0=i.get("y", 0),
                o0=i.get("opacity", 1), s0=i.get("scale", 1), r0=i.get("rotate", 0),
                x1=f.get("x", 0), y1=f.get("y", 0), o1=f.get("opacity", 1),
                s1=f.get("scale", 1), r1=f.get("rotate", 0),
                dur=el.get("duration_seconds", 0.5), delay=el.get("delay_seconds", 0),
                ease=el.get("easing", "power2.out"), repeat=repeat))
    return GSAP_TEMPLATE.substitute(tweens="\n".join(tweens))

def emit_css(spec: dict, bezier: list) -> str:
    out = []
    for scene in spec["scenes"]:
        for el in scene["elements"]:
            i, f = el["initial_state"], el["final_state"]
            iter_ = "infinite" if el.get("loop") else "1"
            out.append(CSS_KEYFRAMES_TEMPLATE.substitute(
                name=el["name"], x0=i.get("x", 0), y0=i.get("y", 0),
                s0=i.get("scale", 1), r0=i.get("rotate", 0), o0=i.get("opacity", 1),
                x1=f.get("x", 0), y1=f.get("y", 0), s1=f.get("scale", 1),
                r1=f.get("rotate", 0), o1=f.get("opacity", 1),
                dur=el.get("duration_seconds", 0.5),
                easing=cssify_bezier(el.get("easing", ""), bezier),
                delay=el.get("delay_seconds", 0), iter=iter_))
    return "\n".join(out)

def emit_framer(spec: dict, bezier: list) -> str:
    blocks = []
    for scene in spec["scenes"]:
        for el in scene["elements"]:
            i, f = el["initial_state"], el["final_state"]
            blocks.append(FRAMER_MOTION_TEMPLATE.substitute(
                tag="div", x0=i.get("x", 0), y0=i.get("y", 0), o0=i.get("opacity", 1),
                s0=i.get("scale", 1), r0=i.get("rotate", 0), x1=f.get("x", 0),
                y1=f.get("y", 0), o1=f.get("opacity", 1), s1=f.get("scale", 1),
                r1=f.get("rotate", 0), dur=el.get("duration_seconds", 0.5),
                delay=el.get("delay_seconds", 0), bezier=",".join(map(str, bezier))))
    return "\n".join(blocks)

def run(animation_spec_json: str, motion_profile_json: str, out_dir: str,
        targets=("gsap", "css", "framer")):
    spec = json.loads(Path(animation_spec_json).read_text())
    profile = json.loads(Path(motion_profile_json).read_text())
    bezier = profile["easing"]["cubic_bezier"]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if "gsap" in targets:
        Path(out_dir, "animation.gsap.js").write_text(emit_gsap(spec))
    if "css" in targets:
        Path(out_dir, "animation.css").write_text(emit_css(spec, bezier))
    if "framer" in targets:
        Path(out_dir, "animation.framer.jsx").write_text(emit_framer(spec, bezier))
