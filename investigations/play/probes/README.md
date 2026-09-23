# Play probes

Each script answers one question. Run from `sfd-reland/investigations/play/`.
The mirrors are in the repo archive since 2026-09-23:
`/home/fsanches/compartilhado/upstream_repos/repo_archive/{m4rc1e,alexeiva,librefonts}/play.git`.
Pass the m4rc1e one where a script takes `[mirror]`. (alexeiva/play d84ad58 is the
canonical upstream; its tree is identical to m4rc1e 3565c8a.)

| script | question it answers | command |
|---|---|---|
| `release_vs_upstream.sh` | Was the shipped v2.101 built from m4rc1e/play, and from which commit's source? Pass = release differs from `3565c8a:fonts/ttf/*` only in `head` (modified, checkSumAdjustment), and from the unhinted `f17f03f:fonts/ttf/*` export in no layout/metric table and no glyph coordinate. | `bash probes/release_vs_upstream.sh [mirror]` |
| `gate_vs_history.sh` | Which Play release does our conversion of the hg `.sfd` match? Gates one built font against all five Play binaries google/fonts ever shipped (v1.002, v1.003, v1.100, v2.000, v2.101). Fewer blocking rows = closer. | `bash probes/gate_vs_history.sh <Regular\|Bold> <built.ttf> runs/history` |
| `design_delta.py` | How much DESIGN differs between two fonts? Pairs by codepoint; counts missing codepoints, differing advances, and outlines whose bbox moves >2 units or area changes >1% (point order / curve conversion ignored). | `gftools/venv/bin/python3 probes/design_delta.py <A.ttf> <B.ttf>` |
| `classify_rows.py` | One TSV line per BLOCKING gate row, with its classification and, for cmap rows, both glyphs' name/advance/bbox. | `gftools/venv/bin/python3 probes/classify_rows.py <gate.txt> <release.ttf> <built.ttf> <Style> > rows.tsv` |
| `modern_route_gate.sh` | How far is the pinned toolchain from reproducing the release out of its real source (`Play.glyphs`, Glyphs 2), and what blocks it? Runs babelfont on the Glyphs 2 file, one builder3 build, and the table gate. | `bash probes/modern_route_gate.sh [mirror] [outdir]` |

`<built.ttf>` is the font `tools/baseline.sh` leaves in
`$SCRATCH/baseline/Play-<Style>-<TAG>/fonts/ttf/` (regenerable; rerun baseline.sh).
