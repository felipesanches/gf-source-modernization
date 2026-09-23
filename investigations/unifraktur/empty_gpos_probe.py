#!/usr/bin/env python3
"""Is the release's empty GPOS the WHOLE of the shaping difference, and what closes it?

FontForge's exporter shares one script list between GSUB and GPOS (SFScriptsInLookups
in lookups.c ignores its gpos argument and collects scripts from both lookup sets;
dumpg___info in tottfgpos.c then writes a table that has scripts and no lookups --
"to get around a bug in Uniscribe"). So a source whose lookups are all GSUB exports a
GPOS carrying the GSUB's scripts, zero features, zero lookups. fontc emits no GPOS.

This probe grafts a GPOS of exactly that shape (script records built from OUR OWN
GSUB's script list, each with an empty default LangSys; empty FeatureList and
LookupList) onto a built font, writes the result next to it, and shapes
  release vs built            and   release vs built+shared-scripts GPOS
with sfd-batch5's sweep.py (HarfBuzz output compared by glyph NAME, across 4
directions x 4 buffer-flag sets x 3 kern settings). It builds nothing.

    <venv python3> empty_gpos_probe.py <release.ttf> <built.ttf> <out.ttf>
"""
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot

SWEEP = '/home/fsanches/compartilhado/sfd-batch5/tools/probes/gdef_mark_vs_base/sweep.py'


def shared_script_gpos(font):
    """A GPOS with the GSUB's scripts and languages, no features, no lookups."""
    gsub = font['GSUB'].table
    t = ot.GPOS()
    t.Version = 0x00010000
    t.ScriptList = ot.ScriptList()
    t.ScriptList.ScriptRecord = []
    for rec in gsub.ScriptList.ScriptRecord:
        r = ot.ScriptRecord()
        r.ScriptTag = rec.ScriptTag
        r.Script = ot.Script()

        def empty_langsys():
            ls = ot.LangSys()
            ls.LookupOrder = None
            ls.ReqFeatureIndex = 0xFFFF
            ls.FeatureIndex = []
            ls.FeatureCount = 0
            return ls
        r.Script.DefaultLangSys = empty_langsys() if rec.Script.DefaultLangSys else None
        r.Script.LangSysRecord = []
        for lr in rec.Script.LangSysRecord:
            n = ot.LangSysRecord()
            n.LangSysTag = lr.LangSysTag
            n.LangSys = empty_langsys()
            r.Script.LangSysRecord.append(n)
        r.Script.LangSysCount = len(r.Script.LangSysRecord)
        t.ScriptList.ScriptRecord.append(r)
    t.ScriptList.ScriptCount = len(t.ScriptList.ScriptRecord)
    t.FeatureList = ot.FeatureList()
    t.FeatureList.FeatureRecord = []
    t.FeatureList.FeatureCount = 0
    t.LookupList = ot.LookupList()
    t.LookupList.Lookup = []
    t.LookupList.LookupCount = 0
    tab = newTable('GPOS')
    tab.table = t
    return tab


def sweep(a, b):
    """'N runs, M differ' plus the differing runs split by direction and case label."""
    import collections
    import importlib.util
    spec = importlib.util.spec_from_file_location('sweep', SWEEP)
    sw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sw)
    total, diffs = sw.compare(a, b)
    by = collections.Counter((d[2], d[0]) for d in diffs)
    lines = ['%d runs, %d differ' % (total, len(diffs))]
    for dirn in sw.DIRECTIONS:
        parts = ['%s=%d' % (lab, n) for (dd, lab), n in sorted(by.items()) if dd == dirn]
        lines.append('    %-3s %5d  %s' % (dirn, sum(n for (dd, _), n in by.items()
                                                  if dd == dirn), ' '.join(parts)))
    return '\n'.join(lines)


def main():
    release, built, out = sys.argv[1:4]
    f = TTFont(built)
    if 'GPOS' in f:
        raise SystemExit('built font already has a GPOS')
    f['GPOS'] = shared_script_gpos(f)
    f.save(out)
    rel = TTFont(release)['GPOS'].table
    new = TTFont(out)['GPOS'].table
    print('release GPOS scripts %s, features %d, lookups %d'
          % ([s.ScriptTag for s in rel.ScriptList.ScriptRecord],
             rel.FeatureList.FeatureCount, rel.LookupList.LookupCount))
    print('grafted GPOS scripts %s, features %d, lookups %d'
          % ([s.ScriptTag for s in new.ScriptList.ScriptRecord],
             new.FeatureList.FeatureCount, new.LookupList.LookupCount))
    print('release vs built                 :', sweep(release, built))
    print('release vs built + shared GPOS   :', sweep(release, out))
    # Control: also take the release's GDEF glyph classes, to show what the rest is.
    g = TTFont(out)
    g['GDEF'].table.GlyphClassDef.classDefs = dict(
        TTFont(release)['GDEF'].table.GlyphClassDef.classDefs)
    ctl = out.replace('.ttf', '+releaseGDEF.ttf')
    g.save(ctl)
    print('release vs built + GPOS + release GDEF classes (control only):',
          sweep(release, ctl))


if __name__ == '__main__':
    main()
