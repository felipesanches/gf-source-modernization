#!/usr/bin/env python3
"""Varela's GSUB rows: which language-specific substitutions differ from the release?

Question: the gate's lookup-order arbitration refuses Varela's GSUB rows. langsys_lookups.py
shows three registration differences (liga and smcp for AZE/CRT/TRK inherit latn/dflt
lookups through FEA include_dflt; aalt is registered for latn/SRB) and one packing
difference (the ordn chaining lookup has 4 subtables in the release, 2 in ours). Which of
them change shaped text, and does babelfont emitting `language XXX exclude_dflt;` fix the
first two?

Signal read: HarfBuzz glyph names (ltr, script Latn) for targeted texts, per language
(OpenType language via BCP47: tr=TRK, az=AZE, crh=CRT, ro=ROM, mo->ROM/MOL, sr=SRB,
de=DEU), with the features named in each case switched on:
  liga      'fi' 'fl' 'ffi' 'office'                       (Turkish must NOT ligate fi)
  smcp      'i' 'I' 'istanbul'                              (Turkish i -> idotaccent.smcp)
  ordn      '1a' '2o' '1.a' '2.o' '12a' 'a1a'              (4 vs 2 subtables)
  aalt      '!' 'a' 'S'                                     (only in candidate for sr)

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 varela_gsub_check.py \
        <release.ttf> <candidate.ttf> [<candidate2.ttf> ...]
"""
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

CASES = [
    ("liga", {}, ["fi", "fl", "ffi", "ffl", "office", "fifi"]),
    ("smcp", {"smcp": True}, ["i", "I", "istanbul", "fi"]),
    ("ordn", {"ordn": True}, ["1a", "2o", "1.a", "2.o", "12a", "a1a", "1.o.a"]),
    ("aalt", {"aalt": True}, ["!", "a", "S", "?"]),
]
LANGS = [None, "tr", "az", "crh", "ro", "mo", "sr", "de", "en"]


def shape(path, names, text, lang, feats):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if lang:
        buf.language = lang
    hb.shape(font, buf, feats)
    return [names[i.codepoint] for i in buf.glyph_infos]


def main():
    rel, cands = sys.argv[1], sys.argv[2:]
    rn = TTFont(rel).getGlyphOrder()
    for cand in cands:
        cn = TTFont(cand).getGlyphOrder()
        n = diff = 0
        per = {}
        for label, feats, texts in CASES:
            for lang in LANGS:
                for t in texts:
                    n += 1
                    a = shape(rel, rn, t, lang, feats)
                    b = shape(cand, cn, t, lang, feats)
                    if a != b:
                        diff += 1
                        per.setdefault(label, []).append((lang, t, a, b))
        print("%s: %d cases, %d differ" % (cand.rsplit("/", 2)[-3:], n, diff))
        for label, rows in per.items():
            print("  %s: %d" % (label, len(rows)))
            for lang, t, a, b in rows[:4]:
                print("    lang=%s %r release=%s cand=%s" % (lang, t, a, b))


if __name__ == "__main__":
    main()
