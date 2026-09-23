#!/bin/sh
# Questions answered (conversion only, no build), for both converter builds
# (f725e6a = target/release, ca43adc = target-heights/release):
#  1. Do --fontforge-os2-defaults / --snap-component-transforms change the ComicRelief
#     conversion at all?  (cmp of .glyphs: "no-op" = byte-identical)
#  2. What does --fontforge-underline-position change?  (expect -185 -> -272)
#  3. Does the SIM-upos-97 copy differ from the unmodified conversion ONLY in
#     underlinePosition?  (expect one changed line, "value = -97")
# Usage: sh verify/probes/conv_checks.sh   (after make_edits.sh)
set -eu
E=/home/fsanches/compartilhado/sfd-reland/investigations/small/verify/edits
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-small-verify/conv; mkdir -p $S
PRE="--add-instance-per-master --infer-mark-category --set-subcategory --keep-source-glyph-names --keep-source-advances"
POST="--reverse-path-direction --add-legacy-duplicate-cmap"
for bf in target target-heights; do
  BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/$bf/release/babelfont
  for s in Regular Bold; do
    o=$E/ComicRelief-$s.orig.sfd
    $BF $o $S/$bf-$s-all.glyphs --fontforge-os2-defaults $PRE --snap-component-transforms $POST 2>/dev/null
    $BF $o $S/$bf-$s-noos2.glyphs $PRE --snap-component-transforms $POST 2>/dev/null
    $BF $o $S/$bf-$s-nosnap.glyphs --fontforge-os2-defaults $PRE $POST 2>/dev/null
    $BF $o $S/$bf-$s-ul.glyphs --fontforge-os2-defaults $PRE --snap-component-transforms --fontforge-underline-position $POST 2>/dev/null
    $BF $E/ComicRelief-$s.SIM-upos-97.sfd $S/$bf-$s-sim.glyphs --fontforge-os2-defaults $PRE --snap-component-transforms $POST 2>/dev/null
    echo "$bf $s: os2-defaults $(cmp -s $S/$bf-$s-all.glyphs $S/$bf-$s-noos2.glyphs && echo no-op || echo CHANGES);" \
         "snap $(cmp -s $S/$bf-$s-all.glyphs $S/$bf-$s-nosnap.glyphs && echo no-op || echo CHANGES);" \
         "ff-underline: $(diff $S/$bf-$s-all.glyphs $S/$bf-$s-ul.glyphs | grep '^[<>]' | tr '\n' ' ');" \
         "sim vs unmodified: $(diff $S/$bf-$s-all.glyphs $S/$bf-$s-sim.glyphs | grep -c '^[<>]') lines, $(diff $S/$bf-$s-all.glyphs $S/$bf-$s-sim.glyphs | grep '^>' | tr '\n' ' ')"
  done
done
