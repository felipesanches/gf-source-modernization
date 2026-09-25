#!/usr/bin/env python3
"""The table gate with the GSUB-arbitration change the gsub unit proposes, as a wrapper.

Question answered: with sfd-batch5/tools/table_gate.py (2f43693, md5 68c33418) left
untouched, what does the gate report for a pair once arbitrate_gsub_lookup_order()

  1. compares CONTEXTUAL lookups by their rules instead of by (type, 0 entries):
     for every glyph that can start a match, the ordered list of rules that can fire
     there -- backtrack, input, lookahead as glyph sets, and each nested lookup by its
     own content -- across all subtables in application order. The lookup TYPE (5
     Context vs 6 ChainContext: a type-6 rule with no backtrack and no lookahead IS a
     type-5 rule), the FORMAT (1/2/3) and the SUBTABLE PACKING are representation.
     RibeyeMarrow-Regular is the case: FontForge wrote its `frac` as nine format-3
     ChainContext subtables, fontc (fea-rs 1.0.0 contextual.rs `into_lookups`: no rule
     has backtrack or lookahead -> SequenceContext) writes the same nine rules, in the
     same order per first glyph, as one type-5 subtable, and condition 2 refused on the
     type alone. The shared gate counted every contextual lookup as 0 entries, so it
     never compared their rules at all; this is stricter there, not looser.
  2. says so in the RELEASE-STALE line when an accepted pair's contextual lookups differ
     in type or packing;
  3. shapes, besides the existing two-character corpus, every sequence a contextual
     rule or a ligature spells (each position filled from its coverage/class by every
     glyph the cmap reaches, at most 200 per rule), because a two-character word cannot
     reach a three- or four-glyph context ("1/4", "0/00", "1.a").

It is otherwise the same gate: same argv, same output format. The original function
is taken from the shared file and changed by the exact-match replacements in PATCHES
below (each must apply exactly once, or this refuses to run), so the difference from
the shared gate is only what those replacements say.

Usage:
  table_gate_gsub_proposed.py <d3.json> --fonts <shipped.ttf> <built.ttf>
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import hashlib
import importlib.util
import itertools
import sys

SHARED = "/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py"
spec = importlib.util.spec_from_file_location("table_gate", SHARED)
tg = importlib.util.module_from_spec(spec)
sys.modules["table_gate"] = tg
spec.loader.exec_module(tg)


def _ctx_type(t):
    """A type-5 Context lookup is a type-6 ChainContext lookup with no backtrack and
    no lookahead; the compiler's choice between them is representation."""
    return 6 if t == 5 else t


def _subtables(lk):
    sts = list(lk.SubTable)
    if lk.LookupType == 7:
        return sts[0].ExtensionLookupType, [s.ExtSubTable for s in sts]
    return lk.LookupType, sts


