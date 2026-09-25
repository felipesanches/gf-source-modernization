#!/usr/bin/env python3
"""Which (script, language, feature) runs which GSUB/GPOS lookups -- release vs build?

Question: Varela's GSUB rows survive the gate's lookup-order arbitration because
shaping differs under some languages. Is that a different SET of lookups registered
for a language system (FEA include_dflt inheritance, a feature registered for a
language the source excludes), rather than different lookup contents?

Lookups are identified by CONTENT, not index (the two compilers order them
differently): type + the rules they hold, glyphs keyed by codepoint when cmap'd and by
name otherwise; a contextual lookup is identified by its type and subtable count.
Each (script, lang, feature) is mapped to the sorted list of lookup identities it
runs, and the two fonts' maps are diffed.

Signal read: GSUB (or GPOS with --gpos) ScriptList -> LangSys -> FeatureIndex ->
Feature.LookupListIndex, plus each lookup's subtables.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 langsys_lookups.py \
        <release.ttf> <candidate.ttf> [--gpos]
"""
import hashlib
import sys

from fontTools.ttLib import TTFont


def lookup_ids(font, tag):
    cmap = font.getBestCmap()
    rev = {}
    for c, g in sorted(cmap.items()):
        rev.setdefault(g, c)

    def k(g):
        return "U+%04X" % rev[g] if g in rev else g
    out = []
    t = font[tag].table
    for i, lk in enumerate(t.LookupList.Lookup):
        rules = []
        for st in lk.SubTable:
            st = getattr(st, "ExtSubTable", st)
            for a, b in sorted((getattr(st, "mapping", None) or {}).items()):
                rules.append(("s", k(a), k(b)))
            for a, alts in sorted((getattr(st, "alternates", None) or {}).items()):
                rules.append(("a", k(a), tuple(k(x) for x in alts)))
            for a, ligs in sorted((getattr(st, "ligatures", None) or {}).items()):
                for lg in ligs:
                    rules.append(("l", k(a), tuple(k(x) for x in lg.Component), k(lg.LigGlyph)))
        if not rules:
            rules = [("subtables", len(lk.SubTable))]
        h = hashlib.sha1(repr(sorted(rules)).encode()).hexdigest()[:8]
        first = rules[0]
        out.append("T%d:%s:%d:%s" % (lk.LookupType, h, len(rules), first[1] if len(first) > 1 else ""))
    return out


def langsys_map(font, tag):
    ids = lookup_ids(font, tag)
    t = font[tag].table
    feats = t.FeatureList.FeatureRecord
    m = {}
    for sr in t.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys is not None:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        systems += [(lr.LangSysTag.strip(), lr.LangSys) for lr in sr.Script.LangSysRecord]
        for lang, ls in systems:
            for fi in ls.FeatureIndex:
                fr = feats[fi]
                key = (sr.ScriptTag, lang, fr.FeatureTag)
                m.setdefault(key, [])
                m[key] += [ids[i] for i in fr.Feature.LookupListIndex]
    return {k: sorted(v) for k, v in m.items()}


def main():
    a, b = sys.argv[1], sys.argv[2]
    tag = "GPOS" if "--gpos" in sys.argv else "GSUB"
    ma, mb = langsys_map(TTFont(a), tag), langsys_map(TTFont(b), tag)
    keys = sorted(set(ma) | set(mb))
    same = 0
    for key in keys:
        la, lb = ma.get(key), mb.get(key)
        if la == lb:
            same += 1
            continue
        if la is None:
            print("%-22s only in candidate: %s" % ("/".join(key), lb))
        elif lb is None:
            print("%-22s only in release  : %s" % ("/".join(key), la))
        else:
            print("%-22s release %s\n%-22s cand    %s" % ("/".join(key), la, "", lb))
            print("%-22s   release-only %s  cand-only %s" % (
                "", sorted(set(la) - set(lb)), sorted(set(lb) - set(la))))
    print("%s: %d (script, language, feature) keys, %d identical, %d differ"
          % (tag, len(keys), same, len(keys) - same))


if __name__ == "__main__":
    main()
