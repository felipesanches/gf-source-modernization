#!/usr/bin/env python3
"""Does a GSUB difference change shaped text? (uharfbuzz over the cmap)

Question: the gate's GSUB rows can be pure structure (lookup order, subtable packing,
lookup type 5 vs 6) or a real behaviour change (a feature registered for a language
the source excluded, a lookup the release lacks). This shapes the same corpus with
both fonts under every (language system, feature) either font registers and reports
every run whose output differs (glyph NAMES + x advances; both fonts keep the
source's glyph names).

Corpus (text only -- a shaper reaches nothing that the cmap cannot):
  * every codepoint both fonts map, alone;
  * every pair of "rule" characters: codepoints whose glyph appears anywhere in either
    font's GSUB (input, coverage, class, backtrack, lookahead, ligature component);
  * every sequence a rule describes, expanded: ligature components; for contextual
    rules backtrack + input + lookahead with each position filled from its coverage /
    class by every mapped glyph (capped at 400 sequences per rule).
Features: the default set (nothing requested), then each GSUB feature tag of either
font switched on alone. Languages: every language system either font registers
(OpenType tag -> BCP 47 via TAGS below) under its script, plus no language.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 shape_compare.py \
        <release.ttf> <build.ttf> [--examples N]
Output: per (script, language, feature) the number of runs in which the feature FIRED in
the release (output differs from the same run with no feature requested; for "default",
from the plain cmap glyphs) -- so a "0 differ" is known to have exercised the feature --
and the number of runs whose GLYPHS differ (a GSUB
effect), with up to N examples each (default 3); runs whose glyphs agree and only x
advances differ are counted apart (ADVANCE-ONLY: a GDEF mark-class or GPOS matter, not
GSUB -- e.g. a combining mark the release classes as a base keeps its advance), then
    TOTAL <runs> runs, <glyph-diff> differ in glyphs, <adv> differ in advances only
"""
import itertools
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

TAGS = {"dflt": None, "ROM": "ro", "MOL": "ro-MD", "TRK": "tr", "AZE": "az", "CRT": "crh",
        "DEU": "de", "SRB": "sr-Latn", "NLD": "nl", "CAT": "ca", "PLK": "pl"}
SCRIPTS = {"latn": "Latn", "cyrl": "Cyrl", "grek": "Grek", "DFLT": None}


def gsub_glyphs(font):
    """Every glyph name that any GSUB rule mentions, and expanded rule sequences."""
    names, seqs = set(), []
    if "GSUB" not in font:
        return names, seqs
    for lk in font["GSUB"].table.LookupList.Lookup:
        sts = list(lk.SubTable)
        if lk.LookupType == 7:
            sts = [s.ExtSubTable for s in sts]
        for st in sts:
            for a, b in (getattr(st, "mapping", None) or {}).items():
                names.add(a)
                names.update(b if isinstance(b, list) else [b])
            for a, alts in (getattr(st, "alternates", None) or {}).items():
                names.add(a)
                names.update(alts)
            for a, ligs in (getattr(st, "ligatures", None) or {}).items():
                for lg in ligs:
                    seq = [[a]] + [[c] for c in lg.Component]
                    seqs.append(seq)
                    names.update([a] + list(lg.Component))
            fmt = getattr(st, "Format", None)
            if fmt == 3:
                pos = []
                for attr in ("BacktrackCoverage", "InputCoverage", "LookAheadCoverage", "Coverage"):
                    cs = getattr(st, attr, None)
                    if cs is None:
                        continue
                    cs = cs if isinstance(cs, list) else [cs]
                    glist = [list(c.glyphs) for c in cs]
                    if attr == "BacktrackCoverage":
                        glist = glist[::-1]
                    pos += glist
                    for g in glist:
                        names.update(g)
                seqs.append(pos)
            elif fmt in (1, 2):
                cov = list(st.Coverage.glyphs)
                names.update(cov)
                for attr in ("BacktrackClassDef", "InputClassDef", "LookAheadClassDef", "ClassDef"):
                    cd = getattr(st, attr, None)
                    if cd is not None:
                        names.update(cd.classDefs)
                for attr in ("ChainSubRuleSet", "SubRuleSet"):
                    for gi, rs in enumerate(getattr(st, attr, None) or []):
                        for r in (getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None) or []):
                            seq = [[g] for g in reversed(getattr(r, "Backtrack", []))] + [[cov[gi]]] + \
                                  [[g] for g in r.Input] + [[g] for g in getattr(r, "LookAhead", [])]
                            seqs.append(seq)
                if fmt == 2:
                    def members(cd, c, restrict=None):
                        if cd is None:
                            return []
                        m = [g for g, k in cd.classDefs.items() if k == c]
                        return [g for g in m if (restrict is None or g in restrict)]
                    bc = getattr(st, "BacktrackClassDef", None)
                    ic = getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None)
                    lc = getattr(st, "LookAheadClassDef", None)
                    for attr in ("ChainSubClassSet", "SubClassSet"):
                        for ci, cs in enumerate(getattr(st, attr, None) or []):
                            if cs is None:
                                continue
                            first = members(ic, ci, set(cov)) if ci else [g for g in cov if g not in (ic.classDefs if ic else {})]
                            for r in (getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None) or []):
                                inp = list(getattr(r, "Input", None) or getattr(r, "Class", []))
                                seq = [members(bc, c) for c in reversed(getattr(r, "Backtrack", []))] + [first] + \
                                      [members(ic, c) for c in inp] + [members(lc, c) for c in getattr(r, "LookAhead", [])]
                                seqs.append(seq)
    return names, seqs


