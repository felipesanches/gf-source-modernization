# binary_to_source

**Question answered:** can a family that Google Fonts ships with no sources anywhere be given
a source by converting its own binary with babelfont, and does that source rebuild the binary?

`probe.py` converts each shipped `.ttf` with babelfont (TTF reader -> `.glyphs`), builds it with
gftools-builder, and gates the build against the shipped binary exactly as `tools/land.py` gates a
conversion: the table gate (`tools/table_gate.py`), the release's exact codepoints, and
`tools/functional_gate.py` (cmap, shaping, rendering, names, line spacing, advances, GDEF).
CLEAN means 0 blocking table rows, the same codepoints and every functional check passing.

The one workaround applied after babelfont is `tools/workarounds.py`'s weight class: fontc
1.0.0 drops a single master's instance weightClass (`issues/fontc-static-weight-class.md`), so
a usWeightClass other than 400 travels as FEA (`table OS/2 { WeightClass N; }`), read from the
binary.

    BF=<babelfont> B3=<gftools-builder> python3 tools/probes/binary_to_source/probe.py \
      <scratch dir> <shipped.ttf>...

(a Python with what tools/functional_gate.py imports: fontTools, uharfbuzz, freetype-py).

It prints one verdict line per font, then the blocking rows and failed functional checks.
The scratch dir keeps each font's `.glyphs`, `config.yaml`, build and diffenator3 JSON.

## The other scripts

- `screen.py <census tsv> <google/fonts> <rev> <repo archive>`: for each family the census gave no
  buildable source (NO-SOURCES, NO-SOURCE-BLOCK, NOT-MIRRORED), does the repository METADATA.pb
  records hold any source file -- at the recorded commit, inside a .zip there, or anywhere in
  its history (googlefontdirectory-hg: the family's directory only)? BINARY-ONLY /
  HAS-SOURCES / NO-REPO (results/screen-2026-10-13.tsv). Sources kept in another repository
  (Noto CJK: Adobe's Source Han) and generators (Libre Barcode) it cannot see.
- `check_info_claims.py <google/fonts> <rev> <repo archive>`: which upstream_info.md files claim
  source formats in their "Buildable" row that the recorded repository never held, or state a
  "Source path" that is not in it (results/upstream-info-claims-2026-10-13.tsv).
- `legacy_kern_pairs.py <scratch> <shipped.ttf>...`: when a release kerns with a legacy `kern`
  table and its source through a GPOS kern feature, which kerned pairs does HarfBuzz shape
  differently? (results/legacy-kern-pairs.txt)
- `check_weight_class_refactor.py <.glyphs>...`: does tools/workarounds.py's weight_class
  behave exactly as before its FEA writer was split out (for the binaries' usWeightClass)?
- `babelfont/rebuild.sh <empty dir>`: rebuilds the babelfont the "after" runs used, from public
  upstream plus `babelfont/measure-integration.diff`, and checks it is the measured tree. The
  patch series in `babelfont/sr-aef-uncompile-fixes/` and `babelfont/ttf-static-font-fidelity/`
  are the same changes, commit by commit, for review (pr-bodies/ has their PR texts).
- `babelfont/refresh.sh`: after a converter change, regenerates the patch series, the
  integration diff and rebuild.sh's checksum from the babelfont branches, and checks that the
  diff applied to public upstream gives exactly the measured tree.

## Results

See `RESULTS.md`: the runs, the exact tool revisions and the inputs they were measured on.
