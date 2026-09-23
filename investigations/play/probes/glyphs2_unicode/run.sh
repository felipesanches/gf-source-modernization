#!/bin/sh
# Question: does gftools-builder3 e851b8b map a Glyphs 2 source's unquoted, all-digit
# hex unicode (endash: `unicode = 2013;`) to U+2013 -- in the variable font (fontc's
# glyphs-reader) and in the static fonts (buildVariable false)? Also: are both static
# instances (Regular, Bold) produced? (The default config cannot be tested on this
# 2-glyph font: ttfautohint finds no style metrics, and e851b8b ignores autohintTTF.)
# Expected if correct: U+0041 and U+2013 everywhere. Suspected (glyphslib-rs
# CommaHexStringVisitor::visit_u64 formats the integer as hex, then parses it as hex,
# so 2013 stays decimal): U+07DD in whatever is read through glyphslib.
# Usage: sh run.sh [workdir]
set -u
H=$(cd "$(dirname "$0")" && pwd)
W=${1:-$(mktemp -d)}
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
cmaps() { for f in "$@"; do "$PY" -c "import sys; from fontTools.ttLib import TTFont; print(sys.argv[1].split('/')[-1], ' '.join('U+%04X' % c for c in sorted(TTFont(sys.argv[1]).getBestCmap())))" "$f"; done; }
for mode in variable statics; do
  rm -rf "$W/$mode"; mkdir -p "$W/$mode/sources"; cp "$H/sources/Min.glyphs" "$W/$mode/sources/"
  case $mode in
    statics) printf 'sources:\n  - Min.glyphs\nbuildVariable: false\n' ;;
    variable) printf 'sources:\n  - Min.glyphs\nbuildStatic: false\n' ;;
  esac > "$W/$mode/sources/config.yaml"
  (cd "$W/$mode" && "$B3" sources/config.yaml > build.log 2>&1); echo "== $mode (exit $?)"
  cmaps $(find "$W/$mode/fonts" -name '*.ttf' | sort)
done
echo "== babelfont (glyphslib) read, written back as Glyphs 3:"
"$BF" "$H/sources/Min.glyphs" "$W/min-g3.glyphs" >/dev/null 2>&1; grep -E "glyphname|unicode" "$W/min-g3.glyphs" | paste - - | sed 's/;//g'