def langsystems(font):
    out = set()
    for tag in ("GSUB", "GPOS"):
        if tag not in font or not font[tag].table.ScriptList:
            continue
        t = font[tag].table
        for sr in t.ScriptList.ScriptRecord:
            if sr.Script.DefaultLangSys is not None:
                out.add((sr.ScriptTag, "dflt"))
            for lr in sr.Script.LangSysRecord:
                out.add((sr.ScriptTag, lr.LangSysTag.strip()))
    return out


def features(font):
    if "GSUB" not in font:
        return set()
    return {fr.FeatureTag for fr in font["GSUB"].table.FeatureList.FeatureRecord}


def main():
    rel, bld = sys.argv[1], sys.argv[2]
    nex = int(sys.argv[sys.argv.index("--examples") + 1]) if "--examples" in sys.argv else 3
    R, B = TTFont(rel), TTFont(bld)
    rc, bc = R.getBestCmap(), B.getBestCmap()
    shared = sorted(set(rc) & set(bc))
    rev = {}
    for c in shared:
        rev.setdefault(rc[c], c)
    names_r, seqs_r = gsub_glyphs(R)
    names_b, seqs_b = gsub_glyphs(B)
    rule_cps = sorted({rev[n] for n in (names_r | names_b) if n in rev})
    corpus = set(chr(c) for c in shared)
    corpus.update(a + b for a, b in itertools.product([chr(c) for c in rule_cps], repeat=2))
    for seq in seqs_r + seqs_b:
        opts = [[chr(rev[g]) for g in pos if g in rev] for pos in seq]
        if not opts or any(not o for o in opts):
            continue
        for n, combo in enumerate(itertools.product(*opts)):
            if n >= 400:
                break
            corpus.add("".join(combo))
    corpus = sorted(corpus)
    systems = sorted(langsystems(R) | langsystems(B))
    feats = sorted(features(R) | features(B))
    fr = hb.Font(hb.Face(hb.Blob.from_file_path(rel)))
    fb = hb.Font(hb.Face(hb.Blob.from_file_path(bld)))
    ro, bo = R.getGlyphOrder(), B.getGlyphOrder()

    def run(font, order, text, feat, script, lang):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        if lang:
            buf.language = lang
        hb.shape(font, buf, feat)
        return [(order[i.codepoint], p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    total = diff = advonly = 0
    adv_glyphs = set()
    print("corpus: %d strings (%d shared codepoints, %d rule characters); %d language systems; "
          "features: default + %s" % (len(corpus), len(shared), len(rule_cps), len(systems), " ".join(feats)))
    for script, lang in [(None, None)] + systems:
        if lang is not None and lang not in TAGS:
            print("   (no BCP47 mapping for %s/%s; skipped)" % (script, lang))
            continue
        hscript = SCRIPTS.get(script) if script else None
        hlang = TAGS.get(lang) if lang else None
        base = {}
        for feat in [None] + feats:
            fdict = {feat: True} if feat else {}
            n = d = fired = 0
            ex = []
            for text in corpus:
                n += 1
                a = run(fr, ro, text, fdict, hscript, hlang)
                b = run(fb, bo, text, fdict, hscript, hlang)
                if feat is None:
                    base[text] = a
                    naive = [rc[ord(ch)] for ch in text]
                    fired += [g for g, _ in a] != naive
                else:
                    fired += a != base[text]
                if a == b:
                    continue
                if [g for g, _ in a] == [g for g, _ in b]:
                    advonly += 1
                    adv_glyphs.update(g for (g, x), (_, y) in zip(a, b) if x != y)
                    continue
                d += 1
                if len(ex) < nex:
                    ex.append("%r release=%s build=%s" % (text, [g for g, _ in a], [g for g, _ in b]))
            total += n
            diff += d
            print("%s/%s %s: fired in %d of %d runs; %d differ in glyphs" % (
                script or "-", lang or "-", feat or "default", fired, n, d))
            for e in ex:
                print("      %s" % e)
    if advonly:
        print("ADVANCE-ONLY %d runs (same glyphs, different x advance), at glyphs %s"
              % (advonly, " ".join(sorted(adv_glyphs))))
    print("TOTAL %d runs, %d differ in glyphs, %d differ in advances only" % (total, diff, advonly))

if __name__ == "__main__":
    main()
