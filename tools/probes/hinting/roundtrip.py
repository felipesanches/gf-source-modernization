#!/usr/bin/env python3
"""Can a release's TrueType hinting live in a source and come back exactly through the Python
build? Route (a) step 3 (ROUTE-A.md), before any babelfont or fontc change.

For each release font: write a UFO whose glyphs keep the release's own points (fontTools
drawPoints: implied on-curves stay implied, contour starts and order kept, components kept)
and whose libs hold ufo2ft's `public.truetype.instructions` (formatVersion "1"):
  font lib   fontProgram, controlValueProgram (assembly), controlValue {index: value},
             maxFunctionDefs, maxInstructionDefs, maxStackElements, maxStorage, maxZones,
             maxTwilightPoints
  glyph lib  assembly, id (fontTools HashPointPen of the release glyph, as ufo2ft checks it)
plus gasp (openTypeGaspRangeRecords) and head flags (openTypeHeadFlags). Then:
  ufo     compile that UFO with ufo2ft (no cubic conversion, no direction reversal, implied
          on-curves kept, no production names) and run functional_gate's hinting check
          against the release;
  file    the same UFO without the instruction libs, compiled the same way, then the
          release's hinting file (hinting_file.py extract) applied with hinting_file.py apply.
Result 2026-11-05 (ROUTE-A.md): a .glyphs route is not possible -- glyphsLib drops every
public.* userData key and fontmake runs it in minimal mode, which skips layer userData.

Usage: roundtrip.py <scratch dir> <release.ttf>...
Prints, per font and route: the hinting check's status and its first failures.
"""
import os
import sys
from functools import partial

import ufoLib2
from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.pens.hashPointPen import HashPointPen
from fontTools.pens.roundingPen import RoundingPointPen
from fontTools.ttLib import TTFont
from ufo2ft import compileTTF

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import functional_gate as fg  # noqa: E402

KEY = "public.truetype.instructions"


def asm(program):
    return "\n".join(program.getAssembly())


def glyph_hash(tt, name):
    gs = tt.getGlyphSet()
    pen = HashPointPen(tt["hmtx"][name][0], gs)
    tt["glyf"][name].drawPoints(RoundingPointPen(pen, transformRoundFunc=partial(floatToFixedToFloat, precisionBits=14)),
                                tt["glyf"])
    return pen.hash


def to_ufo(path):
    tt = TTFont(path)
    ufo = ufoLib2.Font()
    head, hhea, os2 = tt["head"], tt["hhea"], tt["OS/2"]
    ufo.info.unitsPerEm = head.unitsPerEm
    ufo.info.ascender, ufo.info.descender = hhea.ascent, hhea.descent
    ufo.info.familyName, ufo.info.styleName = "Roundtrip", "Regular"
    ufo.info.openTypeHeadFlags = [b for b in range(16) if head.flags & (1 << b)]
    if "gasp" in tt:
        ufo.info.openTypeGaspRangeRecords = [
            {"rangeMaxPPEM": k, "rangeGaspBehavior": [b for b in range(4) if v & (1 << b)]}
            for k, v in sorted(tt["gasp"].gaspRange.items())]
    font = {"formatVersion": "1"}
    for key, tag in (("fontProgram", "fpgm"), ("controlValueProgram", "prep")):
        if tag in tt:
            font[key] = asm(tt[tag].program)
    if "cvt " in tt:
        font["controlValue"] = {str(i): v for i, v in enumerate(tt["cvt "].values)}
    for k in ("maxFunctionDefs", "maxInstructionDefs", "maxStackElements", "maxStorage",
              "maxZones", "maxTwilightPoints"):
        font[k] = getattr(tt["maxp"], k)
    ufo.lib[KEY] = font
    ufo.lib["public.glyphOrder"] = tt.getGlyphOrder()
    cmap = {}
    for u, n in tt.getBestCmap().items():
        cmap.setdefault(n, []).append(u)
    glyf = tt["glyf"]
    for name in tt.getGlyphOrder():
        g = ufo.newGlyph(name)
        g.width = tt["hmtx"][name][0]
        g.unicodes = cmap.get(name, [])
        glyf[name].drawPoints(g.getPointPen(), glyf)
        prog = getattr(glyf[name], "program", None)
        code = asm(prog) if prog is not None and prog.getBytecode() else ""
        if code or glyf[name].numberOfContours:
            g.lib[KEY] = {"formatVersion": "1", "assembly": code, "id": glyph_hash(tt, name)}
    return ufo


def build(ufo, out):
    otf = compileTTF(ufo, convertCubics=False, reverseDirection=False, dropImpliedOnCurves=False,
                     useProductionNames=False, removeOverlaps=False)
    otf.save(out)
    return out


def check(release, built):
    A, B = fg.Font(release), fg.Font(built)
    _, _, ka, kb = fg.correspondence(A, B)
    c = fg.check_hinting(A, B, ka, kb, 3)
    return c["status"], c["failures"] or c["notes"]


def strip_libs(ufo):
    ufo.lib.pop(KEY, None)
    for g in ufo:
        g.lib.pop(KEY, None)
    return ufo


def main():
    import subprocess
    scratch = sys.argv[1]
    os.makedirs(scratch, exist_ok=True)
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hinting_file.py")
    for path in sys.argv[2:]:
        stem = os.path.splitext(os.path.basename(path))[0]
        ufo = to_ufo(path)
        st, why = check(path, build(ufo, os.path.join(scratch, stem + ".ufo-route.ttf")))
        print("%-28s ufo   %s  %s" % (stem, st, " | ".join(w[:100] for w in why[:2])), flush=True)
        hfile = os.path.join(scratch, stem + ".hinting.json")
        with open(hfile, "w") as fh:
            subprocess.run([sys.executable, tool, "extract", path], stdout=fh, check=True)
        plain = build(strip_libs(ufo), os.path.join(scratch, stem + ".plain.ttf"))
        out = os.path.join(scratch, stem + ".file-route.ttf")
        r = subprocess.run([sys.executable, tool, "apply", hfile, plain, out], capture_output=True, text=True)
        if r.returncode:
            print("%-28s file  APPLY-REFUSED  %s" % (stem, r.stderr.strip()[-200:]), flush=True)
            continue
        st, why = check(path, out)
        print("%-28s file  %s  %s" % (stem, st, " | ".join(w[:100] for w in why[:2])), flush=True)


main()
