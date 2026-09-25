#!/bin/bash
# Question answered: which styles' converted FEA does a candidate babelfont change?
# A converter change can only move a style's layout rows if it changes the feature
# code babelfont writes into the .glyphs, so this pre-screens every style of a pairing
# table (convert only, no build) and lists the ones whose featurePrefixes/features
# differ between two converter binaries run with the same recipe flags.
#
#   OLD=<babelfont> NEW=<babelfont> FAMILIES=<pairing.tsv> SCRATCH=<dir> \
#     bash fea_diff_sweep.sh > <out.tsv>
# Output rows: style <TAB> SAME|DIFFERS|CONVERT-FAILED(old/new) <TAB> first differing line
set -uo pipefail
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
W=/home/fsanches/compartilhado/sfd-reland
export FAMILIES
tail -n +2 "$FAMILIES" | while IFS=$'\t' read -r repo fam lic kind base commit style src shipped; do
  d="$SCRATCH/feasweep/$style"; rm -rf "$d"; mkdir -p "$d/tree"
  if [ "$kind" = hg ]; then
    git -C "$ARC/$base.git" archive "$commit" "$lic/$fam" | tar -x -C "$d/tree" --strip-components=2
  else
    git -C "$ARC/$base.git" archive "$commit" | tar -x -C "$d/tree"
  fi
  [ -e "$d/tree/$src" ] || { printf '%s\tNO-SOURCE\t-\n' "$style"; continue; }
  mapfile -t flags < <("$PY" "$W/tools/recipe.py" "$style")
  "$OLD" "$d/tree/$src" "$d/old.glyphs" "${flags[@]}" > /dev/null 2>&1 || { printf '%s\tCONVERT-FAILED(old)\t-\n' "$style"; continue; }
  "$NEW" "$d/tree/$src" "$d/new.glyphs" "${flags[@]}" > /dev/null 2>&1 || { printf '%s\tCONVERT-FAILED(new)\t-\n' "$style"; continue; }
  "$PY" - "$d/old.glyphs" "$d/new.glyphs" "$style" <<'EOF'
import sys, openstep_plist
def fea(p):
    d = openstep_plist.load(open(p, encoding="utf-8"), use_numbers=True)
    out = []
    for k in ("featurePrefixes", "classes", "features"):
        for x in d.get(k, []):
            out.append("%s %s\n%s" % (k, x.get("tag") or x.get("name"), x.get("code", "")))
    return "\n".join(out).splitlines()
a, b = fea(sys.argv[1]), fea(sys.argv[2])
if a == b:
    print("%s\tSAME\t-" % sys.argv[3])
else:
    import difflib
    first = next(l for l in difflib.unified_diff(a, b, lineterm="", n=0)
                 if l[:1] in "+-" and not l.startswith(("+++", "---")))
    print("%s\tDIFFERS\t%s" % (sys.argv[3], first.strip()))
EOF
  rm -rf "$d/tree"
done
