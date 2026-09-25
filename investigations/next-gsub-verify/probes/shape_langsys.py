#!/usr/bin/env python3
"""Question: shaped with HarfBuzz, does the build substitute exactly as the release
does, under EVERY language system either font declares, feature by feature?

Written independently of investigations/next-gsub/probes/shape_compare.py.

Language systems are forced with HarfBuzz's private-use language tag
`x-hbot<TAG>` (hb-ot-tag.cc parse_private_use_subtag), so AZE/CRT/MOL/SRB/TRK are
selected exactly, not through a BCP-47 guess. Script comes from the text (Latin,
plus Cyrillic/Greek samples when the fonts declare cyrl/grek).

Corpus (per font pair): every codepoint both fonts map, alone; every 2-gram over the
"layout alphabet" (codepoints whose glyph appears in any GSUB rule of either font,
capped); every 3-gram over a fixed figures/ordinal/ligature alphabet
(0-9 / U+2044 . a o f i l j t b h k c s); and every ligature's component sequence
spelled in codepoints when all components are encoded.

For each language system L and each feature F of either font: shape with {F: on}
(HarfBuzz defaults otherwise), and once with every feature on. Compares glyph NAMES
and advances. Prints per (L, F): runs, differing runs, runs where F changed the
output in the release (so a 0-difference result is not vacuous), and up to 3 examples.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY shape_langsys.py <release.ttf> <build.ttf> [--max-alpha N]
"""
import itertools
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def cmap(f):
    return f.getBestCmap() or {}


def rule_glyphs(f):
    out = set()
    if "GSUB" not in f:
        return out
    for lk in f["GSUB"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if lk.LookupType == 7:
                st = st.ExtSubTable
            for attr in ("mapping", "alternates", "ligatures"):
                d = getattr(st, attr, None)
                if d:
                    out.update(d)
                    if attr == "ligatures":
                        for ligs in d.values():
                            for l in ligs:
                                out.update(l.Component)
            for attr in ("Coverage", "BacktrackCoverage", "InputCoverage", "LookAheadCoverage"):
                c = getattr(st, attr, None)
                if c is None:
                    continue
                for cc in (c if isinstance(c, list) else [c]):
                    if cc is not None and getattr(cc, "glyphs", None):
                        out.update(cc.glyphs)
    return out


def langsys_tags(f):
    tags = set()
    for tag in ("GSUB", "GPOS"):
        if tag in f and f[tag].table.ScriptList:
            for sr in f[tag].table.ScriptList.ScriptRecord:
                for lr in sr.Script.LangSysRecord:
                    tags.add((sr.ScriptTag, lr.LangSysTag))
                tags.add((sr.ScriptTag, "dflt"))
    return tags


def features(f):
    fs = set()
    for tag in ("GSUB", "GPOS"):
        if tag in f and f[tag].table.FeatureList:
            fs.update(fr.FeatureTag for fr in f[tag].table.FeatureList.FeatureRecord)
    return fs


def main():
    rel, bld = sys.argv[1], sys.argv[2]
    max_alpha = 120
    if "--max-alpha" in sys.argv:
        max_alpha = int(sys.argv[sys.argv.index("--max-alpha") + 1])
    R, B = TTFont(rel), TTFont(bld)
    rc, bc = cmap(R), cmap(B)
    shared = sorted(set(rc) & set(bc))
    rev = {}
    for cp in shared:
        rev.setdefault(rc[cp], cp)
    layout = sorted({rev[g] for g in (rule_glyphs(R) | rule_glyphs(B)) if g in rev})
    alpha = layout[:max_alpha]
    words = set(chr(c) for c in shared)
    words |= {a + b for a, b in itertools.product([chr(c) for c in alpha], repeat=2)}
    fixed = [c for c in "0123456789/⁄.aofiljtbhkcs" if ord(c) in rc and ord(c) in bc]
    words |= {"".join(p) for p in itertools.product(fixed, repeat=3)}
    for f in (R, B):
        if "GSUB" in f:
            for lk in f["GSUB"].table.LookupList.Lookup:
                if lk.LookupType != 4:
                    continue
                for st in lk.SubTable:
                    for first, ligs in st.ligatures.items():
                        for l in ligs:
                            seq = [first] + list(l.Component)
                            if all(g in rev for g in seq):
                                words.add("".join(chr(rev[g]) for g in seq))
    # a few longer strings that exercise fraction / ordinal contexts
    words |= {"1/2", "12/34", "123/456", "1⁄2", "10/20 3/4", "1a", "2o", "1.a", "10.o",
              "office", "affluent", "fjord", "ffi", "fi", "fl", "ffl", "Tiit", "i̇"}
    words = sorted(words)
    fr = hb.Font(hb.Face(hb.Blob.from_file_path(rel)))
    fb = hb.Font(hb.Face(hb.Blob.from_file_path(bld)))
    rorder, border = R.getGlyphOrder(), B.getGlyphOrder()

    def shape(font, order, text, feats, lang, script=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        if lang is not None:
            buf.language = lang
        hb.shape(font, buf, feats)
        return tuple((order[i.codepoint], p.x_advance)
                     for i, p in zip(buf.glyph_infos, buf.glyph_positions))

    systems = sorted(langsys_tags(R) | langsys_tags(B))
    feats = sorted(features(R) | features(B))
    print("release %s\nbuild   %s" % (rel, bld))
    print("language systems:", ["%s/%s" % s for s in systems])
    print("features:", feats)
    print("corpus: %d strings (layout alphabet %d of %d codepoints)" % (len(words), len(alpha), len(layout)))
    total = diff_total = 0
    for script, lang in systems:
        sc = {"latn": "Latn", "cyrl": "Cyrl", "grek": "Grek", "DFLT": None}.get(script.strip(), None)
        lang_tag = None if lang.strip() == "dflt" else "x-hbot" + lang.strip()
        for feat in feats + ["*ALL*"]:
            on = {t: True for t in feats} if feat == "*ALL*" else {feat: True}
            n = nd = fired = 0
            ex = []
            for w in words:
                a = shape(fr, rorder, w, on, lang_tag, sc)
                b = shape(fb, border, w, on, lang_tag, sc)
                n += 1
                if a != b:
                    nd += 1
                    if len(ex) < 3:
                        ex.append((w, a, b))
                if feat != "*ALL*" and shape(fr, rorder, w, {}, lang_tag, sc) != a:
                    fired += 1
            total += n
            diff_total += nd
            if nd or feat == "*ALL*":
                print("%s/%s %-5s runs %d differ %d fired-in-release %d" % (script, lang.strip(), feat, n, nd, fired))
                for w, a, b in ex:
                    print("    %r release %s" % (w, [g for g, _ in a]))
                    print("    %r build   %s" % (w, [g for g, _ in b]))
    print("TOTAL runs %d, differing %d" % (total, diff_total))


if __name__ == "__main__":
    main()
