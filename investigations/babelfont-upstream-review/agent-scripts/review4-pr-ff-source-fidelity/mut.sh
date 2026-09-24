#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review4-pr-ff-source-fidelity
F=$S/mut/babelfont/src/filters/snapcomponenttransforms.rs
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review4-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
cd $S/mut
run() { name=$1; sudo -n /usr/local/sbin/drop-caches; echo "== $name" >> $S/mut-summary.txt; cargo test -p babelfont --lib snapcomponenttransforms > $S/mut-$name.log 2>&1; grep -E '^test .*(FAILED|ok)$|^test result' $S/mut-$name.log >> $S/mut-summary.txt; cp $S/snap.orig.rs $F; }
: > $S/mut-summary.txt
cp $S/snap.orig.rs $F; run unmutated
sed -i 's/    !layer.is_background && matches!(layer.master, LayerType::DefaultForMaster(_))/    let _ = layer; true/' $F; grep -q 'let _ = layer; true' $F && run M1_always_true || echo "M1 sed failed" >> $S/mut-summary.txt
sed -i 's/    !layer.is_background && matches!(layer.master, LayerType::DefaultForMaster(_))/    matches!(layer.master, LayerType::DefaultForMaster(_))/' $F; grep -q '^    matches!(layer.master' $F && run M2_no_background_check || echo "M2 sed failed" >> $S/mut-summary.txt
sed -i 's/    !layer.is_background && matches!(layer.master, LayerType::DefaultForMaster(_))/    !layer.is_background/' $F; grep -q '^    !layer.is_background$' $F && run M3_no_master_check || echo "M3 sed failed" >> $S/mut-summary.txt
sed -i 's/    if rounded == 0.0 {/    if rounded == 0.0 \&\& false {/' $F; grep -q 'rounded == 0.0 && false' $F && run M4_no_neg_zero || echo "M4 sed failed" >> $S/mut-summary.txt
touch $S/mut.done
