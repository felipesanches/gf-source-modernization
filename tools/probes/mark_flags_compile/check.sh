#!/bin/sh
# Compile markflags.sfd with --fontforge-mark-lookups and print the GDEF mark class /
# mark glyph sets and each GPOS lookup's flag and filtering set.
# Usage: sh check.sh <babelfont binary>
set -eu
D=$(cd "$(dirname "$0")" && pwd)
OUT=${TMPDIR:-/home/fsanches/compartilhado/tmp}/markflags.ttf
"$1" "$D/markflags.sfd" "$OUT" --fontforge-mark-lookups
/home/fsanches/compartilhado/gftools/venv/bin/python3 - "$OUT" <<'PY'
import sys
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1]); g = f["GDEF"].table
print("MarkAttachClassDef", g.MarkAttachClassDef.classDefs if g.MarkAttachClassDef else None)
print("MarkGlyphSets", [c.glyphs for c in g.MarkGlyphSetsDef.Coverage] if getattr(g, "MarkGlyphSetsDef", None) else None)
for i, l in enumerate(f["GPOS"].table.LookupList.Lookup):
    print(i, l.LookupType, hex(l.LookupFlag), getattr(l, "MarkFilteringSet", None))
PY
