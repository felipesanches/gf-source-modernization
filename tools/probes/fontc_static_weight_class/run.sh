#!/bin/sh
# Question answered: does fontc give a static, single-master Glyphs source the OS/2
# usWeightClass its instance states, the way fontmake does?
#
# sources/WeightClass.glyphs: one master, one instance "Bold" with weightClass = 700.
# Expected (and EXPECTED.txt, 2026-09-23):
#   fontmake 3.11.1 (glyphsLib)                  usWeightClass=700
#   fontc 1.0.0 via gftools-builder3 e851b8b     usWeightClass=400
# fontbe/src/os2.rs takes usWeightClass from a 'wght' axis default, else from
# static metadata, else 400; for a Glyphs source nothing sets the static metadata,
# and a single master has no axis -- so the instance's weightClass is never read.
set -eu
cd "$(dirname "$0")"
rm -rf fonts fontmake-out
/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder sources/config.yaml >/dev/null 2>&1
/home/fsanches/compartilhado/gftools/venv/bin/fontmake -g sources/WeightClass.glyphs -i -o ttf --output-dir fontmake-out >/dev/null 2>&1
/home/fsanches/compartilhado/gftools/venv/bin/python3 - <<'PY'
from fontTools.ttLib import TTFont
for label, p in (("fontmake", "fontmake-out/WeightClassProbe-Bold.ttf"),
                 ("fontc", "fonts/ttf/WeightClassProbe-Bold.ttf")):
    print("%-9s usWeightClass=%d" % (label, TTFont(p)["OS/2"].usWeightClass))
PY
rm -rf fonts fontmake-out instance_ufo master_ufo
