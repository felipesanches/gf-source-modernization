# Re-land on upstream tools, 2026-10-01: research results

The re-land of all 101 repositories with babelfont upstream main 004200b7 and gftools-rust
ade8776 (logs/reland-2026-10-01/, triage.tsv via tools/reland_triage.py: 149 styles, 39 pass the
functional gate, 29 CLEAN) was followed by five research agents, one per failure cluster.
Their scripts are in research-scratch (sessions/2026-10-01_reland-r); the results quoted in
PR-QUEUE are here:

- `linespacing/`: babelfont-proto-legacy-os2-version.diff (prototype filter
  --fontforge-legacy-os2-version: clear fsSelection bits 7/8 when the source's OS2Version is 1-3;
  2 unit tests, fmt, clippy); bit7_sweep.txt (rule right on 139 of 141 FontForge exports, the
  current reader on 8); coverage.tsv (cause per failing style); README (probes).
- `names/`: fix.txt, fix-always.txt, fix-others.txt -- names check before/after adding the
  proposed Name Table Entry values (73 of 87 failing styles fixed; 27 passing styles broken,
  releases renamed at onboarding).
- `outlines/`: README of the rendering/advances research (stale lsb, FontForge .notdef, sfdLib
  interpolated points, spacing-combining marks, isFixedPitch).
