#!/bin/bash
# VERIFY COPY of investigations/next-provenance/probes/thabit_pipeline.sh: identical steps, but
# scratch under sfd-reland-scratch/provenance-verify, outputs under
# investigations/next-provenance-verify/runs/<name>, the AFMs fetched independently into
# <scratch>/xorg (sha1 in runs/<name>/inputs.sha1), BF defaulting to the verifier's own build.
# Optional DROP_NBSP=1 removes the 2010-save glyph uni00A0 before the build steps.
# Question answered: if every step of Thabit's build script (hg 52f780b ofl/thabit/src/
# build.py; helper.py in the 0.02 release's ChangeLog) is written into the .sfd as a
# documented edit, and the converter carries the FontForge-exporter rules this unit
# found, which table rows and which rendering differences remain against the four
# binaries Google Fonts ships (google/fonts b5efa9c32e8f ofl/thabit/*.ttf)?
#
# Steps per style (probes/ff_build_ops.py; each op cites the FontForge 2008 code it follows):
#   upright : mergefea Thabit.fea -> mergepsfont cour{,b}.pfa + .afm -> ffnotdef (emulation)
#   oblique : obliqize -16 rad (U+200C..U+202E kept upright) -> pastepsglyphs upright Courier
#             ( ) [ ] { } ! -> mergefea -> mergepsfont cour{i,bi}.pfa + .afm -> ffnotdef
# then tools/baseline.sh with the prototype converter (BF, default: the scratch build of
# babelfont 17ea899 + probes/babelfont-prototype-all5.patch) and EXTRA_FLAGS, then
# probes/rebuild_with_workarounds.sh (land.py's usWeightClass workaround), then
# probes/d3_render.py on the rendering diff.
#
# Inputs: the hg monorepo at 52f780b (sources, Thabit.fea, cour/*.pfa) from the repo
# archive, and the IBM Courier AFMs, which the hg tree lacks: X.Org font-ibm-type1 at
# 88a51daabc8a5bf2dbb2ace89c638058b01b3cf3 (its cour*.pfa are byte-identical to hg's;
# fetched from https://gitlab.freedesktop.org/xorg/font/ibm-type1/-/raw/<rev>/<file>).
#
# Usage: thabit_pipeline.sh <run-name> ["<extra babelfont flags>"]
# e.g.   thabit_pipeline.sh p1 "--fontforge-implied-oncurves --fontforge-rint-coordinates"
set -euo pipefail
name=$1; extra=${2:-}
W=/home/fsanches/compartilhado/sfd-reland
I=$W/investigations/next-provenance
VV=$W/investigations/next-provenance-verify
S=/home/fsanches/compartilhado/sfd-reland-scratch/provenance-verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
HG=52f780bc9d197280a9f430574e179a5f233c56b6
XORG=88a51daabc8a5bf2dbb2ace89c638058b01b3cf3
BF=${BF:-$S/target-bf/release/babelfont}
GF=/home/fsanches/compartilhado/google/fonts/ofl/thabit
src=$S/pipeline-$name; out=$VV/runs/$name
rm -rf "$src"; mkdir -p "$src/cour" "$out"
for f in Thabit.sfd Thabit-Bold.sfd Thabit.fea; do git -C "$ARC" show "$HG:ofl/thabit/src/$f" > "$src/$f"; done
if [ "${DROP_NBSP:-0}" = 1 ]; then
  # Candidate documented edit (verifier): delete the empty uni00A0 glyph, the LAST glyph
  # of both .sfd files (gid 307 / 309, nothing refers to it), which the 2010 save carries
  # and the 2008 release neither encodes nor contains. FATAL if it is not the last glyph.
  for f in Thabit.sfd Thabit-Bold.sfd; do
    "$PY" - "$src/$f" <<'PYEOF'
import re, sys
p = sys.argv[1]; t = open(p, encoding="utf-8", errors="surrogateescape").read()
blocks = list(re.finditer(r"^StartChar: ([^\n]*)\n.*?^EndChar\n\n?", t, re.M | re.S))
last = blocks[-1]
if last.group(1) != "uni00A0" or not re.search(r"^Encoding: 160 160 %d$" % (len(blocks) - 1), last.group(0), re.M):
    sys.exit("FATAL: uni00A0 is not the last glyph of %s" % p)
if re.search(r"^Refer: %d " % (len(blocks) - 1), t, re.M):
    sys.exit("FATAL: something refers to uni00A0")
