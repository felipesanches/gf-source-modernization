# manjari-2026-11-18

Manjari (google/fonts `ofl/manjari`, version 2.000) pins gitlab.com/smc/fonts/manjari at 8948773e572ce0b58d93b0f120f561a0b02e9853 with an override config that builds `sources/Manjari-{Thin,Regular,Bold}.ufo`. fontc_crater cannot fetch GitLab repositories (googlefonts/google-fonts-sources#80). These measurements ask whether a googlefonts repository could carry Manjari with sources that rebuild the release.

Tools: gftools-builder 1e638bd (simoncozens/gftools-rust, fontc 1.0.0), the one `tools/land.py` pins; babelfont 26fdcfa9 (felipesanches/babelfont-rs branch 2026-11-02); Python gftools 0.10.8 with fontTools 4.68.0 (fontc_crater's pins). Gates: `tools/table_gate.py` and `tools/functional_gate.py`, as `tools/land.py` runs them.

## The upstream UFOs as they are

- Python gftools 0.10.8 cannot open `Manjari-Thin.ufo` or `Manjari-Bold.ufo`: their `data` directory is a symbolic link to `../Manjari-Regular.ufo/data`, and fontTools stops with `IllegalBackReference: path 'data' resolves outside of the filesystem root`. A mirror of the upstream repository would therefore still fail in crater.
- `ufo-route.txt`: `B3=<gftools-builder 1e638bd> ufo_route.py <checkout> <google/fonts>/ofl/manjari`. All three styles build. Code points, shaping (about 662,700 runs each), names, line spacing, advances, GDEF and hinting (the release's `prep` is the 7-byte smart-dropout setup fontc also writes) pass. Two GSUB rows per style are lookup numbering and rule order, with identical shaping. Rendering fails: 11 (Thin), 4 (Regular) and 6 (Bold) outlines draw different ink.
- `ufo-route-overlaps.txt`: the same with `removeOutlineOverlaps: true` added to the config; the result is identical.
- `duplicate-contours.tsv`: `duplicate_contours.py <the three UFOs>`. 8 Thin glyphs and 1 Regular glyph draw the same contour two or three times (`guillemotleft` in the Regular: 4 contours, each twice; the release has 2). The release, built by fontmake with overlap removal, merged them; the fontc build keeps them. The other differing glyphs (`uni00B5`, `section`, `logicalnot` in the Regular; `p2l3u1`, `l3p1` and its variants in the Bold, built from components) have not been explained yet.
- None of the differing glyphs changed upstream after the pinned commit (17 later commits on master).

## The binary route

- `binary-route.txt`: `tools/probes/binary_to_source/probe.py` on the three shipped fonts. No style builds: the release's vendor ID is `SMC` padded with a NUL byte, babelfont writes it into the `.glyphs` file as `SMC{0x00}`, and fontc rejects that (`Invalid tag 'SMC{0x00}': Invalid length (9)`). 242 of the 3,832 `.ttf` files in google/fonts cc39c4c2c have a NUL-padded vendor ID.
