# play -- landing from the Glyphs source

**Model**: Claude Opus 5.5. **Date**: 2026-10-02.

Decision (Felipe, 2026-10-01): play is represented by alexeiva/play `sources/Play.glyphs`
at d84ad58 (v2.101), the source of the release (FINDINGS.md). families.tsv rows of kind
`glyphs` (tools/make_families.py `GLYPHS`) make tools/land.py build googlefonts/play as
that upstream history + the template commit + one commit adding `sources/config.yaml`.
No converter runs, so none is cited. The hg `.sfd`, librefonts/play, the 2016 `.glyphs`/
`.vfb` and m4rc1e/play are recorded in the README via plans/play.json `earlier_sources`.

## The builder variant (glyphslib-rs PR #4)

Play.glyphs is Glyphs 2 with unquoted all-digit hex unicodes (`unicode = 2013;`).
glyphslib-rs 0.2.8 reads them as decimal; PR #4 ("glyphs2: read an unquoted all-digit hex
unicode as hex", felipesanches/glyphslib-rs `fix-v2-unquoted-hex-unicode` 27cb8bf, = v0.2.8
plus that commit) fixes it, still unmerged on 2026-10-02. To measure before it merges:

    sh builder-pr4/build.sh /home/fsanches/compartilhado/tmp/agent-play     # ~2 min with a warm target
    # -> /home/fsanches/compartilhado/tmp/agent-play/target/release/gftools-builder

It builds gftools-rust ade8776 (the B3 land.py cites) in a clone, with
`--config 'patch.crates-io.glyphslib.path=...'`; no tracked file anywhere changes. land.py
takes it as `B3=<path>` (+ `B3_NOTE=` for the commit message) and then marks the landing
`-UNPUBLISHED-BUILDER`, which push.sh refuses. Once #4 is merged and released, rebuild the
default B3 and re-land without `B3=`.

## Measurement

    cd sfd-reland
    env OUT=<scratch>/repos LANDED=<scratch>/landed.tsv LAND_ARGS=--unpublished-converter \
        B3=<scratch>/target/release/gftools-builder B3_NOTE="..." \
        sh tools/reland_all.sh 2026-10-02-play play

Logs: `logs/reland-2026-10-02-all/play.log` (before: the hg `.sfd`),
`logs/reland-2026-10-02-play-stock-builder/play.log` (Glyphs source, stock B3 ade8776),
`logs/reland-2026-10-02-play/play.log` (Glyphs source, B3 + #4),
`logs/reland-2026-10-02-play-fixes/play.log` (B3 + #4 + the non-fontc tool fixes,
`builder-fixes/build.sh`; see RESPONSIBILITY.md). Against google/fonts
b5efa9c32e8f:

| check | hg .sfd (before) | .glyphs, stock B3 | .glyphs, B3 + #4 (after) | B3 + #4 + tool fixes |
|---|---|---|---|---|
| table gate rows, Bold / Regular | 365 / 353 | 165 / 164 | 15 / 14 | 15 / 14 |
| cmap | FAIL, 134 lost | FAIL, 53 lost / 50 gained (hex read as decimal) | FAIL, 3 lost (FB00 FB03 FB04); 6 renamed, 7 renamed with other points | as B3 + #4 |
| shaping, runs differing (Bold) | 663931 of 1362608 | 166170 of 1295215 | 178400 of 1356073 (more codepoints shaped) | 178400 of 1356073 (unchanged) |
| rendering | FAIL, 246 glyph diffs | FAIL, 18 | FAIL, 18 glyph diffs, 48 outlines | as B3 + #4 (compared unhinted) |
| names | PASS | FAIL (as after) | FAIL (Bold usWeightClass; Regular ID 4/6) | FAIL Bold usWeightClass only (fontc); Regular PASS |
| line_spacing | FAIL (asc/desc) | FAIL, only underlinePosition | FAIL, only post.underlinePosition | FAIL, only post.underlinePosition |
| advances | FAIL, 174 differ | FAIL, 0 differ, 5 renamed | FAIL, 0 differ, 5 renamed glyphs | as B3 + #4 |
| gdef | FAIL | FAIL (as after) | FAIL, 0 class differences shaping reads | as B3 + #4 |
| hinting (not gated) | release ttfautohinted | unhinted | unhinted | autohinted (default args; the release used --increase-x-height=13) |

## What remains, classified

Which component owns each item, read from the code, and what was fixed:
`RESPONSIBILITY.md` (2026-10-02, later than the classification below; 5 and 10 are
fixed outside fontc, 5's usWeightClass and 1-4, 6-9 are fontc).

The release is the Glyphs.app export of d84ad58, ttfautohinted (FINDINGS.md: it differs
from that commit's fonts/ttf only in head.modified/checkSumAdjustment), so nothing is
**source** drift and no documented edit applies. Detail: `probes/glyphs_route_residuals.py`
-> `runs/glyphs_route_residuals.txt`.

**Tool** -- Glyphs.app export rules the static path (glyphslib -> babelfont 0.2.2
instancer -> fontc) does not reproduce:
1. No automatic `languagesystem`s: the file has no Languagesystems prefix, Glyphs.app
   synthesises DFLT/latn/cyrl/grek; the build has DFLT + a latn that holds only ccmp (from a
   `script latn;` inside ccmp). So liga/smcp/c2sc/aalt/case... never apply to Latin text
   ("office" -> o f f i c e): most shaping rows, GSUB script/feature list rows.
2. Zero-width marks: Glyphs.app shifts a nonspacing mark left by its width (acutecomb
   -299..-100); the build keeps the source x (100..299). Mark composites (uni03020303 ...)
   and mkmk positions move with it: rendering rows, base+mark(+mark) shaping.
3. Production names from a newer GlyphData: uni0122/uni0136.../uni0306.cy/CR where the
   release has Gcommaaccent/Kcommaaccent.../brevecombcy/nonmarkingreturn (GSUB.lookup_list,
   cmap "another name", advances "no counterpart").
4. GlyphData unicodes for ff/ffi/ffl (U+FB00/FB03/FB04) not assigned.
5. Instance data: Bold's Glyphs 2 `weightClass = Bold;` ignored (usWeightClass 400 vs 700);
   Regular named "Play" in IDs 4/6 instead of "Play Regular"/"Play-Regular".
6. panose bWeight (5/8 in the release, from the weight class) left 0.
7. post.underlinePosition: Glyphs.app writes the parameter + thickness/2 (-100 + 25 = -75).

**fontc-only** (encoding choices; disclose if they stay):
8. Mark attachment: release GDEF 1.0 MarkAttachClassDef + GPOS flags 256/512/768; build
   GDEF 1.2 mark filtering sets (flag 16). 16 GDEF glyph classes differ that no lookup reads.
9. Cubic-to-quadratic conversion: 7 comma-accent glyphs differ in point count (U+0122: 43
   vs 44 points, same bbox).
10. Hinting: the release is ttfautohinted (sources/build.sh); the build is unhinted
   (reported, not gated).
