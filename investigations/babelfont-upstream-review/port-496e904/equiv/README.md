# Re-landing equivalence: integration-ff-prs 17ea899 vs babelfont 8b59bc3 (2026-09-24)

integration-ff-prs was rebuilt as upstream/main 496e904 + `git merge --no-edit`
pr-ff-reader-fixes 11706ea (fast-forward), pr-ff-source-fidelity 24671e6,
pr-ff-os2-defaults 119f2be -> 17ea899 (the earlier head, 6232710 on 0b55947, is in the reflog).
Built: `CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR=../../target-integration cargo build --release
-p babelfont --features cli` -> sha256 4cbc83e0c1ea0592... (copied to `bin/`).

| file | question it answers | command |
|---|---|---|
| `bin/babelfont-integration-17ea899` | the candidate (copy of target-integration/release/babelfont) | -- |
| `bin/babelfont-integration-17ea899-minus-496e904` | bisect binary: 17ea899 with #85 (496e904) reverse-applied (`src-no85/`, `pr85-496e904.patch`, `build-no85.log`) | `cd src-no85 && CARGO_TARGET_DIR=../target-no85 cargo build --release -p babelfont --features cli` |
| `RESULT-minus-496e904.txt` | sfd-reland equivalence probe with the bisect binary as candidate: does removing #85 change anything? (no: rows identical to the 17ea899 run) | `cd /home/fsanches/compartilhado/sfd-reland && TMPDIR=<existing dir> .../python3 tools/probes/upstream_prs_equivalence/run.py --cand <bin>` |
| `bbox_offset_styles.py` -> `bbox_offset_styles.txt` | for the 15 offset-mode (OS2Win*/Hhead*Offset: 1) styles, can #85 (ceil/floor instead of round of the bbox base) change a resolved metric at all? Signal: exact curve y-extrema, components decomposed (fontTools BoundsPen), floor/ceil vs round | `.../python3 bbox_offset_styles.py bin/babelfont-integration-17ea899 bbox-work` |
| `gate_candidate.py` -> `gate-all-landed.txt` | would every landed style (33, 27 repos), re-converted with the candidate + tools/workarounds.py, still pass land.py's gate against the shipped font? Builds the committed `sources/` tree with builder3 e851b8b; diffenator3 + sfd-batch5/tools/table_gate.py + exact best-cmap. CLEAN = 0 blocking rows, no cmap change | `TMPDIR=../probe-tmp .../python3 gate_candidate.py --cand bin/babelfont-integration-17ea899 --out gate-work` |
| `comicrelief_build_compare.py` -> `comicrelief/RESULT.txt` | does the one intended .glyphs difference (ComicRelief-Regular `-0` -> `0` component offsets) change the built font? (no: only head.modified differs) | `TMPDIR=../probe-tmp .../python3 comicrelief_build_compare.py bin/babelfont-integration-17ea899` |

Notes
- TMPDIR must be an existing directory: builder3 e851b8b's fix step writes a temp .ttf
  there and fails every build ("No such file or directory") when it does not exist.
- Shipped fonts: /home/fsanches/compartilhado/google/fonts at b5efa9c32 (the revision the
  landings were gated against; no diff on the 42 families.tsv files).
- `target-no85/` is a regenerable cargo cache (copy of target-integration + the bisect build).
