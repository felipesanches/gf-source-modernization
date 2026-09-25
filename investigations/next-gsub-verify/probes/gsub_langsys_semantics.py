#!/usr/bin/env python3
"""Question: do two fonts (release, build) apply the same GSUB substitutions, in the
same order, under EVERY language system either of them declares -- independently of
lookup indices, lookup types (5 vs 6), subtable packing and formats?

Written independently of investigations/next-gsub/probes/gsub_semantic_diff.py to
cross-check it.

Model of OpenType GSUB application used here:
  * for a (script, language) the shaper picks the LangSys (falling back to the
    script's DefaultLangSys, then to DFLT); a feature applies only if that LangSys
    lists it; its lookups run in LookupList-index order across all active features.
  * inside a lookup, at each position, subtables are tried in order and the first one
    that matches applies. So a lookup's behaviour is, per starting glyph, the ORDERED
    list of rules whose first input position contains that glyph. For a contextual
    lookup (type 5/6, any format) a rule is (backtrack sets, input sets, lookahead
    sets, [(sequence index, nested lookup behaviour)]); type 5 is type 6 with empty
    backtrack/lookahead. For single/ligature/alternate/multiple lookups the rule is
    the mapping for that glyph (ligatures ordered as the subtable orders them).
  * nested lookups are expanded to their behaviour, so a nested lookup's index is
    irrelevant.

Output: per language system (union of both fonts), per feature: EQUAL, or the first
difference; then, per language system, whether the application SEQUENCE (lookup
behaviours in index order, each tagged with the features that reach it) is equal.
Also lists feature-less lookups (reached only through a chain) with their indices.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY gsub_langsys_semantics.py <release.ttf> <build.ttf>
"""
import sys

from fontTools.ttLib import TTFont


def lookup_behaviour(gsub, idx, memo, stack=()):
    """Canonical behaviour of lookup idx: {first_glyph: tuple(rules)} as a frozen tuple."""
    if idx in memo:
        return memo[idx]
    if idx in stack:
        return ("RECURSION", idx)
    lk = gsub.LookupList.Lookup[idx]
    per = {}

    def add(g, rule):
        per.setdefault(g, []).append(rule)

    for st in lk.SubTable:
        t = lk.LookupType
        if t == 7:
            t = st.ExtSubTable.LookupType if hasattr(st, "ExtSubTable") else st.ExtensionLookupType
            st = st.ExtSubTable
        if t == 1:
            for g, v in st.mapping.items():
                add(g, ("single", v))
        elif t == 2:
            for g, v in st.mapping.items():
                add(g, ("multiple", tuple(v)))
        elif t == 3:
            for g, v in st.alternates.items():
                add(g, ("alternate", tuple(v)))
        elif t == 4:
            for g, ligs in st.ligatures.items():
                for lig in ligs:
                    add(g, ("ligature", tuple(lig.Component), lig.LigGlyph))
        elif t in (5, 6):
            for first, rule in context_rules(st, t):
                back, inp, ahead, recs = rule
                nested = tuple((si, lookup_behaviour(gsub, li, memo, stack + (idx,)))
                               for si, li in recs)
                add(first, ("context", back, inp, ahead, nested))
        else:
            add("*", ("unknown-type", t))
    out = tuple(sorted((g, canonical_rules(r)) for g, r in per.items()))
    memo[idx] = out
    return out


def _sets(rule):
    """Aligned constraint sets of a context rule: {offset: set}, input start = 0."""
    _, back, inp, ahead, _n = rule
    d = {}
    for k, s in enumerate(reversed(back)):
        d[-1 - k] = s
    for k, s in enumerate(inp):
        d[k] = s
    for k, s in enumerate(ahead):
        d[len(inp) + k] = s
    return d


def _overlap(x, y):
    """Can two context rules both match at one position?"""
    dx, dy = _sets(x), _sets(y)
    for off in set(dx) & set(dy):
        a, b = dx[off], dy[off]
        if isinstance(a, tuple) or isinstance(b, tuple):   # symbolic class 0
            continue
        if not (a & b):
            return False
    return True


