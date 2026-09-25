#!/usr/bin/env python3
"""Reference implementation of FontForge's shared GSUB/GPOS script list, and a
comparator for the layout tables of two fonts.

Question 1 (emulate): if a built font had its layout script lists shared the way
FontForge's OpenType exporter shares them, would its GSUB/GPOS equal the release's?
FontForge (lookups.c SFScriptsInLookups, identical in v20100501, v20110222 and master
67dd7dc9) collects the scripts of BOTH tables' lookups and writes that union into BOTH
tables; SFLangsInScript gives a script that has no lookups in a table one dummy
default LangSys with no features ("This is what VOLT does"); dumpg___info writes a
table that has scripts and no lookups ("to get around a bug in Uniscribe"). Languages
are NOT shared: each table keeps its own. This probe applies exactly that rule to a
compiled font -- it is the oracle the fontc prototype (Opts::share_script_lists) is
checked against, and the stand-in used before the prototype existed.

Question 2 (compare): are two fonts' GSUB/GPOS the same in the fields the table gate
reads (script -> language -> feature tags; feature tag -> lookup types; lookup
count), plus table version? Prints one line per table: SAME or the difference.

Run:
    PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
    $PY ff_shared_scripts.py emulate <built.ttf> <out.ttf>
    $PY ff_shared_scripts.py compare <release.ttf> <candidate.ttf>
"""
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot


def _empty_langsys():
    ls = ot.LangSys()
    ls.LookupOrder = None
    ls.ReqFeatureIndex = 0xFFFF
    ls.FeatureIndex = []
    ls.FeatureCount = 0
    return ls


def _empty_table(tag):
    t = getattr(ot, tag)()
    t.Version = 0x00010000
    t.ScriptList = ot.ScriptList()
    t.ScriptList.ScriptRecord = []
    t.ScriptList.ScriptCount = 0
    t.FeatureList = ot.FeatureList()
    t.FeatureList.FeatureRecord = []
    t.FeatureList.FeatureCount = 0
    t.LookupList = ot.LookupList()
    t.LookupList.Lookup = []
    t.LookupList.LookupCount = 0
    tab = newTable(tag)
    tab.table = t
    return tab


def share_scripts(font):
    """Apply FontForge's rule in place. -> list of what was added."""
    tables = [t for t in ("GSUB", "GPOS") if t in font]
    union = set()
    for tag in tables:
        sl = font[tag].table.ScriptList
        union |= {r.ScriptTag for r in (sl.ScriptRecord if sl else [])}
    added = []
    if not union:
        return added
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            font[tag] = _empty_table(tag)
            added.append("%s created" % tag)
        t = font[tag].table
        have = {r.ScriptTag for r in t.ScriptList.ScriptRecord}
        for script in sorted(union - have):
            r = ot.ScriptRecord()
            r.ScriptTag = script
            r.Script = ot.Script()
            r.Script.DefaultLangSys = _empty_langsys()
            r.Script.LangSysRecord = []
            r.Script.LangSysCount = 0
            t.ScriptList.ScriptRecord.append(r)
            added.append("%s += %s/dflt (empty)" % (tag, script))
        t.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
        t.ScriptList.ScriptCount = len(t.ScriptList.ScriptRecord)
    return added


def describe(font, tag):
    """A comparable summary of one layout table, or None when absent."""
    if tag not in font:
        return None
    t = font[tag].table
    feats = t.FeatureList.FeatureRecord if t.FeatureList else []
    lookups = t.LookupList.Lookup if t.LookupList else []
    scripts = []
    for r in (t.ScriptList.ScriptRecord if t.ScriptList else []):
        langs = []
        if r.Script.DefaultLangSys is not None:
            d = r.Script.DefaultLangSys
            langs.append(("dflt", d.ReqFeatureIndex,
                          tuple(sorted(feats[i].FeatureTag for i in d.FeatureIndex))))
        for lr in r.Script.LangSysRecord:
            langs.append((lr.LangSysTag, lr.LangSys.ReqFeatureIndex,
                          tuple(sorted(feats[i].FeatureTag for i in lr.LangSys.FeatureIndex))))
        scripts.append((r.ScriptTag, tuple(langs)))
    return {
        "version": hex(t.Version),
        "scripts": tuple(scripts),
        "features": tuple(sorted((f.FeatureTag, tuple(lookups[i].LookupType
                                                      for i in f.Feature.LookupListIndex))
                                 for f in feats)),
        "lookups": len(lookups),
    }


def main():
    mode = sys.argv[1]
    if mode == "emulate":
        src, out = sys.argv[2:4]
        f = TTFont(src)
        added = share_scripts(f)
        f.save(out)
        print("\n".join(added) or "nothing to add")
    elif mode == "compare":
        a, b = TTFont(sys.argv[2]), TTFont(sys.argv[3])
        rc = 0
        for tag in ("GSUB", "GPOS"):
            da, db = describe(a, tag), describe(b, tag)
            if da == db:
                print("%s SAME %s" % (tag, "absent" if da is None else
                                      "scripts=%s features=%d lookups=%d" % (
                                          [s[0] for s in da["scripts"]],
                                          len(da["features"]), da["lookups"])))
            else:
                rc = 1
                print("%s DIFFERS" % tag)
                for k in ("version", "scripts", "features", "lookups"):
                    va = None if da is None else da[k]
                    vb = None if db is None else db[k]
                    if va != vb:
                        print("  %s:\n    A=%s\n    B=%s" % (k, va, vb))
        sys.exit(rc)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
