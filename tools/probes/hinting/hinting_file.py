#!/usr/bin/env python3
"""Prototype of the route (a) builder operation: a font's TrueType hinting as one text file in
the source repository, applied to the compiled font. Answers: does a separate hinting file,
applied after compiling, reproduce a release's hinting exactly (functional_gate `hinting`)?

  hinting_file.py extract <release.ttf> > <Font>.hinting.json
  hinting_file.py apply <Font>.hinting.json <built.ttf> <out.ttf>

File (formatVersion "1"; programs in fontTools/ufo2ft assembly, glyph ids as ufo2ft checks them):
  fpgm, prep         assembly text, or absent
  cvt                list of values
  gasp               {"<ppem>": <behavior bits as int>}
  maxp               maxZones, maxTwilightPoints, maxStorage, maxFunctionDefs,
                     maxInstructionDefs, maxStackElements, maxSizeOfInstructions
  head_flag_3        true/false (integer ppem)
  hdmx               {"<ppem>": {"<glyph>": width}}       (device metrics, when the release has them)
  LTSH               {"<glyph>": yPel}
  VDMX               {"version", "ratRanges": [...], "groups": [{"<yPelHeight>": [yMax, yMin]}]}
  glyphs             {"<glyph>": {"assembly": text, "id": HashPointPen hash of the glyph's points}}
  components         {"<composite glyph>": [flags of each component, masked to COMPONENT_FLAGS]}
                     (ROUND_XY_TO_GRID, USE_MY_METRICS, OVERLAP_COMPOUND, SCALED/UNSCALED_COMPONENT_OFFSET:
                     they change the hinted result, and a compiler sets its own)
apply refuses a glyph whose points do not hash to its id (the program would address other
points) and exits 1, naming them; it never applies a program to other points.
"""
import array
import json
import sys
from functools import partial

from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.pens.hashPointPen import HashPointPen
from fontTools.pens.roundingPen import RoundingPointPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram

COMPONENT_FLAGS = 0x0004 | 0x0200 | 0x0400 | 0x0800 | 0x1000
MAXP = ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
        "maxStackElements", "maxSizeOfInstructions")


def asm(program):
    return "\n".join(program.getAssembly())


def program(text):
    p = ttProgram.Program()
    p.fromAssembly(text.splitlines())
    return p


def glyph_id(tt, name):
    pen = HashPointPen(tt["hmtx"][name][0], tt.getGlyphSet())
    tt["glyf"][name].drawPoints(RoundingPointPen(pen, transformRoundFunc=partial(floatToFixedToFloat, precisionBits=14)),
                                tt["glyf"])
    return pen.hash


def extract(path):
    tt = TTFont(path)
    d = {"formatVersion": "1"}
    for tag in ("fpgm", "prep"):
        if tag in tt:
            d[tag] = asm(tt[tag].program)
    if "cvt " in tt:
        d["cvt"] = list(tt["cvt "].values)
    if "gasp" in tt:
        d["gasp"] = {str(k): v for k, v in sorted(tt["gasp"].gaspRange.items())}
    d["maxp"] = {k: getattr(tt["maxp"], k) for k in MAXP}
    d["head_flag_3"] = bool(tt["head"].flags & 8)
    if "hdmx" in tt:
        d["hdmx"] = {str(p): dict(w) for p, w in sorted(tt["hdmx"].hdmx.items())}
    if "LTSH" in tt:
        d["LTSH"] = dict(tt["LTSH"].yPels)
    if "VDMX" in tt:
        v = tt["VDMX"]
        d["VDMX"] = {"version": v.version, "ratRanges": [dict(r) for r in v.ratRanges],
                     "groups": [{str(k): list(x) for k, x in g.items()} for g in v.groups]}
    glyphs = {}
    for name in tt.getGlyphOrder():
        g = tt["glyf"][name]
        if hasattr(g, "program") and g.program.getBytecode():
            glyphs[name] = {"assembly": asm(g.program), "id": glyph_id(tt, name)}
    d["glyphs"] = glyphs
    d["components"] = {name: [c.flags & COMPONENT_FLAGS for c in tt["glyf"][name].components]
                       for name in tt.getGlyphOrder() if tt["glyf"][name].isComposite()}
    json.dump(d, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")


def apply(hpath, inp, out):
    d = json.load(open(hpath))
    assert d.get("formatVersion") == "1", "unknown formatVersion"
    tt = TTFont(inp)
    for tag in ("fpgm", "prep"):
        if tag in d:
            tt[tag] = newTable(tag)
            tt[tag].program = program(d[tag])
        elif tag in tt:
            del tt[tag]
    if "cvt" in d:
        tt["cvt "] = newTable("cvt ")
        tt["cvt "].values = array.array("h", d["cvt"])
    elif "cvt " in tt:
        del tt["cvt "]
    if "gasp" in d:
        tt["gasp"] = newTable("gasp")
        tt["gasp"].version = 1
        tt["gasp"].gaspRange = {int(k): v for k, v in d["gasp"].items()}
    bad = []
    glyf = tt["glyf"]
    for name in tt.getGlyphOrder():
        g = glyf[name]
        if name in d["glyphs"]:
            if glyph_id(tt, name) != d["glyphs"][name]["id"]:
                bad.append(name)
                continue
            g.program = program(d["glyphs"][name]["assembly"])
        elif hasattr(g, "program"):
            g.program = ttProgram.Program()
            g.program.fromBytecode(b"")
    for name, flags in d.get("components", {}).items():
        g = glyf[name] if name in glyf else None
        if g is None or not g.isComposite() or len(g.components) != len(flags):
            bad.append(name)
            continue
        for c, f in zip(g.components, flags):
            c.flags = (c.flags & ~COMPONENT_FLAGS) | f
    if bad:
        sys.exit("points or components differ from the hinting file, nothing applied to: %d glyph(s): %s"
                 % (len(bad), " ".join(bad[:20])))
    for k, v in d["maxp"].items():
        setattr(tt["maxp"], k, v)
    tt["head"].flags = (tt["head"].flags & ~8) | (8 if d["head_flag_3"] else 0)
    for tag in ("hdmx", "LTSH", "VDMX"):
        if tag in tt and tag not in d:
            del tt[tag]
    if "hdmx" in d:
        t = tt["hdmx"] = newTable("hdmx")
        t.hdmx = {int(p): w for p, w in d["hdmx"].items()}
    if "LTSH" in d:
        t = tt["LTSH"] = newTable("LTSH")
        t.version, t.yPels = 0, d["LTSH"]
    if "VDMX" in d:
        t = tt["VDMX"] = newTable("VDMX")
        t.version = d["VDMX"]["version"]
        t.ratRanges = d["VDMX"]["ratRanges"]
        t.groups = [{int(k): tuple(x) for k, x in g.items()} for g in d["VDMX"]["groups"]]
        t.numRecs, t.numRatios = len(t.groups), len(t.ratRanges)
    # maxp limits are stated, not recalculated: keep them as written
    tt.recalcBBoxes = True
    tt.save(out, reorderTables=True)
    t2 = TTFont(out)
    for k, v in d["maxp"].items():
        if getattr(t2["maxp"], k) != v:
            sys.exit("maxp.%s recalculated on save: %s, file says %s" % (k, getattr(t2["maxp"], k), v))


if __name__ == "__main__":
    if sys.argv[1:2] == ["extract"]:
        extract(sys.argv[2])
    elif sys.argv[1:2] == ["apply"]:
        apply(*sys.argv[2:5])
    else:
        sys.exit(__doc__)