def canonical_rules(rules):
    """The behaviour-relevant form of one first glyph's ordered rule list.

    ligature: the set of LIVE ligatures (one is dead when an earlier ligature's
      components are a prefix of its own; among live ones the longest match wins,
      so their order no longer matters).
    context: the order of two rules matters only if both can match at one position;
      rules are sorted into a canonical order, and every pair whose relative order
      the sort changed must be disjoint -- otherwise the original order is kept
      (tagged) so a real reordering shows up as a difference.
    """
    if rules and all(r[0] == "ligature" for r in rules):
        live = []
        for r in rules:
            comps = r[1]
            if any(comps[:len(m[1])] == m[1] for m in live):
                continue
            live.append(r)
        return ("ligatures", tuple(sorted(live)))
    if rules and all(r[0] == "context" for r in rules):
        key = lambda r: repr(r)
        srt = sorted(rules, key=key)
        pos = {id(r): i for i, r in enumerate(rules)}
        for i in range(len(srt)):
            for j in range(i + 1, len(srt)):
                if pos[id(srt[i])] > pos[id(srt[j])] and _overlap(srt[i], srt[j]):
                    return ("context-ordered", tuple(rules))
        return ("context", tuple(srt))
    return ("plain", tuple(rules))


def _cov(c):
    return tuple(c.glyphs) if c is not None else ()


