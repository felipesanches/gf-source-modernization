#!/bin/bash
# Question answered: was the Play release google/fonts ships (v2.101) built from
# m4rc1e/play, and from which commit's source?
#
# Compares google/fonts ofl/play/Play-<Style>.ttf, table by table (raw bytes), with
#   (1) m4rc1e/play 3565c8a fonts/ttf/Play-<Style>.ttf  -- the hinted fonts
#       (sources/build.sh: ttfautohint -x 13), and
#   (2) m4rc1e/play f17f03f fonts/ttf/Play-<Style>.ttf  -- the unhinted Glyphs.app
#       export of sources/Play.glyphs (blob b5d9f58, unchanged at 3565c8a).
# Pass = (1) differs only in head (modified, checkSumAdjustment); (2) has identical
# cmap/hmtx/GSUB/GPOS/GDEF/OS2/hhea/post and every glyph's coordinates.
#
# Usage: probes/release_vs_upstream.sh [mirror]
#   mirror defaults to a scratch clone; create one with
#     git clone --mirror https://github.com/m4rc1e/play <mirror>
# (m4rc1e/play is NOT in the repo archive as of 2026-09-23.)
set -uo pipefail
M=${1:-/home/fsanches/compartilhado/upstream_repos/repo_archive/m4rc1e/play.git}
GF=/home/fsanches/compartilhado/google/fonts
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
t=$(mktemp -d)
for s in Regular Bold; do
  git -C "$M" show 3565c8a:fonts/ttf/Play-$s.ttf > "$t/hinted-$s.ttf"
  git -C "$M" show f17f03f:fonts/ttf/Play-$s.ttf > "$t/unhinted-$s.ttf"
done
echo "Play.glyphs blob at f17f03f / 3565c8a: $(git -C "$M" rev-parse f17f03f:sources/Play.glyphs) $(git -C "$M" rev-parse 3565c8a:sources/Play.glyphs)"
"$PY" - "$GF" "$t" <<'PYEOF'
import sys
from fontTools.ttLib import TTFont
gf, t = sys.argv[1:3]
for s in ["Regular", "Bold"]:
    rel = TTFont(f"{gf}/ofl/play/Play-{s}.ttf")
    h = TTFont(f"{t}/hinted-{s}.ttf")
    tabs = sorted(set(rel.reader.keys()) | set(h.reader.keys()))
    d = [x for x in tabs if x not in rel.reader or x not in h.reader or rel.reader[x] != h.reader[x]]
    hd = [k for k in vars(rel["head"]) if getattr(rel["head"], k) != getattr(h["head"], k, None)]
    print(f"{s}: release vs 3565c8a hinted: tables differing {d}; head fields differing {hd}")
    u = TTFont(f"{t}/unhinted-{s}.ttf")
    same = [x for x in ["cmap", "hmtx", "GSUB", "GPOS", "GDEF", "OS/2", "hhea", "post"] if rel.reader[x] == u.reader[x]]
    ga, gb = rel["glyf"], u["glyf"]
    order = rel.getGlyphOrder() == u.getGlyphOrder()
    nd = sum(ga[g].getCoordinates(ga)[0].array.tolist() != gb[g].getCoordinates(gb)[0].array.tolist() for g in rel.getGlyphOrder()) if order else "n/a"
    print(f"{s}: release vs f17f03f unhinted: byte-identical {same}; glyph order equal {order}; glyphs with different coordinates {nd}")
PYEOF
rm -rf "$t"
