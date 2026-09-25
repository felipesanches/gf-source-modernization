#!/usr/bin/env python3
"""Independent check: which (script, language, feature) keys apply different GSUB effects?

Question: next-emptygpos claims Varela's GSUB rows come from babelfont registering
FontForge's per-language lookups with FEA's default include_dflt (so latn AZE/CRT/TRK
inherit liga lookup 24 and smcp lookup 21) plus aalt being registered under latn/SRB.
This probe re-derives the difference WITHOUT the other agent's langsys_lookups.py:
for every (script, language, feature) key present in either font it collects the
set of lookup EFFECT signatures reachable from that key and compares the two fonts.

Signal read: GSUB ScriptList/FeatureList/LookupList via fontTools. A lookup's
signature is its type plus its glyph mapping by glyph NAME (single/multiple/
alternate/ligature); a chaining/contextual lookup's signature is 'ctx' plus the
sorted signatures of the lookups it calls (context glyphs are not compared, so
subtable packing does not matter). Lookup indices and order are ignored: this
asks only WHICH effects a key reaches.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 langsys_effects.py <release.ttf> <candidate.ttf>
"""
import sys

from fontTools.ttLib import TTFont


def lookup_sig(gsub, idx, memo, stack=()):
    if idx in memo:
        return memo[idx]
    lk = gsub.LookupList.Lookup[idx]
    items = set()
    kind = lk.LookupType
    for st in lk.SubTable:
        t = st.LookupType if kind != 7 else st.ExtSubTable.LookupType
        s = st if kind != 7 else st.ExtSubTable
        if t == 1:
            items |= {("s", a, b) for a, b in s.mapping.items()}
        elif t == 2:
            items |= {("m", a, tuple(b)) for a, b in s.mapping.items()}
        elif t == 3:
            items |= {("a", a, tuple(b)) for a, b in s.alternates.items()}
        elif t == 4:
            for first, ligs in s.ligatures.items():
                items |= {("l", (first,) + tuple(l.Component), l.LigGlyph) for l in ligs}
        elif t in (5, 6):
            called = set()
            for attr in ("SubstLookupRecord",):
                pass
            # collect every nested lookup index, whatever the format
            def walk(obj):
                if obj is None:
                    return
                if hasattr(obj, "LookupListIndex") and hasattr(obj, "SequenceIndex"):
                    called.add(obj.LookupListIndex)
                    return
                if isinstance(obj, list):
                    for o in obj:
                        walk(o)
                    return
                if hasattr(obj, "__dict__"):
                    for k, v in vars(obj).items():
                        if k in ("Coverage", "ClassDef", "BacktrackClassDef", "InputClassDef",
                                 "LookAheadClassDef", "BacktrackCoverage", "InputCoverage",
                                 "LookAheadCoverage"):
                            continue
                        if isinstance(v, (list,)) or hasattr(v, "__dict__"):
                            walk(v)
            walk(s)
            nested = []
            for c in sorted(called):
                if c in stack:
                    nested.append(("recursive", c))
                else:
                    nested.append(lookup_sig(gsub, c, memo, stack + (idx,)))
            items.add(("ctx", tuple(sorted(nested, key=repr))))
        else:
            items.add(("type", t))
    sig = (kind if kind != 7 else "ext", frozenset(items))
    memo[idx] = sig
    return sig


def keys(font):
    gsub = font["GSUB"].table
    memo = {}
    out = {}
    feats = gsub.FeatureList.FeatureRecord
    for sr in gsub.ScriptList.ScriptRecord:
        langs = []
        if sr.Script.DefaultLangSys:
            langs.append(("dflt", sr.Script.DefaultLangSys))
        langs += [(l.LangSysTag, l.LangSys) for l in sr.Script.LangSysRecord]
        for tag, ls in langs:
            for fi in ls.FeatureIndex:
                fr = feats[fi]
                sigs = frozenset(lookup_sig(gsub, li, memo) for li in fr.Feature.LookupListIndex)
                k = (sr.ScriptTag, tag.strip() if tag != "dflt" else "dflt", fr.FeatureTag)
                out[k] = out.get(k, frozenset()) | sigs
    return out


def main():
    rel, cand = sys.argv[1:3]
    a, b = keys(TTFont(rel)), keys(TTFont(cand))
    allk = sorted(set(a) | set(b))
    diff = [k for k in allk if a.get(k) != b.get(k)]
    print("%d keys in release, %d in candidate, %d of %d differ" % (len(a), len(b), len(diff), len(allk)))
    for k in diff:
        ra, rb = a.get(k), b.get(k)
        if ra is None or rb is None:
            print("  %s/%s %s: only in %s" % (k[0], k[1], k[2], "candidate" if ra is None else "release"))
            continue
        extra = rb - ra
        missing = ra - rb

        def short(sig):
            kind, items = sig
            its = sorted(items, key=repr)[:3]
            return "type%s[%d items, e.g. %s]" % (kind, len(items), its)
        print("  %s/%s %s: candidate has %d extra effect(s) %s; lacks %d %s" % (
            k[0], k[1], k[2], len(extra), [short(s) for s in extra], len(missing),
            [short(s) for s in missing]))


if __name__ == "__main__":
    main()
