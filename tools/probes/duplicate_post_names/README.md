# duplicate_post_names

Federo's binary-route build had one blocking row, `hmtx.nonmarkingreturn {"width": [532, 0]}` (logs/crater-skipped-2026-11-16/probe.txt). The release's post table names two glyphs `nonmarkingreturn`: glyph 2 (advance 0) and glyph 217 (advance 532), both empty and unencoded. diffenator3 keys the hmtx comparison by name and read glyph 217 in the release and glyph 2 in the build. The build has the same 220 glyphs in the same order with the same metrics; glyph 217 is named `nonmarkingreturn.1`, as fontTools names it when reading the release.

`tools/table_gate.py` `arbitrate_duplicate_names` now passes such a row only when the name is stated more than once in the release and every advance and left side bearing is equal index by index. With it Federo's probe has 0 blocking rows and fails the functional gate on hinting only:

    BF=<babelfont 26fdcfa9> python3 -I tools/probes/binary_to_source/probe.py <scratch> <google/fonts>/ofl/federo/Federo-Regular.ttf

## How common is it

`scan.py <google/fonts checkout>`: fonts whose post table gives one name to more than one glyph, with each glyph's index, advance, left side bearing, contour count and code points. It reads the `.ttf` files directly inside each family directory.

`scan.tsv`: google/fonts cc39c4c2c, fontTools 4.61.1: 66 of 3832 fonts.
