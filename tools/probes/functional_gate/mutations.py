#!/usr/bin/env python3
"""Question answered: does each check of tools/functional_gate.py fail on the defect it is
there to catch, and only that check?

Takes one release (default Salsa-Regular, which has GDEF, GPOS kerning, marks classed as
bases and unencoded glyphs), writes one mutated copy per defect class with fontTools, and
gates release vs copy. Expected: the unmutated copy passes all eight checks; each mutation
fails the check(s) listed in EXPECT (a mutation that changes behaviour in several ways fails
several checks, e.g. an advance change also moves shaped glyphs).

The hinting check's instructed-release rules need an instructed release: the HINTED
mutations run on Actor-Regular (169 glyph programs, its own fpgm, prep, cvt and gasp).

Usage: $PY tools/probes/functional_gate/mutations.py [release.ttf [hinted-release.ttf]] > tools/probes/functional_gate/MUTATIONS.txt
Scratch: $FG_SCRATCH/mutations/ (regenerable).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import functional_gate  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

REL = sys.argv[1] if len(sys.argv) > 1 else "/home/fsanches/compartilhado/google/fonts/ofl/salsa/Salsa-Regular.ttf"
HINTED_REL = sys.argv[2] if len(sys.argv) > 2 else "/home/fsanches/compartilhado/google/fonts/ofl/actor/Actor-Regular.ttf"
OUT = os.path.join(functional_gate.SCRATCH, "mutations")


def kern_value(tt):
    """Halve the first non-zero PairPos format-1 x-advance (a kerning pair)."""
    for lk in tt["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            st = getattr(st, "ExtSubTable", st)
            for ps in getattr(st, "PairSet", None) or []:
                for rec in ps.PairValueRecord:
                    v = rec.Value1
                    if v is not None and getattr(v, "XAdvance", 0):
                        v.XAdvance = v.XAdvance // 2 - 7
                        return
            for c1 in getattr(st, "Class1Record", None) or []:
                for c2 in c1.Class2Record:
                    v = c2.Value1
                    if v is not None and getattr(v, "XAdvance", 0):
                        v.XAdvance = v.XAdvance // 2 - 7
                        return
    raise SystemExit("no kerning value found")


def advance(tt):
    w, l = tt["hmtx"]["a"]
    tt["hmtx"]["a"] = (w + 12, l)


def psname(tt):
    for r in tt["name"].names:
        if r.nameID == 6:
            r.string = r.toUnicode() + "X"


def typo_bit(tt):
    tt["OS/2"].fsSelection |= 0x80
    tt["OS/2"].sTypoLineGap += 150


def no_gdef(tt):
    del tt["GDEF"]


def unencoded_outline(tt):
    cmapped = set(tt.getBestCmap().values())
    for n in tt.getGlyphOrder():
        g = tt["glyf"][n]
        if n not in cmapped and n != ".notdef" and g.numberOfContours > 0:
            g.coordinates[0] = (g.coordinates[0][0] + 60, g.coordinates[0][1] + 60)
            g.recalcBounds(tt["glyf"])
            return n
    raise SystemExit("no unencoded outline glyph")


def remap(tt):
    for st in tt["cmap"].tables:
        if 0x41 in st.cmap:
            st.cmap[0x41] = st.cmap[0x42]


def weight(tt):
    tt["OS/2"].usWeightClass += 100


def gasp_changed(tt):
    tt["gasp"].gaspRange = {0xFFFF: 10}


def prep_removed(tt):
    del tt["prep"]


def gasp_fontspector(tt):
    # Actor's release gasp is 8:2,16:1,65535:3; fontspector's is accepted in its place
    tt["gasp"].gaspRange = {0xFFFF: 0x0F}


def head_flag3_cleared(tt):
    # the release (Actor) sets it; a build may add it, never drop it
    tt["head"].flags &= ~8


def prep_smart_dropout_appended(tt):
    # the smart_dropout setup is accepted only in place of no prep, never added to one
    from fontTools.ttLib.tables import ttProgram
    p = ttProgram.Program()
    p.fromBytecode(tt["prep"].program.getBytecode() + bytes([0xB8, 0x01, 0xFF, 0x85, 0xB0, 0x04, 0x8D]))
    tt["prep"].program = p


MUTATIONS = [("identity", lambda tt: None, set()),
             ("kerning value halved", kern_value, {"shaping"}),
             ("advance of 'a' +12", advance, {"shaping", "advances", "rendering"}),
             ("name ID 6 changed", psname, {"names"}),
             ("USE_TYPO_METRICS set, typo gap +150", typo_bit, {"line_spacing"}),
             ("GDEF removed", no_gdef, {"gdef", "shaping"}),
             ("unencoded glyph outline moved", unencoded_outline, {"rendering"}),
             ("U+0041 mapped to B's glyph", remap, {"cmap", "shaping", "rendering"}),
             ("usWeightClass +100", weight, {"names"}),
             ("gasp 65535:15 -> 65535:10", gasp_changed, {"hinting"}),
             ("prep removed", prep_removed, {"hinting"})]


def first_program(tt):
    """The first glyph, in glyph order, that carries a program."""
    for n in tt.getGlyphOrder():
        g = tt["glyf"][n]
        if getattr(g, "program", None) is not None and len(g.program.getBytecode()):
            return n


def program_removed(tt):
    from fontTools.ttLib.tables import ttProgram
    n = first_program(tt)
    prog = ttProgram.Program()
    prog.fromBytecode(b"")
    tt["glyf"][n].program = prog
    return n


def cvt_changed(tt):
    tt["cvt "].values[0] += 20
    return "cvt[0] %d" % tt["cvt "].values[0]


def points_rotated(tt):
    """The first instructed simple glyph's first contour, started one point later: the same
    outline, so only a program addressing points by index can tell."""
    import array
    for n in tt.getGlyphOrder():
        g = tt["glyf"][n]
        if (not g.isComposite() and g.numberOfContours and getattr(g, "program", None) is not None
                and len(g.program.getBytecode())):
            end = g.endPtsOfContours[0]
            pts = list(g.coordinates[:end + 1])
            flags = list(g.flags[:end + 1])
            g.coordinates[:end + 1] = pts[1:] + pts[:1]
            g.flags = array.array("B", flags[1:] + flags[:1] + list(g.flags[end + 1:]))
            return n


HINTED_MUTATIONS = [("hinted identity", lambda tt: None, set()),
                    ("glyph program removed", program_removed, {"hinting"}),
                    ("cvt[0] +20", cvt_changed, {"hinting"}),
                    ("contour start rotated", points_rotated, {"hinting"}),
                    ("gasp -> fontspector's 65535:15", gasp_fontspector, set()),
                    ("smart_dropout appended to prep", prep_smart_dropout_appended, {"hinting"}),
                    ("head flag 3 cleared", head_flag3_cleared, {"hinting"})]


def main():
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    runs = [(REL, m) for m in MUTATIONS] + [(HINTED_REL, m) for m in HINTED_MUTATIONS]
    for i, (rel, (label, fn, expect)) in enumerate(runs):
        tt = TTFont(rel)
        what = fn(tt)
        path = os.path.join(OUT, "%02d-%s.ttf" % (i, label.split()[0].replace("'", "")))
        tt.save(path)
        res = functional_gate.run(rel, path, label)
        failed = set(functional_gate.failed_checks(res))
        ok = failed == expect
        bad += not ok
        print("%-5s %-38s expected fail %-40s got %s%s" % ("OK" if ok else "WRONG", label,
                                                          ",".join(sorted(expect)) or "-",
                                                          ",".join(sorted(failed)) or "-",
                                                          " (%s)" % what if what else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
