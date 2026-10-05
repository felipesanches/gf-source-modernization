"""For each of the 42 styles: glyphs whose Fore layer has contours AND references
(mixed), and whether any reference there has a transform the OLD snap would have
changed (non-integer offset, or a scale/matrix entry within 1.5 F2Dot14 steps of an
integer but not equal to it). Also refs with matrix entries outside [-2, 1.999939]."""
import os, re, sys
sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
import recipe
STEP = 1.0 / 16384
def would_snap(m):
    a, b, c, d, e, f = m
    ch = []
    for v in (a, b, c, d):
        r = round(v)
        if v != r and abs(v - r) <= 1.5 * STEP:
            ch.append("scale %r->%d" % (v, r))
    for v in (e, f):
        if v != round(v):
            ch.append("offset %r" % v)
    return ch
def parse(text):
    glyphs = []
    cur = None
    layer = None
    for line in text.splitlines():
        if line.startswith("StartChar:"):
            cur = {"name": line.split(":", 1)[1].strip(), "layers": {}}
            layer = None
        elif cur is None:
            continue
        elif line.startswith("EndChar"):
            glyphs.append(cur); cur = None
        elif line in ("Fore", "Back") or line.startswith("Layer:"):
            layer = line
            cur["layers"].setdefault(layer, {"contours": 0, "refs": []})
        elif line.startswith("SplineSet") and layer:
            cur["layers"][layer]["contours"] += 1
        elif line.startswith("Refer:"):
            parts = line.split()
            # Refer: gid uni S|N a b c d e f ...
            m = [float(x) for x in parts[4:10]]
            L = layer or "Fore"
            cur["layers"].setdefault(L, {"contours": 0, "refs": []})["refs"].append(m)
    return glyphs
tot_mixed = tot_mixed_snap = tot_comp_snap = tot_out = 0
for row in recipe.rows():
    g = parse(recipe.source_text(row))
    mixed = mixed_snap = comp_snap = out_rng = 0
    ex = []
    for gl in g:
        for L, v in gl["layers"].items():
            if L == "Back" or not v["refs"]:
                continue
            ch = [c for m in v["refs"] for c in would_snap(m)]
            oor = any(not (-2 <= x <= 1.999939) for m in v["refs"] for x in m[:4])
            if v["contours"]:
                mixed += 1
                if ch:
                    mixed_snap += 1; ex.append("%s[%s mixed]: %s" % (gl["name"], L, ch[:3]))
            else:
                if oor:
                    out_rng += 1; ex.append("%s[%s out-of-range]" % (gl["name"], L))
                elif ch:
                    comp_snap += 1
    tot_mixed += mixed; tot_mixed_snap += mixed_snap; tot_comp_snap += comp_snap; tot_out += out_rng
    print("%-28s mixed=%d mixed_would_snap=%d composite_snapped=%d composite_out_of_range=%d %s" % (
        row["style"], mixed, mixed_snap, comp_snap, out_rng, "; ".join(ex[:4])))
print("TOTAL mixed=%d mixed_would_snap=%d composite_snapped=%d out_of_range=%d" % (tot_mixed, tot_mixed_snap, tot_comp_snap, tot_out))
