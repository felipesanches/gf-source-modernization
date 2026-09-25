#!/usr/bin/env python3
"""What does diffenator3's RENDERING diff say about a harness build?

Question answered: tools/baseline.sh gates only diffenator3's `tables` and `cmap_diff`
sections (sfd-batch5/tools/table_gate.py); the per-glyph rendering comparison in
`locations[].glyphs` and `locations[].words` is not gated there (table_gate.py: "outlines
are gated by the rendering diff"). A build can therefore be table-CLEAN while glyphs draw
differently. For one harness run, how many glyphs and words differ in rendering, by how
many pixels at most, and in which Unicode blocks?

Usage:
  d3_render.py <scratch>/baseline/<Style>-<TAG>/d3.json [--list N]
Prints: glyph diffs, word diffs, max differing_pixels, and the glyph diffs per block
(Arabic U+0600-06FF/FB50-FEFF, Latin and symbols elsewhere), with the N worst.
"""
import json
import sys


def block(cp):
    if 0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFEFF or 0x0750 <= cp <= 0x077F:
        return "arabic"
    if cp < 0x0250 or 0x1E00 <= cp <= 0x1EFF or 0xFB00 <= cp <= 0xFB06:
        return "latin"
    return "other"


def main(path, n=10):
    d = json.load(open(path))
    glyphs, words, px = [], 0, 0
    for loc in d.get("locations") or []:
        for g in loc.get("glyphs") or []:
            glyphs.append(g)
            px = max(px, g.get("differing_pixels") or 0)
        w = loc.get("words") or {}
        for lst in (w.values() if isinstance(w, dict) else []):
            words += len(lst)
            for x in lst:
                px = max(px, x.get("differing_pixels") or 0)
    per = {}
    for g in glyphs:
        s = g.get("string") or ""
        cp = ord(s[0]) if s else -1
        per.setdefault(block(cp), []).append((g.get("differing_pixels") or 0, "U+%04X" % cp if cp >= 0 else "?"))
    print("glyph diffs %d, word diffs %d, max differing_pixels %d" % (len(glyphs), words, px))
    for k, v in sorted(per.items()):
        v.sort(reverse=True)
        print("  %-7s %4d glyphs; worst %s" % (k, len(v), v[:n]))


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--list") + 1]) if "--list" in sys.argv else 10
    main(sys.argv[1], n)
