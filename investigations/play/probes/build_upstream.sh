#!/bin/sh
# Question: does alexeiva/play's own source (sources/Play.glyphs at v2.101 = d84ad58)
# build with gftools-builder3 e851b8b (fontc 1.0.0)? That decides whether
# googlefonts/play can be alexeiva/play's history plus a build config alone.
#
# Three runs, each printed with its outcome:
#   1. as is, default config (variable + statics)
#   2. the same, with ringcomb.case's anchors removed (a PROBE, not a fix): lists the
#      glyphs fontc then reports as interpolation-incompatible
#   3. as 2, with buildVariable: false: which static fonts come out
# Then, for any static produced, the table gate and cmap against the Play google/fonts
# ships (b5efa9c32e8f).
#
# Usage: sh build_upstream.sh [workdir]      (default: a new mktemp -d)
set -u
W=${1:-$(mktemp -d)}
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/alexeiva/play.git
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
GF=/home/fsanches/compartilhado/google/fonts/ofl/play
P="$W/play"
rm -rf "$P"
git clone -q "$ARC" "$P" && git -C "$P" checkout -q d84ad58

build() {  # $1 = label
  (cd "$P" && rm -rf fonts && "$B3" sources/config.yaml > "$W/$1.log" 2>&1)
  echo "== run $1: exit $?; built: $(ls "$P"/fonts/ttf 2>/dev/null | tr '\n' ' ')"
  tail -1 "$W/$1.log" | cut -c1-300
}

printf 'sources:\n  - Play.glyphs\n' > "$P/sources/config.yaml"
build 1-as-is

"$PY" - "$P/sources/Play.glyphs" <<'EOF'
import re, sys
p = sys.argv[1]
t = open(p, encoding="utf-8").read()
i = t.index("glyphname = ringcomb.case;"); j = t.index("\nglyphname = ", i + 10)
open(p, "w", encoding="utf-8").write(t[:i] + re.sub(r"\nanchors = \(\n.*?\n\);", "", t[i:j], flags=re.S) + t[j:])
EOF
build 2-no-ringcomb-anchors
echo "interpolation-incompatible glyphs: $(grep -oE "'[^']+' has interpolation-incompatible" "$W/2-no-ringcomb-anchors.log" | sort -u | wc -l)"
grep -oE "'[^']+' has interpolation-incompatible" "$W/2-no-ringcomb-anchors.log" | sort -u | cut -d"'" -f2 | tr '\n' ' '; echo

printf 'sources:\n  - Play.glyphs\nbuildVariable: false\n' > "$P/sources/config.yaml"
build 3-statics-only

for s in Regular Bold; do
  built="$P/fonts/ttf/Play-$s.ttf"
  [ -f "$built" ] || { echo "Play-$s: not built"; continue; }
  "$D3" -J 1 --no-languages --no-match --json --succinct "$GF/Play-$s.ttf" "$built" > "$W/d3-$s.json" 2>/dev/null
  echo "== gate Play-$s"
  "$PY" "$TG" "$W/d3-$s.json" --fonts "$GF/Play-$s.ttf" "$built" | grep -E "blocking table difference|^ *BLOCKING" | head -30
  "$PY" - "$GF/Play-$s.ttf" "$built" <<'EOF'
import sys
from fontTools.ttLib import TTFont
rel, ours = (set(TTFont(p).getBestCmap()) for p in sys.argv[1:3])
print("cmap: %d shipped, %d built, %d gained, %d lost" % (len(rel), len(ours), len(ours - rel), len(rel - ours)))
EOF
done
echo "workdir: $W"
