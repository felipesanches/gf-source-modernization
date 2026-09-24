#!/usr/bin/env python3
"""Question answered: for every families.tsv style whose .sfd stores its win/hhea
metrics in offset mode (OS2WinAOffset/OS2WinDOffset/HheadAOffset/HheadDOffset = 1),
does babelfont #85 (496e904: base = ceil(ymax)/floor(ymin) instead of round()) change
the resolved metric at all? It can only when the font's exact y-extrema are fractional
with ceil(ymax) != round(ymax) or floor(ymin) != round(ymin).

Signal: exact (curve-extrema) y-bounds over every glyph's master layer, components
decomposed with their transforms (fontTools BoundsPen, the analogue of the kurbo
BezPath::bounding_box babelfont's compute_font_bbox_y uses), measured on the .glyphs
the candidate writes from the UNMODIFIED .sfd (recipe flags). Cross-checked against the
shipped font's head.yMin/yMax (FontForge's floor/ceil of its own bbox).

Usage: bbox_offset_styles.py <babelfont> <workdir>
"""
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/sfd-reland/tools")
import recipe  # noqa: E402
import glyphsLib  # noqa: E402
from fontTools.pens.boundsPen import BoundsPen  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

KEYS = ("OS2WinAOffset", "OS2WinDOffset", "HheadAOffset", "HheadDOffset")


class GlyphSet(dict):
    pass


def main():
    binary, work = sys.argv[1], sys.argv[2]
    os.makedirs(work, exist_ok=True)
    print("%-28s %12s %12s  %-22s %-22s  %s" % ("style", "ymin", "ymax", "floor/round(ymin)",
                                                "ceil/round(ymax)", "shipped head yMin/yMax"))
    for row in recipe.rows():
        text = recipe.source_text(row)
        if not any(re.search(r"^%s: 1$" % k, text, re.M) for k in KEYS):
            continue
        src = os.path.join(work, row["style"] + ".sfd")
        open(src, "w", encoding="utf-8", errors="replace").write(text)
        out = os.path.join(work, row["style"] + ".glyphs")
        flags = recipe.flags_for(open(src, encoding="utf-8", errors="replace").read(), row["shipped"])
        subprocess.run([binary, src, out] + flags, check=True, capture_output=True)
        font = glyphsLib.GSFont(out)
        mid = font.masters[0].id
        gs = GlyphSet()
        for g in font.glyphs:
            layer = g.layers[mid]
            if layer is not None:
                gs[g.name] = layer
        ymin, ymax = math.inf, -math.inf
        for name, layer in gs.items():
            pen = BoundsPen(gs)
            layer.draw(pen)
            if pen.bounds:
                ymin, ymax = min(ymin, pen.bounds[1]), max(ymax, pen.bounds[3])
        head = TTFont(row["shipped"])["head"]
        f_ymin, r_ymin = math.floor(ymin), round(ymin)
        c_ymax, r_ymax = math.ceil(ymax), round(ymax)
        print("%-28s %12.4f %12.4f  %-22s %-22s  %d/%d" % (
            row["style"], ymin, ymax,
            "%d/%d %s" % (f_ymin, r_ymin, "same" if f_ymin == r_ymin else "DIFFER"),
            "%d/%d %s" % (c_ymax, r_ymax, "same" if c_ymax == r_ymax else "DIFFER"),
            head.yMin, head.yMax))


if __name__ == "__main__":
    main()