def context_rules(st, t):
    """Yield (first_glyph, (backtrack, input, lookahead, [(seqIndex, lookupIndex)]))
    with every position as a frozenset of glyph names; backtrack is in logical
    (text) order nearest-last."""
    fmt = st.Format
    if t == 5:
        if fmt == 1:
            cov = _cov(st.Coverage)
            for g, rs in zip(cov, st.SubRuleSet or []):
                if rs is None:
                    continue
                for r in rs.SubRule:
                    inp = (frozenset([g]),) + tuple(frozenset([x]) for x in r.Input)
                    yield g, ((), inp, (), tuple((x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord))
        elif fmt == 2:
            cov = _cov(st.Coverage)
            cd = st.ClassDef.classDefs
            allg = None

            def members(c, universe):
                return frozenset(g for g in universe if cd.get(g, 0) == c)
            universe = set(cd) | set(cov)
            for g in cov:
                c0 = cd.get(g, 0)
                rs = st.SubClassSet[c0] if st.SubClassSet and c0 < len(st.SubClassSet) else None
                if rs is None:
                    continue
                for r in rs.SubClassRule:
                    inp = (frozenset([g]),) + tuple(("class", c, members(c, universe)) if c == 0 else members(c, universe) for c in r.Class)
                    yield g, ((), inp, (), tuple((x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord))
        elif fmt == 3:
            covs = [frozenset(c.glyphs) for c in st.Coverage]
            recs = tuple((x.SequenceIndex, x.LookupListIndex) for x in st.SubstLookupRecord)
            for g in st.Coverage[0].glyphs:
                yield g, ((), (frozenset([g]),) + tuple(covs[1:]), (), recs)
    else:
        if fmt == 1:
            cov = _cov(st.Coverage)
            for g, rs in zip(cov, st.ChainSubRuleSet or []):
                if rs is None:
                    continue
                for r in rs.ChainSubRule:
                    back = tuple(frozenset([x]) for x in reversed(r.Backtrack))
                    inp = (frozenset([g]),) + tuple(frozenset([x]) for x in r.Input)
                    ahead = tuple(frozenset([x]) for x in r.LookAhead)
                    yield g, (back, inp, ahead, tuple((x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord))
        elif fmt == 2:
            cov = _cov(st.Coverage)
            bcd = st.BacktrackClassDef.classDefs if st.BacktrackClassDef else {}
            icd = st.InputClassDef.classDefs if st.InputClassDef else {}
            lcd = st.LookAheadClassDef.classDefs if st.LookAheadClassDef else {}

            def mem(cd, c):
                if c == 0:
                    return ("class0-of", tuple(sorted(cd)))   # "everything not listed" -- keep symbolic
                return frozenset(g for g, k in cd.items() if k == c)
            for g in cov:
                c0 = icd.get(g, 0)
                rs = st.ChainSubClassSet[c0] if st.ChainSubClassSet and c0 < len(st.ChainSubClassSet) else None
                if rs is None:
                    continue
                for r in rs.ChainSubClassRule:
                    back = tuple(mem(bcd, c) for c in reversed(r.Backtrack))
                    inp = (frozenset([g]),) + tuple(mem(icd, c) for c in r.Input)
                    ahead = tuple(mem(lcd, c) for c in r.LookAhead)
                    yield g, (back, inp, ahead, tuple((x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord))
        elif fmt == 3:
            back = tuple(frozenset(c.glyphs) for c in reversed(st.BacktrackCoverage))
            covs = [frozenset(c.glyphs) for c in st.InputCoverage]
            ahead = tuple(frozenset(c.glyphs) for c in st.LookAheadCoverage)
            recs = tuple((x.SequenceIndex, x.LookupListIndex) for x in st.SubstLookupRecord)
            for g in st.InputCoverage[0].glyphs:
                yield g, (back, (frozenset([g]),) + tuple(covs[1:]), ahead, recs)


def langsystems(gsub):
    """{(script, lang): {feature_tag: [lookup indices]}} (lang 'dflt' = DefaultLangSys)."""
    out = {}
    feats = gsub.FeatureList.FeatureRecord
    for sr in gsub.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys is not None:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        for lr in sr.Script.LangSysRecord:
            systems.append((lr.LangSysTag.strip(), lr.LangSys))
        for lang, ls in systems:
            m = {}
            idxs = list(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                idxs.append(ls.ReqFeatureIndex)
            for fi in idxs:
                fr = feats[fi]
                m.setdefault(fr.FeatureTag, []).extend(fr.Feature.LookupListIndex)
            out[(sr.ScriptTag.strip(), lang)] = {k: sorted(set(v)) for k, v in m.items()}
    return out


def resolve(ls_map, script, lang):
    """What a shaper selects for (script, lang): exact LangSys, else script dflt, else DFLT."""
    for key in ((script, lang), (script, "dflt"), ("DFLT", "dflt")):
        if key in ls_map:
            return key, ls_map[key]
    return None, {}


def main():
    rel, bld = sys.argv[1], sys.argv[2]
    R, B = TTFont(rel), TTFont(bld)
    if "GSUB" not in R or "GSUB" not in B:
        print("GSUB present: release=%s build=%s" % ("GSUB" in R, "GSUB" in B))
        return
    rg, bg = R["GSUB"].table, B["GSUB"].table
    rmemo, bmemo = {}, {}
    rls, bls = langsystems(rg), langsystems(bg)
    keys = sorted(set(rls) | set(bls))
    print("release language systems:", sorted(rls))
    print("build   language systems:", sorted(bls))
    n_diff = 0
    for key in keys:
        # what a shaper would use for this (script, lang) in each font
        rk, rm = resolve(rls, *key)
        bk, bm = resolve(bls, *key)
        tags = sorted(set(rm) | set(bm))
        diffs = []
        for tag in tags:
            ra = [lookup_behaviour(rg, i, rmemo) for i in rm.get(tag, [])]
            ba = [lookup_behaviour(bg, i, bmemo) for i in bm.get(tag, [])]
            if ra != ba:
                if len(ra) != len(ba):
                    diffs.append("%s: %d lookups (release %s) vs %d (build %s)"
                                 % (tag, len(ra), rm.get(tag), len(ba), bm.get(tag)))
                else:
                    for j, (x, y) in enumerate(zip(ra, ba)):
                        if x != y:
                            xs, ys = dict(x), dict(y)
                            gd = sorted(g for g in set(xs) | set(ys) if xs.get(g) != ys.get(g))
                            diffs.append("%s: lookup #%d of the feature (release %d, build %d) differs for %d first glyph(s), e.g. %s"
                                         % (tag, j, rm[tag][j], bm[tag][j], len(gd), gd[:5]))
                            if gd and "-v" in sys.argv:
                                diffs.append("        release %s: %s" % (gd[0], str(xs.get(gd[0]))[:600]))
                                diffs.append("        build   %s: %s" % (gd[0], str(ys.get(gd[0]))[:600]))
        # application sequence with all features on: lookups by index, tagged with features
        def seq(m, g, memo):
            owners = {}
            for tag, idxs in m.items():
                for i in idxs:
                    owners.setdefault(i, set()).add(tag)
            return [(tuple(sorted(owners[i])), lookup_behaviour(g, i, memo)) for i in sorted(owners)]
        same_seq = seq(rm, rg, rmemo) == seq(bm, bg, bmemo)
        state = "EQUAL" if not diffs and same_seq else "DIFFERS"
        if state != "EQUAL":
            n_diff += 1
        print("%-12s resolves to release %s / build %s: %s; application sequence %s"
              % ("%s/%s" % key, rk, bk, state, "equal" if same_seq else "DIFFERS"))
        for d in diffs:
            print("     ", d)
    # feature-less lookups
    def reached(g):
        s = set()
        for fr in g.FeatureList.FeatureRecord:
            s.update(fr.Feature.LookupListIndex)
        return s
    for name, g in (("release", rg), ("build", bg)):
        fl = [i for i in range(len(g.LookupList.Lookup)) if i not in reached(g)]
        print("%s: %d lookups; feature-less (reached only through a chain): %s; types %s"
              % (name, len(g.LookupList.Lookup), fl, [g.LookupList.Lookup[i].LookupType for i in range(len(g.LookupList.Lookup))]))
    print("SUMMARY: %d of %d language systems differ" % (n_diff, len(keys)))


if __name__ == "__main__":
    main()
