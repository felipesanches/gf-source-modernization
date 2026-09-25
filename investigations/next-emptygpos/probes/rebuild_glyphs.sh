#!/bin/bash
# Question answered: if the converted .glyphs were different in ONE stated way (a
# stand-in for a converter change not yet written), which table rows would still differ
# from the release? Rebuilds an existing harness run's .glyphs after an edit, with the
# same builder3 / d3 / gate steps as tools/baseline.sh, so the only variable is the edit.
#
#   RUN=<harness scratch dir of the style, e.g. .../baseline/Varela-Regular-emptygpos-07>
#   EDIT="<python expression over the .glyphs text, variable t>"   e.g.
#        EDIT='t.replace("languagesystem latn SRB;\\n", "")'
#   B3=<gftools-builder> (default: the pinned one)   EXTRA_CONFIG="key: value"
#   SHIPPED=<release.ttf>   OUT=<dir for the gate text>
#   bash rebuild_glyphs.sh <Style>
# Output: $OUT/<Style>.gate.txt and $OUT/<Style>.ttf; prints the gate's summary line.
set -uo pipefail
style=$1
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
B3=${B3:-/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder}
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
d="$RUN-rebuild"; rm -rf "$d"; mkdir -p "$d/sources" "$OUT"
EDIT="$EDIT" "$PY" - "$RUN/sources/$style.glyphs" "$d/sources/$style.glyphs" <<'EOF'
import os, sys
t = open(sys.argv[1], encoding="utf-8").read()
new = eval(os.environ["EDIT"], {"t": t})
if new == t:
    raise SystemExit("FATAL: the edit changed nothing")
open(sys.argv[2], "w", encoding="utf-8").write(new)
print("edit applied: %d -> %d bytes" % (len(t), len(new)))
EOF
[ $? = 0 ] || exit 2
{ echo "buildVariable: false"; echo "removeOutlineOverlaps: false"
  echo "sources:"; echo "  - $style.glyphs"
  if [ -n "${EXTRA_CONFIG:-}" ]; then printf "%s\n" "$EXTRA_CONFIG"; fi; } > "$d/sources/config.yaml"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) > "$d/build.log" 2>&1 || { echo BUILD-FAILED; exit 1; }
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$SHIPPED" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$SHIPPED" "$built" > "$OUT/$style.gate.txt" 2>&1
cp "$built" "$OUT/$style.ttf"
tail -1 "$OUT/$style.gate.txt"
