# tuffy -- the adversarial verifier's independent checks

Written by the verifying agent from the investigation's claims, deliberately NOT from the
investigator's probes, so a shared bug cannot hide. Recovered from session scratch.
Run with `PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`.

| script | question it answers | command |
|---|---|---|
| `verify_apply.py` | Applied from the UNMODIFIED source to a fresh copy, do the proposed `.sfd` edits produce the gate rows the investigation reported? An independent re-implementation of every proposed op. | `$PY verify_apply.py <in.sfd> <out.sfd> OP ARGS... [-- OP ARGS...]...` |
| `gate_contour_split.py` | Does the table gate's verdict change if `_abs_contour_area` delimits contours by closePath/endPath instead of moveTo? (The fix is now in `sfd-batch5/tools/table_gate.py`, commit `cd4f827`.) | `$PY gate_contour_split.py <d3.json> --fonts <shipped.ttf> <built.ttf>` |
| `xor_scan.py` | Independent of the gate's measures: which codepoints DRAW differently, as filled regions (skia-pathops symmetric difference over the larger area)? | `$PY xor_scan.py <release.ttf> <built.ttf> [--min 0.005] [--cps U+XXXX,...]` |
| `raster_scan.py` | Independent again: which codepoints RENDER differently, rasterised by FreeType unhinted at a given ppem? | `$PY raster_scan.py <release.ttf> <built.ttf> [--min 0.01] [--ppem 1024]` |
| `component_moves.py` | Which composites place their components differently in two fonts (leaf components flattened, matched by codepoint)? | `$PY component_moves.py <A.ttf> <B.ttf>` |

The investigator's own probes are in `../probes/`, each stating its question in its header.
