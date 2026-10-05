next-gsub-verify -- adversarial verification of the "gsub" unit
(Megrim, Poly-Italic, RibeyeMarrow-Regular, Varela-Regular), 2026-09-25.
Model: Claude Opus 5.5. Nothing here is committed; the findings are in the
workflow's structured result. Plain text on purpose (the harness refuses .md reports).

Pins: sources googlefontdirectory-hg 52f780bc (pairing families-next.tsv), releases
google/fonts b5efa9c32e8f, converter integration 17ea899, prototype = 17ea899 + ../next-gsub/
probes/babelfont-17ea899-langsys-as-built.diff built by the verifier (BUILT_FROM d345b49,
scratch ../../../sfd-reland-scratch/gsub-verify/bf-target), gftools-builder3 e851b8b
(fontc 1.0.0), shared gate sfd-batch5/tools/table_gate.py 2f43693 (md5 68c33418),
proposed gate ../next-gsub/probes/table_gate_gsub_proposed.py (md5 c3ee0891).

PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
SC=/home/fsanches/compartilhado/sfd-reland-scratch/gsub-verify
BFI=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BFP=$SC/bf-target/release/babelfont

probes/ (each has a docstring with its question and command)
  release_facts.py              release table set, FFTM stamps vs .sfd times, md5 vs hg
  sfd_registration_vs_release.py  does the release register every lookup exactly as the .sfd?
  sfd_langsys_scan.py           which styles of both batches does the babelfont change touch (static)?
  fea_sweep.sh                  same question, by converting all 149 styles with BFI and BFP
  gsub_langsys_semantics.py     per language system: same substitutions, same order? (structural)
  shape_langsys.py              same, by HarfBuzz shaping with forced x-hbot<TAG> languages
  regate_wa.sh                  rows left after land.py's workarounds and/or another gate
  varela_residual_gpos.py       is Varela's last shaping difference the missing empty GPOS?

runs/
  v0-unmodified                 baseline.sh, BFI            (== baseline-next for all 4)
  v1-megrim-droplookups         baseline.sh, BFI, SRC_OVERRIDE=$SC/src/Megrim.verify-edit.sfd
  v2-proto-langsys              baseline.sh, BFP (Poly-Italic, Poly-Regular, RibeyeMarrow, Varela, Megrim)
  v3-proto+megrim-droplookups   baseline.sh, BFP, the Megrim edits
  v4-megrim-*+workarounds       regate_wa.sh WA=1 on v0/v1/v3 Megrim
  v5-proposed-gate              shared vs proposed gate on v0/v2 builds (GATE_TRACE=1)
  v6-first-batch-ctx            baseline.sh FAMILIES=families.tsv BF=$BFI for the 7 first-batch styles whose
                                releases carry contextual GSUB (Kristi, AbrilFatface, Lekton x2, PatrickHand,
                                Tuffy x2), then the proposed gate on the same d3.json (<Style>.proposed-gate.txt)
  semantics/, shape/            the two equivalence probes, v0 and v2 builds
  varela_residual_gpos.txt      varela_residual_gpos.py on the v2 build
  gate_ctx_negative.*.v2.txt    ../next-gsub/probes/gate_ctx_negative.py on the verifier's v2 builds
  gate_sweep_next.rerun.tsv     ../next-gsub/probes/gate_sweep.sh re-run (identical to theirs)
  converter_tests_proto.txt, clippy_proto.txt, fmt_proto.txt, prototype_build.txt

Commands:
  cd /home/fsanches/compartilhado/gf-source-modernization; V=$PWD/investigations/next-gsub-verify
  for s in Megrim Poly-Italic Poly-Regular RibeyeMarrow-Regular Varela-Regular; do FAMILIES=$PWD/families-next.tsv BF=$BFI OUT=$V/runs/v0-unmodified TAG=gsub-verify-v0 SCRATCH=$SC bash tools/baseline.sh $s; done
  cp <hg Megrim-TTF.sfd> $SC/src/Megrim.verify-edit.sfd; for n in "'aalt' Access All Alternates in Latin lookup 0" "'ss01' Style Set 1 lookup 1" "'locl' Localized Forms in Latin lookup 2"; do $PY tools/sfd_edit.py $SC/src/Megrim.verify-edit.sfd droplookup "$n"; done   (byte-identical to ../next-gsub/edits/Megrim.droplookups.sfd)
  git clone /home/fsanches/compartilhado/babelfont-rs $SC/bf-src; git -C $SC/bf-src checkout 17ea899; git -C $SC/bf-src apply ../next-gsub/probes/babelfont-17ea899-langsys-as-built.diff; commit; sudo -n /usr/local/sbin/drop-caches; CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$SC/bf-target cargo build --release -p babelfont --features cli
  for s in Poly-Italic Poly-Regular RibeyeMarrow-Regular Varela-Regular Megrim; do FAMILIES=$PWD/families-next.tsv BF=$BFP OUT=$V/runs/v2-proto-langsys TAG=gsub-verify-v2 SCRATCH=$SC bash tools/baseline.sh $s; done
  FAMILIES=$PWD/families-next.tsv BF=$BFI OUT=$V/runs/v1-megrim-droplookups TAG=gsub-verify-v1 SCRATCH=$SC SRC_OVERRIDE=$SC/src/Megrim.verify-edit.sfd bash tools/baseline.sh Megrim
  FAMILIES=$PWD/families-next.tsv BF=$BFP OUT=$V/runs/v3-proto+megrim-droplookups TAG=gsub-verify-v3 SCRATCH=$SC SRC_OVERRIDE=$SC/src/Megrim.verify-edit.sfd bash tools/baseline.sh Megrim
  RUN=$SC/baseline/Megrim-gsub-verify-v1 SRC=$SC/src/Megrim.verify-edit.sfd OUT=$V/runs/v4-megrim-v1+workarounds bash $V/probes/regate_wa.sh Megrim   (and v3, and v0 with the unmodified .sfd)
  $PY $V/probes/gsub_langsys_semantics.py <release.ttf> <build.ttf> -v
  $PY $V/probes/shape_langsys.py <release.ttf> <build.ttf>
  $PY $V/probes/sfd_langsys_scan.py > $V/runs/sfd_langsys_scan.txt
  bash $V/probes/fea_sweep.sh > $V/runs/fea_sweep.tsv
  (cd $SC/bf-src && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$SC/bf-target cargo test --release -p babelfont --features cli --lib fontforge)
