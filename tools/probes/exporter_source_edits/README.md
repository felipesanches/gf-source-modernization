# exporter_source_edits

Four babelfont filters reproduced what an exporter did that the source does not state. Simon
declined that kind of filter (#107 closed, #115 "This feels wrong"), so on 2026-10-02 they
became documented `.sfd` edits in the font repositories instead, each its own commit
(`tools/sfd_edit.py` ops `truncateanchors`, `sfdlibinterpolated`, and `setfield` values):

| filter (no longer passed) | becomes | plans |
|---|---|---|
| `--fontforge-truncate-anchors` (#107) | `truncateanchors` | thabit (all 4 styles, one commit) |
| `--sfdlib-interpolated-points` (#115) | `sfdlibinterpolated` (and the plan drops `--round-coordinates`) | comicrelief (one commit per style) |
| `--fontforge-legacy-offset-metrics` (#114) | `setfield` win/hhea values, offsets 0 | mountainsofchristmas (Bold), nothingyoucoulddo, unifraktur |
| `--fontforge-underline-position=20190317` (#116) | `setfield UnderlinePosition -10` | comicrelief (both styles, one commit) |

All scripts run from the gf-source-modernization checkout and write only under `$TMPDIR/exporter-source-edits/`
(`TMPDIR=/home/fsanches/compartilhado/tmp/...`, never `/tmp`). `PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`.

## census.py -- which styles depend on the three recipe flags?

    $PY tools/probes/exporter_source_edits/census.py e2430fa     # plans before these edits

Reads every style's `.sfd` as `land.py` converts it (`sources.py`: archive + plan ops), before
any `truncateanchors`. Signals: `AnchorPoint` coordinates that are not integers, and of those
the ones whose otRound differs from truncation; for each, the release's GPOS anchors of that
glyph (TRUNC = the truncated pair is there and the rounded one is not). Underline: styles that got
`=20190317` (SFD 3.2 or FFTM >= 2018-12-28). Offset: styles that got
`--fontforge-legacy-offset-metrics` (FFTM < 2014-09-16) with offset-mode win/hhea fields.

Result 2026-10-02 (`CENSUS.txt`): fractional anchors only in Thabit -- Thabit 65 (61 round
differently), Thabit-Bold 16 (16), Thabit-Oblique 530 (323), Thabit-BoldOblique 366 (235); all
TRUNC in the release except one fathah anchor per oblique that is ambiguous (fathah has another
anchor at the rounded position). Underline: only ComicRelief-Regular/Bold (-185/175: old rule
-272, new rule -97, release -97). Offset: 80 styles get the flag; which of them it changes is
`convert_check.py`'s question.

## convert_check.py -- does each style convert exactly as it did with the flag?

    BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-all/target-heights/release/babelfont \
      $PY tools/probes/exporter_source_edits/convert_check.py <recipe.py with the flags> [<plans rev>]

`before` = plans at `<rev>` + the recipe that passes the filters (HEAD's `tools/recipe.py` with
`pending/recipe-combined.patch` applied); `after` = the working tree's plans + recipe. Pass:
the two `.glyphs` files are byte-identical.

Result 2026-10-02 (`CONVERT_CHECK.txt`, babelfont integration-all 5b7eb252): 145 of 149 styles
identical, including MountainsofChristmas-Bold, NothingYouCouldDo, UnifrakturMaguntia-Book,
Thabit and Thabit-Bold. Thabit-Oblique and Thabit-BoldOblique differ in one line each: an anchor
at `(-0,464)` with the filter (Rust's trunc keeps the sign) is `(0,464)` with the edit; both
compile to 0. Comic Relief differs by construction (the edit writes the implied on-curve points
out, and its plan drops `--round-coordinates`); `sfdlib_outline_check.py`,
`comic_build_check.py` and the re-land cover it.

## sfdlib_outline_check.py -- does `sfdlibinterpolated` state sfdLib's outline?

    A=/home/fsanches/compartilhado/upstream_repos/repo_archive/loudifier/Comic-Relief.git
    for s in Regular Bold; do
      git -C $A show 856315f5:sources/ComicRelief-$s.sfd > $TMPDIR/ComicRelief-$s.unedited.sfd
      cp $TMPDIR/ComicRelief-$s.unedited.sfd $TMPDIR/ComicRelief-$s.edited.sfd
      python3 tools/sfd_edit.py $TMPDIR/ComicRelief-$s.edited.sfd sfdlibinterpolated
      $PY tools/probes/exporter_source_edits/sfdlib_outline_check.py $TMPDIR/ComicRelief-$s.unedited.sfd \
          $TMPDIR/ComicRelief-$s.edited.sfd /home/fsanches/compartilhado/google/fonts/ofl/comicrelief/ComicRelief-$s.ttf
    done

Per touched glyph: `exact` (the edited contour minus the added 0x80 midpoints == sfdLib 2.0.0's
point list, same order and start), `truetype` (both with every exactly-implied on-curve point
dropped, as write-fonts does: what fontc builds from either), and `release` (the release glyf ==
sfdLib's list rounded with otRound, as a cycle in either direction).

Result 2026-10-02 (`SFDLIB_OUTLINES.txt`): Regular 22 glyphs (30 points), Bold 216 (1083):
exact, truetype and release all pass in every glyph. sfdLib source: `/home/fsanches/compartilhado/tmp/bf-issue123/sfdLib-2.0.0`
(PyPI sfdLib 2.0.0 sdist; `Lib/sfdLib/parser.py` line 394).

## comic_build_check.py -- how close do the built Comic Relief outlines come to the release?

    BF=<babelfont> B3=/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder \
      $PY tools/probes/exporter_source_edits/comic_build_check.py <recipe.py with the filters> [<plans rev>]

Builds both styles three ways -- (a) the babelfont filter (plans at `<rev>`, recipe with the
filters), (b) the edit with `--round-coordinates`, (c) the edit without it, as
plans/comicrelief.json now says -- and compares every simple glyph's outline with the
release's (contours as cycles in either direction, exactly-implied on-curve points dropped on
both sides). Result 2026-10-02 (`COMIC_BUILD.txt`): differing glyphs (a) Regular 9, Bold 31;
(b) 15, 211; (c) 9, 8 -- (c)'s are all among (a)'s. `--round-coordinates` reproduces
FontForge's rint, but this release was compiled by ufo2ft (otRound after decomposition, which
fontc does when the converter leaves coordinates alone); with the filter, the flagged points
escaped it only because the filter ran after it, while they were still implied on-curve points.

## test_ops.py -- the two new ops on tiny fixtures

    python3 tools/probes/exporter_source_edits/test_ops.py

Truncation toward zero (and the rest of the line kept), a flagged middle point, a flagged
closing segment (the contour restarts at the implied point before the old start), an exact
midpoint for a non-dyadic value, and the refusals (nothing to do, cubic layer, TrueType
instructions, open contour).

## The re-land

`logs/reland-2026-10-03-srcedits/` (see its README) is the re-land of the eight families with
these plans and the recipe without the four flags, compared with `logs/reland-2026-10-02-current`.
