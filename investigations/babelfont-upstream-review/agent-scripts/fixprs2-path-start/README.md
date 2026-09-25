# fix-glyphs3-path-start: the preparer's analysis scripts

Kept verbatim because the preparer's notes (workflow wf_f47a0fed-bbb) quote their output.

- `rot1_detail.py <font> <glyph>`: per-contour start points of a glyph, to see a rotation by one node.
- `implied_between01.py <release.ttf> <built.ttf> <file.glyphs>`: counts implied on-curve points between off-curves in each, to separate start-point rotation from implied-point differences.