def _canon_lookup(lks, i, key, memo, stack=()):
    """Content identity of lookup i: plain lookups by (type, sorted rules); contextual
    lookups by {first glyph -> ordered rules that can fire there}."""
    if i in memo:
        return memo[i]
    if i in stack:
        return ("recursive",)
    typ, sts = _subtables(lks[i])
    flag = lks[i].LookupFlag
    if typ not in (5, 6):
        rules = []
        for st in sts:
            for a, b in (getattr(st, "mapping", None) or {}).items():
                rules.append(("m", key(a), tuple(key(x) for x in b) if isinstance(b, (list, tuple)) else key(b)))
            for a, alts in (getattr(st, "alternates", None) or {}).items():
                rules.append(("a", key(a), tuple(key(x) for x in alts)))
            for a, ligs in (getattr(st, "ligatures", None) or {}).items():
                for lg in ligs:
                    rules.append(("l", (key(a),) + tuple(key(c) for c in lg.Component), key(lg.LigGlyph)))
        out = ("plain", typ, flag, tuple(sorted(rules, key=repr)))
        memo[i] = out
        return out

    def nested(recs):
        return tuple((r.SequenceIndex, hashlib.sha1(repr(_canon_lookup(
            lks, r.LookupListIndex, key, memo, stack + (i,))).encode()).hexdigest()[:12])
            for r in recs)

    def gset(glyphs):
        return frozenset(key(g) for g in glyphs)

    ordered = []   # (first-glyph set, backtrack sets nearest-first, input sets after first, lookahead sets, nested)
    for st in sts:
        fmt = getattr(st, "Format", None)
        if fmt == 3:
            if typ == 6:
                back = tuple(gset(c.glyphs) for c in st.BacktrackCoverage)
                inp = [gset(c.glyphs) for c in st.InputCoverage]
                ahead = tuple(gset(c.glyphs) for c in st.LookAheadCoverage)
            else:
                back, ahead = (), ()
                inp = [gset(c.glyphs) for c in st.Coverage]
            ordered.append((inp[0], back, tuple(inp[1:]), ahead, nested(st.SubstLookupRecord)))
        elif fmt == 1:
            cov = st.Coverage.glyphs
            sets = getattr(st, "ChainSubRuleSet", None) or getattr(st, "SubRuleSet", None) or []
            for gi, rs in enumerate(sets):
                for r in (getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None) or []):
                    ordered.append((gset([cov[gi]]),
                                    tuple(frozenset([key(g)]) for g in getattr(r, "Backtrack", [])),
                                    tuple(frozenset([key(g)]) for g in r.Input),
                                    tuple(frozenset([key(g)]) for g in getattr(r, "LookAhead", [])),
                                    nested(r.SubstLookupRecord)))
        elif fmt == 2:
            cov = set(st.Coverage.glyphs)
            ic = getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None)
            bc = getattr(st, "BacktrackClassDef", None)
            lc = getattr(st, "LookAheadClassDef", None)

            def members(cd, c, restrict=None):
                defs = cd.classDefs if cd is not None else {}
                if c == 0:
                    # class 0 is "every glyph no class names": unbounded, so keep it
                    # symbolic -- equal only to the same complement
                    return frozenset([("NOT",) + tuple(sorted(key(g) for g in defs))]) if restrict is None \
                        else gset(g for g in restrict if g not in defs)
                m = [g for g, k in defs.items() if k == c]
                return gset(g for g in m if restrict is None or g in restrict)
            sets = getattr(st, "ChainSubClassSet", None) or getattr(st, "SubClassSet", None) or []
            for ci, cs in enumerate(sets):
                if cs is None:
                    continue
                for r in (getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None) or []):
                    inp = list(getattr(r, "Input", None) or getattr(r, "Class", []))
                    ordered.append((members(ic, ci, cov),
                                    tuple(members(bc, c) for c in getattr(r, "Backtrack", [])),
                                    tuple(members(ic, c) for c in inp),
                                    tuple(members(lc, c) for c in getattr(r, "LookAhead", [])),
                                    nested(r.SubstLookupRecord)))
        else:
            ordered.append((frozenset(), (), (), (), ("unknown-format", fmt)))
    by_first = {}
    for first, back, inp, ahead, rec in ordered:
        for g in first:
            by_first.setdefault(g, []).append((back, inp, ahead, rec))

    def norm(rule):
        back, inp, ahead, rec = rule
        f = lambda seq: tuple(tuple(sorted(map(repr, s))) for s in seq)
        return (f(back), f(inp), f(ahead), rec)
    out = ("ctx", flag, tuple(sorted((repr(g), tuple(norm(r) for r in rules))
                                     for g, rules in by_first.items())))
    memo[i] = out
    return out


def _ctx_profile(font, key):
    """Multiset of contextual lookups' content identities."""
    g = font["GSUB"].table
    lks = g.LookupList.Lookup if g.LookupList else []
    memo = {}
    out = []
    for i, lk in enumerate(lks):
        typ, _ = _subtables(lk)
        if typ in (5, 6):
            out.append(hashlib.sha1(repr(_canon_lookup(lks, i, key, memo)).encode()).hexdigest()[:16])
    return sorted(out)


