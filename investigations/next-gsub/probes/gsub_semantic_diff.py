#!/usr/bin/env python3
"""Is a GSUB difference one of ORDER, of REGISTRATION, or of CONTENT?

Question: the gate flags GSUB.script_list / feature_list / lookup_list. Those rows mix
three different things; this probe separates them, release vs build:

  1. CONTENT -- each lookup gets an identity from what it does (type + every rule,
     contextual lookups included: coverages / classes / nested lookups resolved to
     THEIR identity). Lookups present in one font and not the other are listed with
     their rules; lookups that "pair" (same feature, same slot) but differ are diffed
     rule by rule (release-only / build-only rules).
  2. REGISTRATION -- per (script, language, feature), which lookup identities run.
  3. ORDER -- per (script, language), the sequence of lookup identities a shaper
     applies (lookup-list order, all features of that language system), and whether
     the two fonts' sequences are the same after dropping lookups neither feature
     reaches (nested-only lookups; their list position cannot affect shaping).

Glyphs are keyed by name (both fonts keep the source's glyph names; run with
--by-codepoint to key mapped glyphs by codepoint instead).

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 gsub_semantic_diff.py \
        <release.ttf> <build.ttf> [--by-codepoint]
"""
import hashlib
import sys

from fontTools.ttLib import TTFont


class Lk:
    pass


