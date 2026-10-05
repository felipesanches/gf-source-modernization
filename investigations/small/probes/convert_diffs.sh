#!/bin/sh
# Questions answered (conversion only, no build):
#  1. Is the ComicRelief "sim-97" copy a faithful stand-in for the proposed
#     converter rule? Converting it WITHOUT --fontforge-underline-position must
#     differ from converting the unmodified .sfd only in the underlinePosition
#     value (-185 -> -97). If so, runs/comicrelief-*-sim97 measure exactly what
#     the proposed filter would hand fontc.
#  2. Do the FontForge-exporter flags --fontforge-os2-defaults and
#     --snap-component-transforms change anything for ComicRelief (a release
#     FontForge did not export)? Byte-identical .glyphs = no effect.
#
# Usage: sh probes/convert_diffs.sh [babelfont-binary] [scratch-dir]
# Expected: "only underlinePosition differs" x2, "no-op" x4.
set -eu
BF=${1:-/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target/release/babelfont}
D=${2:-/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-small/convdiff}
E=/home/fsanches/compartilhado/gf-source-modernization/investigations/small/edits
A=/home/fsanches/compartilhado/upstream_repos/repo_archive/loudifier/Comic-Relief.git
C=856315f5a45dfdad75090e4454f1ebfd019296b9
mkdir -p "$D"
# the recipe baseline.sh gives ComicRelief, minus the two flags under test
PRE="--add-instance-per-master --infer-mark-category --set-subcategory --keep-source-glyph-names --keep-source-advances"
POST="--reverse-path-direction --add-legacy-duplicate-cmap"   # same order as baseline.sh
for s in Regular Bold; do
  git -C "$A" show "$C:sources/ComicRelief-$s.sfd" > "$D/CR-$s.sfd"
  [ -s "$E/ComicRelief-$s.upos-sim-97.sfd" ] || { echo "run probes/make_edits.sh first" >&2; exit 1; }
  "$BF" "$D/CR-$s.sfd" "$D/$s-noflag.glyphs" --fontforge-os2-defaults $PRE --snap-component-transforms $POST 2>/dev/null
  "$BF" "$E/ComicRelief-$s.upos-sim-97.sfd" "$D/$s-sim97.glyphs" --fontforge-os2-defaults $PRE --snap-component-transforms $POST 2>/dev/null
  n=$(diff "$D/$s-noflag.glyphs" "$D/$s-sim97.glyphs" | grep -c '^[<>]' || true)
  ctx=$(diff "$D/$s-noflag.glyphs" "$D/$s-sim97.glyphs" | grep '^[<>]' | tr '\n' ' ')
  line=$(diff "$D/$s-noflag.glyphs" "$D/$s-sim97.glyphs" | sed -n 's/^\([0-9]*\)c.*/\1/p')
  prev=$(sed -n "$((line - 1))p" "$D/$s-noflag.glyphs")
  if [ "$n" = 2 ] && [ "$prev" = "name = underlinePosition;" ]; then
    echo "$s: only underlinePosition differs ($ctx)"
  else
    echo "$s: UNEXPECTED diff ($n lines): $ctx"
  fi
  "$BF" "$D/CR-$s.sfd" "$D/$s-noos2.glyphs" $PRE --snap-component-transforms $POST 2>/dev/null
  cmp -s "$D/$s-noflag.glyphs" "$D/$s-noos2.glyphs" && echo "$s: --fontforge-os2-defaults no-op" || echo "$s: --fontforge-os2-defaults CHANGES the conversion"
  "$BF" "$D/CR-$s.sfd" "$D/$s-nosnap.glyphs" --fontforge-os2-defaults $PRE $POST 2>/dev/null
  cmp -s "$D/$s-noflag.glyphs" "$D/$s-nosnap.glyphs" && echo "$s: --snap-component-transforms no-op" || echo "$s: --snap-component-transforms CHANGES the conversion"
done
