#!/bin/bash
# Question answered: converting each style's UNMODIFIED source with FIDELITY
# flags only -- flags that replicate what FontForge's own TTF exporter did, never
# flags that correct the font -- how far is the build from the binary google/fonts
# ships, and in which table rows?
#
# That is the measurement every later decision rests on. Each blocking row it
# reports has to be closed by something visible in the repository's history: a
# documented edit to the .sfd (criterion B), or a converter fix. Whatever this
# reports as CLEAN needs no edit at all, and must not get one.
#
# One build per style, from a config naming only that style's source, so the
# built font and the shipped font are paired by construction rather than by
# matching file names -- mis-pairing is where this programme's false findings
# have come from.
#
# Excluded on purpose, although earlier batches passed them to babelfont:
#   --single-line-names, --drop-copyright-description   babelfont's own help calls
#       each "A correction, not a faithful conversion". A correction belongs in the
#       history as a source edit, not hidden in the converter's arguments.
#   --normalise-nbsp-width   same: the convention makes it an .sfd commit.
#
# Usage: tools/baseline.sh <style> ...      (style names from families.tsv)
#        tools/baseline.sh --all            every row, 3 at a time
# Output: baseline/<style>.tsv  (one row) and baseline/<style>.gate.txt
#
# To TRY a candidate change without touching anything shared (environment):
#   SRC_OVERRIDE=<file.sfd>  convert this file instead of the unmodified source
#   EXTRA_FLAGS="--a --b"    append babelfont flags
#   DROP_FLAGS="--a --b"     remove babelfont flags the default recipe would pass
#   BF=<babelfont binary>    use another converter build
#   OUT=<dir>                write results there instead of baseline/
#   TAG=<name>               suffix for the scratch directory (parallel callers)
set -uo pipefail
W=$(cd "$(dirname "$0")/.." && pwd)
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
BF=${BF:-/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target/release/babelfont}
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
SCR=${SCRATCH:-/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad}/baseline
OUT=${OUT:-$W/baseline}
mkdir -p "$OUT" "$SCR"

for t in "$BF" "$B3" "$D3" "$PY"; do [ -x "$t" ] || { echo "MISSING TOOL: $t" >&2; exit 2; }; done

if [ "${1:-}" = "--all" ]; then
  tail -n +2 "$W/families.tsv" | cut -f7 | xargs -P 3 -n 1 "$0"
  exit $?
fi