t = t[:last.start()] + t[last.end():]
t = re.sub(r"^BeginChars: (\d+) (\d+)$", lambda m: "BeginChars: %s %d" % (m.group(1), int(m.group(2)) - 1), t, count=1, flags=re.M)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
print("dropped uni00A0 from", p)
PYEOF
  done
fi
for f in cour courb couri courbi; do
  git -C "$ARC" show "$HG:ofl/thabit/src/cour/$f.pfa" > "$src/cour/$f.pfa"
  true \
      ;
  cp "$S/xorg/$f.afm" "$src/cour/$f.afm"
done
sha1sum "$src"/cour/* > "$out/inputs.sha1"
ops() { "$PY" "$I/probes/ff_build_ops.py" "$@"; }
ops "$src/Thabit.sfd" "$src/Thabit.gen.sfd" mergefea "$src/Thabit.fea" -- mergepsfont "$src/cour/cour.pfa" "$src/cour/cour.afm" Courier -- ffnotdef > "$out/Thabit.ops.txt"
ops "$src/Thabit-Bold.sfd" "$src/Thabit-Bold.gen.sfd" mergefea "$src/Thabit.fea" -- mergepsfont "$src/cour/courb.pfa" "$src/cour/courb.afm" Courier-Bold -- ffnotdef > "$out/Thabit-Bold.ops.txt"
ops "$src/Thabit.sfd" "$src/Thabit-Oblique.gen.sfd" obliqize -16 200C 202E -- pastepsglyphs "$src/cour/cour.pfa" parenleft parenright exclam bracketleft bracketright braceleft braceright -- mergefea "$src/Thabit.fea" -- mergepsfont "$src/cour/couri.pfa" "$src/cour/couri.afm" Courier-Italic -- ffnotdef > "$out/Thabit-Oblique.ops.txt"
ops "$src/Thabit-Bold.sfd" "$src/Thabit-BoldOblique.gen.sfd" obliqize -16 200C 202E -- pastepsglyphs "$src/cour/courb.pfa" parenleft parenright exclam bracketleft bracketright braceleft braceright -- mergefea "$src/Thabit.fea" -- mergepsfont "$src/cour/courbi.pfa" "$src/cour/courbi.afm" Courier-BoldItalic -- ffnotdef > "$out/Thabit-BoldOblique.ops.txt"
# pairing: the paired uprights from families-next.tsv, the obliques added the same way
fam=$out/families.tsv
head -1 "$W/families-next.tsv" > "$fam"
grep -P '\tThabit(-Bold)?\t' "$W/families-next.tsv" >> "$fam"
grep -P '\tThabit\t' "$W/families-next.tsv" | awk -F'\t' -v gf="$GF" 'BEGIN{OFS="\t"}{$7="Thabit-Oblique"; $9=gf"/Thabit-Oblique.ttf"; print}' >> "$fam"
grep -P '\tThabit-Bold\t' "$W/families-next.tsv" | awk -F'\t' -v gf="$GF" 'BEGIN{OFS="\t"}{$7="Thabit-BoldOblique"; $9=gf"/Thabit-BoldOblique.ttf"; print}' >> "$fam"
for st in Thabit Thabit-Bold Thabit-Oblique Thabit-BoldOblique; do
  ( FAMILIES="$fam" BF="$BF" SRC_OVERRIDE="$src/$st.gen.sfd" EXTRA_FLAGS="$extra" OUT="$out" TAG="$name" SCRATCH="$S" \
      bash "$W/tools/baseline.sh" "$st" > /dev/null ) &
  [ "$st" = Thabit-Bold ] && wait
done
wait
for st in Thabit Thabit-Bold Thabit-Oblique Thabit-BoldOblique; do
  case $st in Thabit|Thabit-Oblique) sp=src/Thabit.sfd;; *) sp=src/Thabit-Bold.sfd;; esac
  bash "$I/probes/rebuild_with_workarounds.sh" "$S/baseline/$st-$name" "$st" "$sp" "$GF/$st.ttf" "$out/workarounds" > /dev/null
  printf '%s\ttable rows %s (harness) -> %s (with land.py workarounds)\t' "$st" \
    "$(cut -f4 "$out/$st.tsv")" "$(grep -c '^ *BLOCKING' "$out/workarounds/$st.gate.txt")"
  "$PY" "$I/probes/d3_render.py" "$S/baseline/$st-$name-workarounds/d3.json" --list 3 | tr '\n' ' '; echo
done | tee "$out/SUMMARY.txt"
