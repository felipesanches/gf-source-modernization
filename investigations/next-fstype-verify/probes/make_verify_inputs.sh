#!/bin/bash
# make_verify_inputs.sh -- independent inputs for re-verifying unit "fstype".
#
# Question answered: built WITHOUT the investigated agent's probes (its
# make_candidates.py and families-fstype.tsv), do the proposed .sfd edits, applied
# one at a time through the shared tools/sfd_edit.py CLI exactly as tools/land.py
# applies a plan, close the rows the investigation says they close -- and which of
# the edits actually change the build?
#
# Writes (under $V=investigations/next-fstype-verify/runs):
#   families-verify.tsv   families-next.tsv's titilliumweb + wallpoet rows, plus the
#                         two ExtraLight rows re-derived here from pair_next.py's own
#                         columns (source = the .sfd whose FontName was the binary's
#                         PS name at google/fonts 90abd17b4; see pair_history.py)
# and candidate .sfd sets under $S (scratch, regenerable):
#   c-fstype/        FSType 0 (all 12)
#   c-elweight/      + TTFWeight 275 on the two ExtraLight sources, NO rename
#   c-el17/          + only LangName ID 17 (and ID 2 for the italic) Thin -> ExtraLight
#   c-elfull/        + the investigation's full rename (FontName, FullName, LangName IDs 3/17[/2])
#   c-version/       c-elfull + Version 1.002 / sfntRevision 0x00010083 / LangName IDs 3,5
# Every LangName line is derived here by editing the source's own line (a string
# replacement inside the named quoted fields), then applied with `setfield LangName`.
#
# Run:  bash investigations/next-fstype-verify/probes/make_verify_inputs.sh
set -euo pipefail
W=/home/fsanches/compartilhado/gf-source-modernization
V=$W/investigations/next-fstype-verify/runs
S=/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
HG=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
C=52f780bc9d197280a9f430574e179a5f233c56b6
GF=/home/fsanches/compartilhado/google/fonts
mkdir -p "$V" "$S"

{ head -1 $W/families-next.tsv
  awk -F'\t' '$1=="titilliumweb"||$1=="wallpoet"' $W/families-next.tsv
  for p in "ExtraLight Thin" "ExtraLightItalic ThinItalic"; do
    set -- $p
    printf 'titilliumweb\ttitilliumweb\tofl\thg\tgooglefonts/googlefontdirectory-hg\t%s\tTitilliumWeb-%s\tsrc/TitilliumWeb-%s-TTF.sfd\t%s/ofl/titilliumweb/TitilliumWeb-%s.ttf\n' \
      "$C" "$1" "$2" "$GF" "$1"
  done; } > "$V/families-verify.tsv"

edit() { "$PY" "$W/tools/sfd_edit.py" "$@"; }

# the source's own LangName 1033 line with the named quoted fields string-replaced
langname() {  # file ids old new
  "$PY" - "$@" <<'EOF'
import re, sys
path, ids, old, new = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], sys.argv[3], sys.argv[4]
text = open(path, encoding="utf-8", errors="surrogateescape").read()
m = re.search(r"^LangName: 1033 (.*)$", text, re.M)
toks = re.findall(r'"[^"]*"', m.group(1))
assert not re.sub(r'"[^"]*"', "", m.group(1)).strip()
for i in ids:
    assert old in toks[i], (i, toks[i])
    toks[i] = toks[i].replace(old, new)
print("LangName 1033 " + " ".join(toks) + " ")
EOF
}

tail -n +2 "$V/families-verify.tsv" | while IFS=$'\t' read -r repo fam lic kind base commit style src shipped; do
  for set in c-fstype c-elweight c-el17 c-elfull c-version; do
    case $set in c-fstype) ;; c-version) [ "$repo" = titilliumweb ] || continue;;
                 *) case $style in *ExtraLight*) ;; *) continue;; esac;; esac
    mkdir -p "$S/$set"; f="$S/$set/$style.sfd"
    git -C "$HG" show "$commit:$lic/$fam/$src" > "$f"
    { echo "## $set $style <- $src"
      edit "$f" setfield FSType 0
      case $set in c-elweight|c-el17|c-elfull|c-version)
        case $style in *ExtraLight*)
          edit "$f" setfield TTFWeight 275
          it=; ids=17; case $style in *Italic) ids=2,17;; esac
          if [ $set = c-el17 ]; then
            edit "$f" setfield "$(langname "$f" $ids Thin ExtraLight)"
          elif [ $set != c-elweight ]; then
            fn=$("$PY" -c "import sys;sys.path.insert(0,'$W/tools');import sfd_edit;print(sfd_edit.field_value(open('$f',errors='replace').read(),'FontName'))")
            edit "$f" setfield FontName "${fn/Thin/ExtraLight}"
            full=$("$PY" -c "import sys;sys.path.insert(0,'$W/tools');import sfd_edit;print(sfd_edit.field_value(open('$f',errors='replace').read(),'FullName'))")
            new="${full/WebThin/Web ExtraLight}"
            edit "$f" setfield FullName "$new"
            edit "$f" setfield "$(langname "$f" 3,$ids Thin ExtraLight)"
          fi;;
        esac;;
      esac
      if [ $set = c-version ]; then
        v=$("$PY" -c "import sys;sys.path.insert(0,'$W/tools');import sfd_edit;print(sfd_edit.field_value(open('$f',errors='replace').read(),'Version'))")
        edit "$f" setfield Version "${v/1.001;/1.002;}"
        edit "$f" setfield sfntRevision 0x00010083
        edit "$f" setfield "$(langname "$f" 3,5 1.001 1.002)"
      fi
    } >> "$V/candidates.log" 2>&1
  done
done
echo "wrote $V/families-verify.tsv and candidate sets under $S; log $V/candidates.log"
