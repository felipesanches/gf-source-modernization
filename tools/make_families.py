#!/usr/bin/env python3
"""Write families.tsv: one row per shipped style this re-landing has to reproduce.

Question answered: for every style, WHICH repository it lands in, what the
unmodified base of that repository is, WHICH source file the style is converted
from, and WHICH shipped binary it must correspond to.

Every later step reads this table instead of re-deriving a pairing. Pairing is
where this programme's false findings have come from (see the memory note
"verify the pair before concluding"), so it is decided once, here, explicitly:

  * batch 6 -- the source each style was converted from is read from the
    batch-6 sweep log line "source for <style>: <path> (rule: ...)", which is
    the selection that sweep actually made. Nothing is re-guessed.
  * batch 7 -- the pipeline's rule: <Style>-TTF.sfd when that variant declares
    glyphs, else <Style>.sfd. Corben-Bold-TTF.sfd declares none, so Corben-Bold
    comes from Corben-Bold.sfd.

Columns:
  repo       googlefonts/<repo> the style lands in
  family     google/fonts family directory
  lic        ofl | apache | ufl
  kind       hg     fresh repository, base = monorepo subtree at `commit`
             fork   googlefonts fork, base = fork master = `commit`
             allerta  added to the existing googlefonts/allerta
             upstream no googlefonts repository yet
             glyphs   the source already is a .glyphs file: base = the upstream
                      repository whose history googlefonts/<repo> carries,
                      `commit` = its revision; no conversion (see GLYPHS below)
  base       where the unmodified files come from (archive slug)
  commit     the revision METADATA.pb records
  style      shipped style name (the .ttf basename)
  source     path of the source file inside the base tree
  shipped    absolute path of the released binary

Usage: tools/make_families.py > families.tsv
"""
import os
import re
import sys

GF = "/home/fsanches/compartilhado/google/fonts"
B6 = "/home/fsanches/compartilhado/sfd-batch6"

BATCH6 = """creepstercaps herrvonmuellerhoff kristi lekton miama monoton nixieone nosifer
nosifercaps novacut novaflat novamono novaoval novaround novascript novaslim
novasquare patrickhand play puritan russoone sixcaps smythe tuffy tulpenone
unifrakturcook unifrakturmaguntia""".split()

# googlefonts/<repo> differs from the family directory in one case: the
# repository created for UnifrakturMaguntia is named `unifraktur`.
REPO_NAME = {"unifrakturmaguntia": "unifraktur"}


# Families represented by an existing Glyphs source instead of a converted .sfd: the
# most faithful available source of what shipped (Felipe, 2026-10-01). Play ships
# v2.101, exported from alexeiva/play sources/Play.glyphs at d84ad58; the
# googlefontdirectory-hg .sfd are v1 (investigations/play/FINDINGS.md). METADATA.pb
# still records the hg commit, so the revision is given here, not read from it.
GLYPHS = {"play": ("alexeiva/play", "d84ad58f3a3bd2c735f431480f969283446b509f",
                   "sources/Play.glyphs")}


def metadata_commit(lic, fam):
    text = open(f"{GF}/{lic}/{fam}/METADATA.pb", encoding="utf-8").read()
    m = re.search(r'^\s*commit:\s*"([0-9a-f]{40})"', text, re.M)
    if not m:
        sys.exit(f"FATAL: no commit in {lic}/{fam}/METADATA.pb")
    return m.group(1)


def batch6_rows():
    work = {}
    for line in open(f"{B6}/worklist.tsv", encoding="utf-8"):
        cols = line.rstrip("\n").split("\t")
        if len(cols) >= 6:
            work[cols[4]] = (cols[0], cols[5])
    for fam in BATCH6:
        slug, lic = work[fam]
        commit = metadata_commit(lic, fam)
        log = open(f"{B6}/logs/{fam}.log", encoding="utf-8", errors="replace").read()
        pairs = sorted(set(re.findall(r"^source for (\S+): (\S.*?) \(rule:", log, re.M)))
        if not pairs:
            sys.exit(f"FATAL: no source-selection line in logs/{fam}.log")
        for style, src in pairs:
            shipped = f"{GF}/{lic}/{fam}/{style}.ttf"
            if not os.path.exists(shipped):
                sys.exit(f"FATAL: {fam}/{style}: no shipped binary at {shipped}")
            # the log path is relative to the monorepo root; the base tree is
            # the family's subtree, so strip "<lic>/<fam>/"
            prefix = f"{lic}/{fam}/"
            if not src.startswith(prefix):
                sys.exit(f"FATAL: {fam}/{style}: source {src} is outside {prefix}")
            if fam in GLYPHS:
                base, rev, gsrc = GLYPHS[fam]
                yield (REPO_NAME.get(fam, fam), fam, lic, "glyphs", base, rev,
                       style, gsrc, shipped)
                continue
            yield (REPO_NAME.get(fam, fam), fam, lic, "hg", slug, commit,
                   style, src[len(prefix):], shipped)


# batch 7: explicit, one row per shipped style
BATCH7 = [
    # repo, family, kind, base slug, style, source
    ("abrilfatface", "abrilfatface", "fork", "librefonts/abrilfatface",
     "AbrilFatface-Regular", "src/AbrilFatface-Regular-TTF.sfd"),
    ("corben", "corben", "fork", "librefonts/corben",
     "Corben-Regular", "src/Corben-Regular-TTF.sfd"),
    # Corben-Bold-TTF.sfd declares no glyphs at all (229 KB, 0 StartChar)
    ("corben", "corben", "fork", "librefonts/corben",
     "Corben-Bold", "src/Corben-Bold.sfd"),
    ("allerta", "allertastencil", "allerta", "librefonts/allerta",
     "AllertaStencil-Regular", "src/AllertaStencil-Regular-TTF.sfd"),
    ("comicrelief", "comicrelief", "upstream", "loudifier/Comic-Relief",
     "ComicRelief-Regular", "sources/ComicRelief-Regular.sfd"),
    ("comicrelief", "comicrelief", "upstream", "loudifier/Comic-Relief",
     "ComicRelief-Bold", "sources/ComicRelief-Bold.sfd"),
]


def batch7_rows():
    for repo, fam, kind, slug, style, src in BATCH7:
        lic = "ofl"
        yield (repo, fam, lic, kind, slug, metadata_commit(lic, fam),
               style, src, f"{GF}/{lic}/{fam}/{style}.ttf")


def main():
    print("\t".join(["repo", "family", "lic", "kind", "base", "commit",
                     "style", "source", "shipped"]))
    for row in list(batch6_rows()) + list(batch7_rows()):
        print("\t".join(row))


if __name__ == "__main__":
    main()
