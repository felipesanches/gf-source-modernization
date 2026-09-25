#!/usr/bin/env python3
"""What would a kern lookup with FontForge's flags change? (a SIMULATION, not a build)

Question answered: FontForge exported each `kern` lookup with the flags its .sfd
states (`Lookup: 258 0 0 ...` = flag 0: no mark is skipped, so a combining mark
between two letters blocks the pair). babelfont turns FontForge kerning into Glyphs
kerning, and fontc 1.0.0's kern writer always sets IgnoreMarks (or, when some marks
advance, UseMarkFilteringSet over those marks); fontir 1.0.0 feature_writers.rs refuses
the ufo2ft option that would turn this off ("KernFeatureWriter ignoreMarks=false" is a
hard error), although fontbe's KernSplitOptions already has the ignore_marks=false
path (kern.rs make_lookups). If fontc honoured it, the built kern lookups would carry
flag 0 and no mark filtering set.

This rewrites a BUILT font's `kern`-feature lookups that fontc's kern writer made
(those carrying IgnoreMarks 0x8 or UseMarkFilteringSet 0x10; a lookup babelfont wrote
as FEA from the .sfd keeps its own flags) to clear those two bits, with no
MarkFilteringSet (dropping GDEF MarkGlyphSetsDef when nothing else uses it) and saves
the result, so probes/shaping_compare.py and the gate can measure the effect. The
output is evidence for the proposal only; it is never a landing candidate.

Usage:
  simulate_kern_flag0.py <built.ttf> <out.ttf>
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import sys

from fontTools.ttLib import TTFont


def main():
    src, dst = sys.argv[1], sys.argv[2]
    f = TTFont(src)
    gpos = f["GPOS"].table
    kern = set()
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "kern":
            kern.update(fr.Feature.LookupListIndex)
    changed = []
    for i in sorted(kern):
        lk = gpos.LookupList.Lookup[i]
        if lk.LookupFlag & 0x18:
            changed.append((i, lk.LookupFlag))
            lk.LookupFlag &= ~0x18
            if hasattr(lk, "MarkFilteringSet"):
                del lk.MarkFilteringSet
    users = [lk for tag in ("GSUB", "GPOS") if tag in f
             for lk in f[tag].table.LookupList.Lookup if lk.LookupFlag & 0x10]
    gdef = f["GDEF"].table
    if not users and getattr(gdef, "MarkGlyphSetsDef", None) is not None:
        gdef.MarkGlyphSetsDef = None
        gdef.Version = 0x00010000 if getattr(gdef, "VarStore", None) is None else gdef.Version
    f.save(dst)
    print("kern lookups rewritten to flag 0: %s" % changed)


if __name__ == "__main__":
    main()