def _rule_sequences(S, B, cap=200):
    """Text for every sequence a contextual rule or a ligature spells, both fonts."""
    words = set()
    for f in (S, B):
        cmap = tg._best_cmap(f)
        rev = {}
        for c, n in sorted(cmap.items()):
            rev.setdefault(n, c)
        if "GSUB" not in f:
            continue
        for lk in f["GSUB"].table.LookupList.Lookup:
            typ, sts = _subtables(lk)
            for st in sts:
                seqs = []
                for a, ligs in (getattr(st, "ligatures", None) or {}).items():
                    for lg in ligs:
                        seqs.append([[a]] + [[c] for c in lg.Component])
                fmt = getattr(st, "Format", None)
                if typ in (5, 6) and fmt == 3:
                    if typ == 6:
                        pos = [list(c.glyphs) for c in reversed(st.BacktrackCoverage)] + \
                              [list(c.glyphs) for c in st.InputCoverage] + \
                              [list(c.glyphs) for c in st.LookAheadCoverage]
                    else:
                        pos = [list(c.glyphs) for c in st.Coverage]
                    seqs.append(pos)
                elif typ in (5, 6) and fmt == 1:
                    cov = st.Coverage.glyphs
                    sets = getattr(st, "ChainSubRuleSet", None) or getattr(st, "SubRuleSet", None) or []
                    for gi, rs in enumerate(sets):
                        for r in (getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None) or []):
                            seqs.append([[x] for x in reversed(getattr(r, "Backtrack", []))] + [[cov[gi]]] +
                                        [[x] for x in r.Input] + [[x] for x in getattr(r, "LookAhead", [])])
                elif typ in (5, 6) and fmt == 2:
                    cov = list(st.Coverage.glyphs)
                    ic = getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None)
                    bc = getattr(st, "BacktrackClassDef", None)
                    lc = getattr(st, "LookAheadClassDef", None)

                    def mem(cd, c):
                        return [g for g, k in (cd.classDefs if cd is not None else {}).items() if k == c]
                    sets = getattr(st, "ChainSubClassSet", None) or getattr(st, "SubClassSet", None) or []
                    for ci, cs in enumerate(sets):
                        if cs is None:
                            continue
                        first = [g for g in cov if (ic.classDefs.get(g, 0) if ic is not None else 0) == ci]
                        for r in (getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None) or []):
                            inp = list(getattr(r, "Input", None) or getattr(r, "Class", []))
                            seqs.append([mem(bc, c) for c in reversed(getattr(r, "Backtrack", []))] + [first] +
                                        [mem(ic, c) for c in inp] + [mem(lc, c) for c in getattr(r, "LookAhead", [])])
                for pos in seqs:
                    opts = [[chr(rev[n]) for n in p if n in rev] for p in pos]
                    if not opts or any(not o for o in opts):
                        continue
                    for n, combo in enumerate(itertools.product(*opts)):
                        if n >= cap:
                            break
                        words.add("".join(combo))
    return sorted(words)


def _ctx_repacked(shipped, built):
    """True when the two fonts' contextual lookups differ in type or subtable count
    (accepted only after their rules compared equal): say so in the stale line."""
    from fontTools.ttLib import TTFont

    def shape(path):
        g = TTFont(path)["GSUB"].table
        return sorted((_subtables(lk)[0], len(lk.SubTable)) for lk in g.LookupList.Lookup
                      if _subtables(lk)[0] in (5, 6))
    return shape(shipped) != shape(built)


PATCHES = [
    ('''            sig = sorted((lk.LookupType,''',
     '''            sig = sorted((_ctx_type(lk.LookupType),'''),
    ('''            types = sorted(lk.LookupType for lk in g.LookupList.Lookup)''',
     '''            types = sorted(_ctx_type(lk.LookupType) for lk in g.LookupList.Lookup)'''),
    ('''            return feats, sig, (types, sorted(rules))''',
     '''            return feats, sig, (types, sorted(rules)), _ctx_profile(f, key)'''),
    ('''        sf, ssig, salt = profile(S, s_key)
        bf, bsig, balt = profile(B, b_key)
        if sf != bf:
            if _dbg:
                print("TRACE gsub: feature tags differ", sf, bf)
            return rows, []''',
     '''        sf, ssig, salt, sctx = profile(S, s_key)
        bf, bsig, balt, bctx = profile(B, b_key)
        if sf != bf:
            if _dbg:
                print("TRACE gsub: feature tags differ", sf, bf)
            return rows, []
        if sctx != bctx:
            if _dbg:
                print("TRACE gsub: contextual lookups' rules differ (%d vs %d contextual lookups, "
                      "%d identical)" % (len(sctx), len(bctx), len(set(sctx) & set(bctx))))
            return rows, []'''),
    ('''        on = {t: True for t in sf}''',
     '''        _seen = set(words)
        words += [w for w in _rule_sequences(S, B) if w not in _seen]
        on = {t: True for t in sf}'''),
    ('    return keep, ["%s; %d shaped runs identical across %d language(s), with the "',
     '    if _ctx_repacked(shipped, built):\n'
     '        how += ("; its contextual lookups carry the same rules per first glyph in another "\n'
     '                "lookup type (5/6), format or subtable packing")\n'
     '    return keep, ["%s; %d shaped runs identical across %d language(s), with the "'),
]


def _build():
    src = open(SHARED).read()
    start = src.index("def arbitrate_gsub_lookup_order(rows, shipped, built):")
    end = src.index("def arbitrate_legacy_kern(rows, shipped, built):")
    fn = src[start:end]
    for old, new in PATCHES:
        if fn.count(old) != 1:
            sys.exit("FATAL: patch does not apply exactly once: %r" % old[:60])
        fn = fn.replace(old, new)
    ns = tg.__dict__
    ns.update({"_ctx_type": _ctx_type, "_ctx_profile": _ctx_profile, "_rule_sequences": _rule_sequences,
               "_ctx_repacked": _ctx_repacked, "_subtables": _subtables})
    exec(compile(fn, SHARED + " (patched by table_gate_gsub_proposed.py)", "exec"), ns)


_build()

if __name__ == "__main__":
    tg.main()
