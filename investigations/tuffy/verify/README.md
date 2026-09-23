# tuffy -- the adversarial verifier's independent checks

Written by the verifying agent from the investigation's claims, deliberately NOT from the
investigator's probes, so a shared bug cannot hide. Recovered from session scratch.
Run with `PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`.

| script | question it answers | command |
|---|---|---|
| `verify_apply.py` | Applied from the UNMODIFIED source to a fresh copy, do the proposed `.sfd` edits produce the gate rows the investigation reported? An independent re-implementation of every proposed op. | `$PY verify_apply.py <in.sfd> <out.sfd> OP ARGS... [-- OP ARGS...]...` |
| `gate_contour_split.py` | Does the table gate's verdict change if `_abs_contour_area` delimits contours by closePath/endPath instead of moveTo? (The fix is now in `sfd-batch5/tools/table_gate.py`, commit `cd4f827`.) | `$PY gate_contour_split.py <d3.json> --fonts <shipped.ttf> <built.ttf>` |
| `xor_scan.py` | **UNRELIABLE -- do not use; kept only because nothing unversioned is deleted.** Meant to measure filled-region differences with skia-pathops, but the area of pathops' XOR/DIFFERENCE output comes back with inconsistent winding (U+1E0C: identical 633434-unit regions measured 115% different). Superseded by `raster_scan.py`; no number in VERIFY.md comes from it. | -- |
| `raster_scan.py` | Independent of the gate's measures: which codepoints RENDER differently? FreeType, unhinted, 1-bit, nonzero fill, both glyphs in one pixel frame; ratio = differing pixels / filled pixels. Sanity: the release against itself gives 0 of 1501. | `$PY raster_scan.py <release.ttf> <built.ttf> [--min 0.01] [--ppem 1024] [--cps U+XXXX,...]` |
| `component_moves.py` | Which composites place their components differently in two fonts (leaf components flattened, matched by codepoint)? | `$PY component_moves.py <A.ttf> <B.ttf>` |
| `gate_filled_area.py` | Which gate rows are only overlap representation? The unmodified gate with the area measure swapped for the FILLED region (pathops simplify, nonzero); `--control A B` for the Allerta negative control. | `$PY gate_filled_area.py <d3.json> --fonts <shipped> <built>` |
| `gate_either_area.py` | The same, but a glyph passes when EITHER the gate's per-contour sum OR the filled-region area agrees within 0.4% (so no current pass can turn into a fail). | `$PY gate_either_area.py <d3.json> --fonts <shipped> <built>` / `--control A B` |
| `rerun.sh` | Reruns every measurement VERIFY.md quotes, from the unmodified sources, one build at a time; records every edit applied. | `bash rerun.sh` (writes to `W=`, default session scratch) |

The investigator's own probes are in `../probes/`, each stating its question in its header.

`runs/` holds the text outputs of the last `rerun.sh` run (gate summaries as `<run>__<Style>.gate.txt`,
raster/component/gate-variant reports, `rerun.log`). Built fonts are not kept; `rerun.sh` regenerates them.
