#!/usr/bin/env python3
"""Question answered: does each check of tools/functional_gate.py fail on the defect it is
there to catch, and only that check?

Takes one release (default Salsa-Regular, which has GDEF, GPOS kerning, marks classed as
bases and unencoded glyphs), writes one mutated copy per defect class with fontTools, and
gates release vs copy. Expected: the unmutated copy passes all seven checks; each mutation
fails the check(s) listed in EXPECT (a mutation that changes behaviour in several ways fails
several checks, e.g. an advance change also moves shaped glyphs).

Usage: $PY tools/probes/functional_gate/mutations.py [release.ttf] > tools/probes/functional_gate/MUTATIONS.txt
Scratch: $FG_SCRATCH/mutations/ (regenerable).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import functional_gate  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

REL = sys.argv[1] if len(sys.argv) > 1 else "/home/fsanches/compartilhado/google/fonts/ofl/salsa/Salsa-Regular.ttf"
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


MUTATIONS = [("identity", lambda tt: None, set()),
             ("kerning value halved", kern_value, {"shaping"}),
             ("advance of 'a' +12", advance, {"shaping", "advances", "rendering"}),
             ("name ID 6 changed", psname, {"names"}),
             ("USE_TYPO_METRICS set, typo gap +150", typo_bit, {"line_spacing"}),
             ("GDEF removed", no_gdef, {"gdef", "shaping"}),
             ("unencoded glyph outline moved", unencoded_outline, {"rendering"}),
             ("U+0041 mapped to B's glyph", remap, {"cmap", "shaping", "rendering"}),
             ("usWeightClass +100", weight, {"names"})]


def main():
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for label, fn, expect in MUTATIONS:
        tt = TTFont(REL)
        what = fn(tt)
        path = os.path.join(OUT, label.split()[0].replace("'", "") + ".ttf")
        tt.save(path)
        res = functional_gate.run(REL, path, label)
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
