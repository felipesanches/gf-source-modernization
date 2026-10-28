#!/bin/sh
# Re-land the unpushed repositories that cite the fork branch heads, after the GDEF prefix revert.
set -u
cd /home/fsanches/compartilhado/gf-source-modernization
export TMPDIR=/home/fsanches/compartilhado/tmp
W22=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-10-22
W23=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-10-23
BF_TREE=$W22 sh tools/build_babelfont.sh || exit 1
BF_TREE=$W23 sh tools/build_babelfont.sh || exit 1
echo BUILT; cat $W22/target-heights/BUILT_FROM $W23/target-heights/BUILT_FROM
BF_TREE=$W22 TABLES=families-binary.tsv sh tools/reland_all.sh 2026-10-28-gdef-revert carlito sansation 
BF_TREE=$W23 TABLES=families-binary.tsv sh tools/reland_all.sh 2026-10-28-gdef-revert alef averialibre averiasanslibre averiaseriflibre blackandwhitepicture blackhansans cutefont dokdo eastseadokdo gamjaflower gugi himelody imfelldoublepica imfelldoublepicasc imfelldwpica imfelldwpicasc imfellenglish imfellenglishsc imfellfrenchcanon imfellfrenchcanonsc imfellgreatprimer imfellgreatprimersc jomolhari lato nanumbrushscript nanumgothic nanumgothiccoding nanummyeongjo nanumpenscript poorstory songmyung stylish sunflower 
echo RELAND-DONE
