# reland-2026-10-01: rendering + advances cluster (scratch)

**Model**: Claude Opus 5.5. Measured 2026-10-01. Pins: babelfont upstream 004200b7
(target-heights/release/babelfont), gftools-builder (gftools-rust ade8776, fontc 1.0.0) at
/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder, google/fonts
working copy /home/fsanches/compartilhado/google/fonts, functional_gate.py from sfd-reland.

Scratch only: nothing here is committed. Promote the scripts next to sfd-reland/tools/probes
if a number below is quoted anywhere.

## Scripts (PY=/home/fsanches/compartilhado/gftools/venv/bin/python3)

| script | question it answers | run |
|---|---|---|
| scripts/build_repo.sh | build a landed repo (or an edited copy of its sources) in scratch | `scripts/build_repo.sh <repo> [<sources dir>] [<build name>]` -> builds/<name>/fonts/ttf |
| scripts/diagnose.py | which reachable glyphs fail the gate's geometry test and HOW (STALE-LSB, SHIFT, ROUND1, MOVED, STRUCT, COMPONENT, ADV), and whether each diffenator3 glyph report is confirmed by geometry or only by HarfBuzz shaping | `$PY scripts/diagnose.py <shipped> <built> <workdir> [--all-changed]` |
| scripts/diagnose_all.sh | diagnose.py over pairs.tsv -> diag/<style>.txt | `scripts/diagnose_all.sh [style]` |
| scripts/lsb_rule.py | in a release, which rule produced glyf header xMin and hmtx lsb (control box vs true-curve floor/trunc/round), and which glyphs are drawn shifted by lsb - xMin | `$PY scripts/lsb_rule.py <release.ttf> --list` |
| scripts/shift_stale_lsb.py | does moving each glyph by the release's lsb - xMin reproduce the release's drawing | `$PY scripts/shift_stale_lsb.py <release> <in.glyphs> <out.glyphs>` |
| scripts/sfd_interp_to_offcurve.py | does emulating sfdLib 2.0.0 (SFD 0x80 interpolated on-curve -> off-curve) reproduce Comic Relief | `$PY scripts/sfd_interp_to_offcurve.py <src.sfd> <in.glyphs> <out.glyphs>` |
| scripts/interp_to_offcurve.py | same, by the midpoint heuristic only (REFUTED as a rule: it also converts designer on-curves that sit at a midpoint) | |
| scripts/add_notdef_glyphs.py | does carrying FontForge's synthesized .notdef in the source reproduce the release's .notdef | `$PY scripts/add_notdef_glyphs.py <in> <out> <Ascent> <Descent>` |
| scripts/round_glyphs.py | how much a ties-to-even round-coordinates filter (implied on-curves left alone) changes point identity | `$PY scripts/round_glyphs.py <in.glyphs> <out.glyphs>` |
| scripts/identity.py | glyphs with the same stored points / the same drawn outline as the release | `$PY scripts/identity.py <shipped> <built>` |
| scripts/dumpglyph.py | print a glyph's points, hmtx, header xMin, components | `$PY scripts/dumpglyph.py <glyph> <font>...` |

Experiments: exp/<name>/sources (edited sources), builds/<name>, gate/<name>/*.json (full
functional_gate.py verdicts), diag/*.txt (diagnose output).
