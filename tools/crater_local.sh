#!/bin/sh
# Question answered: do the targets a fontc_crater PR adds actually build in crater, in both
# of its modes (default: fontc vs fontmake; gftools: Python gftools builder, fontmake vs
# fontc), before the PR is sent? (cmyr on googlefonts/fontc_crater#100: run crater locally on
# the newly added targets as part of preparing these PRs.)
#
#   sh tools/crater_local.sh <old targets.json> <new targets.json> <scratch dir>
#
# <scratch>/fontc must be a checkout of googlefonts/fontc (crater is run from it, as its CI
# does), built with CARGO_TARGET_DIR=<scratch>/target (fontc_crater, fontc, otl-normalizer),
# and <scratch>/venv a venv with fontc's resources/scripts/requirements.txt installed.
# Writes <scratch>/subset.json (only the entries new in <new>), runs `fontc_crater ci` on it
# with its own cache and output dirs, and prints one line per target: success, or the
# failure crater recorded. Exit 1 if any target fails.
set -eu
OLD=${1:?old targets.json}; NEW=${2:?new targets.json}; S=${3:?scratch dir}
python3 - "$OLD" "$NEW" "$S/subset.json" <<'PY'
import json, sys
old, new, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
seen = {(e["repo_url"], e["rev"], e["config"]) for e in old["sources"]}
added = [e for e in new["sources"] if (e["repo_url"], e["rev"], e["config"]) not in seen]
json.dump(dict(new, sources=added), open(out, "w"), indent=2)
print("subset: %d of %d entries are new" % (len(added), len(new["sources"])))
PY
mkdir -p "$S/cache" "$S/out"
# fontc_crater looks for its binaries in <cwd>/target/release, whatever CARGO_TARGET_DIR says
[ -e "$S/fontc/target" ] || ln -s "$S/target" "$S/fontc/target"
( cd "$S/fontc" && PATH="$S/venv/bin:$PATH" CARGO_TARGET_DIR="$S/target" \
    "$S/target/release/fontc_crater" ci "$S/subset.json" --cache "$S/cache" --out "$S/out" ) \
  > "$S/crater.log" 2>&1 || echo "fontc_crater exited non-zero; see $S/crater.log"
latest=$(ls "$S/out"/20*.json 2>/dev/null | sort | tail -n 1)
[ -n "$latest" ] || { echo "no results file in $S/out"; exit 1; }
python3 "$(dirname "$0")/crater_summary.py" "$latest"
