#!/bin/sh
# Question answered: which waiting SFD repositories land CLEAN on babelfont upstream main
# plus ONE open babelfont PR (so that PR alone unblocks them)?
#
# Each converter is a scratch worktree: upstream main 5ff5bf04 + a merge of one PR branch
# (local head, as it will be pushed), built with tools/build_babelfont.sh. Landings go to
# scratch; only the logs land in logs/reland-2026-10-22-u<PR>/.
#
# Usage: sh tools/probes/single_pr_relands/run.sh <scratch dir holding u104 u105 u106 ...>
set -eu
S=${1:?scratch dir}
W=$(cd "$(dirname "$0")/../../.." && pwd)
one() {  # $1 = PR number, rest = repos
  n=$1; shift
  mkdir -p "$S/land-u$n"
  BF_TREE="$S/u$n" OUT="$S/land-u$n/repos" LANDED="$S/land-u$n/landed.tsv" \
    SCRATCH="$S/land-u$n/scratch" LAND_ARGS=--unpublished-converter \
    sh "$W/tools/reland_all.sh" "2026-10-22-u$n" "$@"
}
# USE_TYPO_METRICS set by the build (fsSelection bit 7 with OS2Version < 4): #106
one 106 lekton lilitaone megrim mountainsofchristmas nothingyoucoulddo revalia patrickhand \
  lustria lohitbengali lohittamil limelight
# GDEF absent / glyph classes differ: #104
one 104 kottaone macondo monoton oleoscript oleoscriptswashcaps poly ruluko salsa smythe \
  titanone passionone patrickhand lustria tuffy unifrakturcook comicrelief
# kerning pairs differ: #105
one 105 italiana sanchez