def analyse(path, by_cp):
    f = TTFont(path)
    rev = {}
    for c, n in sorted(f.getBestCmap().items()):
        rev.setdefault(n, c)

    def k(n):
        return "U+%04X" % rev[n] if (by_cp and n in rev) else n

    t = f["GSUB"].table if "GSUB" in f else None
    if t is None:
        return None
    lks = t.LookupList.Lookup if t.LookupList else []
    memo = {}

    def rules_of(i, stack=()):
        if i in memo:
            return memo[i]
        lk = lks[i]
        typ = lk.LookupType
        sts = list(lk.SubTable)
        if typ == 7:
            typ = sts[0].ExtensionLookupType
            sts = [s.ExtSubTable for s in sts]
        rules = []
        for st in sts:
            fmt = getattr(st, "Format", None)
            if typ == 1:
                rules += [("sub", k(a), k(b)) for a, b in st.mapping.items()]
            elif typ == 2:
                rules += [("mult", k(a), tuple(k(x) for x in b)) for a, b in st.mapping.items()]
            elif typ == 3:
                rules += [("alt", k(a), tuple(k(x) for x in b)) for a, b in st.alternates.items()]
            elif typ == 4:
                for a, ligs in st.ligatures.items():
                    for lg in ligs:
                        rules.append(("lig", (k(a),) + tuple(k(x) for x in lg.Component), k(lg.LigGlyph)))
            elif typ in (5, 6):
                def nested(recs):
                    out = []
                    for r in recs:
                        if r.LookupListIndex in stack:
                            out.append((r.SequenceIndex, "recursive"))
                        else:
                            out.append((r.SequenceIndex, lid(r.LookupListIndex, stack + (i,))))
                    return tuple(out)
                if fmt == 3:
                    def cov(cs):
                        return tuple(tuple(sorted(k(g) for g in c.glyphs)) for c in (cs or []))
                    if typ == 6:
                        rules.append(("chain3", cov(st.BacktrackCoverage), cov(st.InputCoverage),
                                      cov(st.LookAheadCoverage), nested(st.SubstLookupRecord)))
                    else:
                        rules.append(("ctx3", cov(st.Coverage), nested(st.SubstLookupRecord)))
                elif fmt == 1:
                    sets = getattr(st, "ChainSubRuleSet", None) or getattr(st, "SubRuleSet", None) or []
                    for gi, rs in enumerate(sets):
                        first = st.Coverage.glyphs[gi]
                        for r in (getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None) or []):
                            rules.append(("ctx1", tuple(k(g) for g in getattr(r, "Backtrack", [])),
                                          (k(first),) + tuple(k(g) for g in r.Input),
                                          tuple(k(g) for g in getattr(r, "LookAhead", [])),
                                          nested(r.SubstLookupRecord)))
                elif fmt == 2:
                    def classes(cd, glyphs=None):
                        m = {}
                        for g, c in (cd.classDefs.items() if cd else []):
                            m.setdefault(c, set()).add(k(g))
                        return m
                    bc = classes(getattr(st, "BacktrackClassDef", None))
                    ic = classes(getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None))
                    lc = classes(getattr(st, "LookAheadClassDef", None))
                    covset = set(k(g) for g in st.Coverage.glyphs)
                    def expand(cm, c, restrict=None):
                        s = cm.get(c)
                        if s is None:
                            return ("class0",)
                        return tuple(sorted(s & restrict if restrict else s))
                    sets = getattr(st, "ChainSubClassSet", None) or getattr(st, "SubClassSet", None) or []
                    for ci, cs in enumerate(sets):
                        if cs is None:
                            continue
                        for r in (getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None) or []):
                            inp = list(getattr(r, "Input", None) or getattr(r, "Class", []))
                            rules.append(("ctx2",
                                          tuple(expand(bc, c) for c in getattr(r, "Backtrack", [])),
                                          (expand(ic, ci, covset),) + tuple(expand(ic, c) for c in inp),
                                          tuple(expand(lc, c) for c in getattr(r, "LookAhead", [])),
                                          nested(r.SubstLookupRecord)))
            else:
                rules.append(("type%d" % typ,))
        memo[i] = (typ, lk.LookupFlag, rules)
        return memo[i]

    def lid(i, stack=()):
        typ, flag, rules = rules_of(i, stack)
        # contextual subtables are ORDERED (first match wins), plain rules are not
        body = rules if typ in (5, 6) else sorted(rules)
        return "T%d/%X:%s:%d" % (typ, flag, hashlib.sha1(repr(body).encode()).hexdigest()[:8], len(rules))

    ids = [lid(i) for i in range(len(lks))]
    feats = t.FeatureList.FeatureRecord
    reached = set()
    reg = {}
    seq = {}
    for sr in t.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys is not None:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        systems += [(lr.LangSysTag.strip(), lr.LangSys) for lr in sr.Script.LangSysRecord]
        for lang, ls in systems:
            fis = list(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                fis.append(ls.ReqFeatureIndex)
            per = {}
            for fi in fis:
                fr = feats[fi]
                for li in fr.Feature.LookupListIndex:
                    reached.add(li)
                    per.setdefault(li, set()).add(fr.FeatureTag)
                reg[(sr.ScriptTag, lang, fr.FeatureTag)] = [ids[li] for li in fr.Feature.LookupListIndex]
            seq[(sr.ScriptTag, lang)] = [(ids[li], "+".join(sorted(per[li]))) for li in sorted(per)]
    out = Lk()
    out.ids, out.rules, out.reg, out.seq, out.reached = ids, [rules_of(i) for i in range(len(lks))], reg, seq, reached
    out.nested_only = [i for i in range(len(lks)) if i not in reached]
    return out


def main():
    rel, bld = sys.argv[1], sys.argv[2]
    by_cp = "--by-codepoint" in sys.argv
    A, B = analyse(rel, by_cp), analyse(bld, by_cp)
    if A is None or B is None:
        print("GSUB present: release %s, build %s" % (A is not None, B is not None))
        return
    print("== LOOKUPS: release %d, build %d; nested-only (no feature): release %s, build %s"
          % (len(A.ids), len(B.ids), A.nested_only, B.nested_only))
    sa, sb = set(A.ids), set(B.ids)
    print("   identical lookup contents: %d; release-only: %d; build-only: %d"
          % (len(sa & sb), len(sa - sb), len(sb - sa)))
    for i, x in enumerate(A.ids):
        if x not in sb:
            print("   release-only L%d %s" % (i, x))
    for i, x in enumerate(B.ids):
        if x not in sa:
            print("   build-only   L%d %s" % (i, x))
    # rule-level diff for lookups that differ, paired by the feature(s) they serve
    def by_feat(X):
        m = {}
        for (s, l, ft), lst in X.reg.items():
            for pos, x in enumerate(lst):
                m.setdefault((ft, pos), set()).add(x)
        return m
    fa, fb = by_feat(A), by_feat(B)
    for key in sorted(set(fa) | set(fb)):
        xa, xb = fa.get(key, set()), fb.get(key, set())
        if xa == xb:
            continue
        for a in sorted(xa - xb):
            for b in sorted(xb - xa):
                ra = A.rules[A.ids.index(a)][2]
                rb = B.rules[B.ids.index(b)][2]
                ro = [r for r in ra if r not in rb]
                bo = [r for r in rb if r not in ra]
                print("   feature %s slot %d: release %s vs build %s: %d release-only rule(s), %d build-only"
                      % (key[0], key[1], a, b, len(ro), len(bo)))
                for r in ro[:40]:
                    print("      release-only %s" % (r,))
                for r in bo[:40]:
                    print("      build-only   %s" % (r,))
                if A.rules[A.ids.index(a)][0] in (5, 6) and not ro and not bo:
                    print("      same rules, different subtable ORDER or nesting")
    print("== REGISTRATION (script/lang/feature -> lookup identities)")
    keys = sorted(set(A.reg) | set(B.reg))
    nd = 0
    for key in keys:
        la, lb = A.reg.get(key), B.reg.get(key)
        if la == lb:
            continue
        nd += 1
        if la is None:
            print("   %-16s only in build  : %s" % ("/".join(key), lb))
        elif lb is None:
            print("   %-16s only in release: %s" % ("/".join(key), la))
        else:
            print("   %-16s release %s\n   %-16s build   %s" % ("/".join(key), la, "", lb))
    print("   %d keys, %d differ" % (len(keys), nd))
    print("== ORDER (per script/lang: the lookup sequence a shaper applies)")
    for key in sorted(set(A.seq) | set(B.seq)):
        qa, qb = A.seq.get(key), B.seq.get(key)
        if qa == qb:
            print("   %-10s same sequence of %d lookups" % ("/".join(key), len(qa)))
            continue
        if qa is None or qb is None:
            print("   %-10s present only in %s" % ("/".join(key), "build" if qa is None else "release"))
            continue
        ida, idb = [x for x, _ in qa], [x for x, _ in qb]
        if sorted(ida) == sorted(idb):
            print("   %-10s SAME lookups, DIFFERENT order:" % "/".join(key))
            print("      release %s" % [ft for _, ft in qa])
            print("      build   %s" % [ft for _, ft in qb])
        else:
            common_a = [x for x in qa if x[0] in idb]
            common_b = [x for x in qb if x[0] in ida]
            print("   %-10s different sets; release-only %s; build-only %s; common part in same order: %s"
                  % ("/".join(key), [ft for x, ft in qa if x not in idb],
                     [ft for x, ft in qb if x not in ida], common_a == common_b))


if __name__ == "__main__":
    main()