for style in "$@"; do
  row=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s' "$W/families.tsv")
  [ -n "$row" ] || { echo "no families.tsv row for $style" >&2; continue; }
  IFS=$'\t' read -r repo fam lic kind base commit _ src shipped <<<"$row"
  d="$SCR/$style${TAG:+-$TAG}"; rm -rf "$d"; mkdir -p "$d/tree" "$d/sources"
  log="$OUT/$style.gate.txt"; : > "$log"

  # the unmodified base tree, exactly what the repository's first commit holds
  if [ "$kind" = hg ]; then
    git -C "$ARC/$base.git" archive "$commit" "$lic/$fam" | tar -x -C "$d/tree" --strip-components=2
  else
    git -C "$ARC/$base.git" archive "$commit" | tar -x -C "$d/tree"
  fi
  sfd="$d/tree/$src"
  if [ -n "${SRC_OVERRIDE:-}" ]; then cp "$SRC_OVERRIDE" "$sfd"; fi
  [ -e "$sfd" ] || { printf '%s\t%s\tNO-SOURCE\t-\t-\t%s\n' "$repo" "$style" "$src" > "$OUT/$style.tsv"; continue; }

  # --- fidelity decisions, each asked of the release -------------------------
  # makeotf's duplicate set: pass the filter only when the release carries it
  dup=$("$PY" - "$shipped" <<'EOF'
import sys
from fontTools.ttLib import TTFont
cm = TTFont(sys.argv[1]).getBestCmap() or {}
a, d = 0x00A0 in cm, 0x00AD in cm
print("yes" if (a and d) else ("partial" if (a or d) else "no"))
EOF
)
  # contour direction: normalise only when the release is itself uniform
  uni=$("$PY" - "$shipped" <<'EOF'
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
f = TTFont(sys.argv[1]); gs = f.getGlyphSet(); cw = ccw = 0
for n in f.getGlyphOrder():
    p = AreaPen(gs)
    try:
        gs[n].draw(p)
    except Exception:
        continue
    cw += p.value < 0; ccw += p.value > 0
print("yes" if cw == 0 or ccw == 0 else "no")
EOF
)
  # Filters run in command-line order. --fontforge-os2-defaults measures the
  # outlines (x-height, cap height), so it runs FIRST, on the outlines exactly as
  # the source states them -- before --snap-component-transforms or any path
  # direction filter changes what FontForge would have measured.
  flags=(--fontforge-os2-defaults --add-instance-per-master --infer-mark-category
         --set-subcategory --keep-source-glyph-names --keep-source-advances
         --snap-component-transforms --fontforge-underline-position)
  if [ "$uni" = yes ]; then flags+=(--correct-path-direction); else flags+=(--reverse-path-direction); fi
  [ "$dup" = yes ] && flags+=(--add-legacy-duplicate-cmap)
  if [ -f "$sfd" ] && grep -qE 'abvm|blwm' "$sfd"; then flags+=(--correct-conjunct-category); fi
  for x in ${EXTRA_FLAGS:-}; do flags+=("$x"); done
  if [ -n "${DROP_FLAGS:-}" ]; then
    keep=(); for x in "${flags[@]}"; do case " $DROP_FLAGS " in *" $x "*) ;; *) keep+=("$x");; esac; done
    flags=("${keep[@]}")
  fi
  echo "flags: ${flags[*]}" >> "$log"
  echo "decisions: legacy-duplicate-cmap-in-release=$dup release-directions-uniform=$uni" >> "$log"

  g="$d/sources/$style.glyphs"
  if ! "$BF" "$sfd" "$g" "${flags[@]}" >> "$log" 2>&1 || [ ! -s "$g" ]; then
    printf '%s\t%s\tCONVERT-FAILED\t-\t-\t%s\n' "$repo" "$style" "${flags[*]}" > "$OUT/$style.tsv"; continue
  fi
  { echo "buildVariable: false"; echo "removeOutlineOverlaps: false"
    echo "sources:"; echo "  - $style.glyphs"; } > "$d/sources/config.yaml"
  if ! (cd "$d" && timeout 900 "$B3" sources/config.yaml) >> "$log" 2>&1; then
    printf '%s\t%s\tBUILD-FAILED\t-\t-\t%s\n' "$repo" "$style" "${flags[*]}" > "$OUT/$style.tsv"; continue
  fi
  built=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null)
  nb=$(printf '%s\n' "$built" | grep -c .)
  if [ "$nb" != 1 ]; then
    printf '%s\t%s\tBUILT-%s-FONTS\t-\t-\t%s\n' "$repo" "$style" "$nb" "$(echo $built | xargs -n1 basename 2>/dev/null | tr '\n' ' ')" > "$OUT/$style.tsv"; continue
  fi

  "$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
  gate=$("$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" 2>&1)
  printf '%s\n' "$gate" >> "$log"
  # absent its closing summary line the gate did not finish; silence is not clean
  n=$(printf '%s' "$gate" | sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' | tail -1)
  keys=$(printf '%s\n' "$gate" | awk '/^ *BLOCKING /{print $2}' | sort -u | paste -sd, -)
  if [ -z "$n" ]; then verdict=GATE-DID-NOT-FINISH; n=-
  elif [ "$n" = 0 ]; then verdict=CLEAN
  else verdict=BLOCKING; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$repo" "$style" "$verdict" "$n" "$(basename "$built")" "${keys:--}" > "$OUT/$style.tsv"
  echo "$style: $verdict $n"
done
