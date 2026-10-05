# What still fails after the 2026-10-02 re-land, and what fixes it

## Current status (2026-10-02, after every pending fix)

Combined view `logs/reland-2026-10-02-current` (+ `-langsys`): **151 styles, 127 functional
PASS, 122 CLEAN, 0 regressions** (from 52 / 51 in `reland-2026-10-01-names-v2`). Converter
babelfont integration-all (upstream main + #101..#106 + 20 unpushed branches, PR-QUEUE 1-2),
recipe = tools/recipe.py + pending/recipe-combined.patch. Poly-Italic CLEAN since -langsys.

Every remaining failure is disclosed in its repo's README (plans/<repo>.json "disclose"):
- fontc-only (gfonts-ai-usage-report/22-fontc-problems.pdf, problems 1-20): Varela, Viga,
  UnifrakturMaguntia, NovaMono, Cardo x3, Kristi, NovaScript, NosiferCaps,
  Overlock-BlackItalic, Thabit-Oblique, Thabit-BoldOblique, Miama, Ultra, Nosifer (legacy
  `kern`), RibeyeMarrow (table rows only), Play x2.
- decided 2026-10-01 (stale side bearings): Corben-Bold, Limelight, MrBedfort, Niconne,
  NixieOne, RougeScript.
Play: glyphslib-rs #4 merged 2026-10-02; it still needs a gftools-builder release whose glyphslib has #4 (via babelfont) before it can be pushed.

The rest of this file is the 2026-10-02 morning snapshot it started from.

**Model**: Claude Opus 5.5. Measured 2026-10-02.

Run: `logs/reland-2026-10-02-final/` (README there says which repos come from which run).
Converter: babelfont integration `eae493be` = upstream main f6c4ef0f + #101 + #102 + #103 +
#104 (with bad16b09) + #105 + #106; builder gftools-rust ade8776 (fontc 1.0.0). Recipe:
gf-source-modernization `tools/recipe.py` as committed with this file.

**149 styles: 108 pass the functional gate, 105 CLEAN** (was 52 / 51 in
`reland-2026-10-01-names-v2`; 0 regressions, `compare-2026-10-01-names-v2.tsv`).
Per style and check: `triage.tsv`. Rerun:

    python3 tools/reland_triage.py 2026-10-02-final
    python3 tools/compare_runs.py 2026-10-01-names-v2 2026-10-02-final

## The 41 failing styles, by what would fix them

| group | styles | cause | fix (PLAN-2026-10-01-followup.md item) |
|---|---|---|---|
| A. decided: disclose | Corben-Bold, Limelight, MrBedfort, Niconne, NixieOne, RougeScript (6) | stale side bearings only (diag/*.g2.txt: every failing glyph STALE-LSB) | none; disclosed in plans/*.json. Gate cannot pass these. |
| B. decided: disclose | Miama, Ultra, Nosifer (3) | release has only a legacy `kern` table (no GDEF/GPOS/GSUB); also Miama italic flag, Nosifer .notdef | disclosed; Nosifer also gets fix 8 |
| C. names: typographic family | TitilliumWeb Black/Light/LightItalic/SemiBold/SemiBoldItalic, Overlock-Black, Overlock-BlackItalic, PassionOne-Black (8) | release states IDs 1/2/4 as a RIBBI style of a typographic family; babelfont has no IDs 16/17 model | new babelfont change; 7 of the 8 fail on names alone |
| D. .notdef | Corben-Regular, Kristi, NosiferCaps, Nosifer (+Thabit, Tuffy-Italic) | FontForge synthesized a .notdef the source lacks | fix 8 `--fontforge-notdef` |
| E. empty GPOS / mark positioning | Varela, Viga, UnifrakturMaguntia, NovaMono | release has GPOS without lookups for marks; fontc writes mark lookups | section 4 compiler item; Viga disclosed |
| F. vertical metrics edits not yet written | MountainsofChristmas-Bold, NothingYouCouldDo (+Unifraktur) | source metrics differ from the release | section 2 edits (next-vmetrics) |
| G. per-family source decisions | Play x2, Tuffy-Regular/Italic, Thabit x2 (6) | wrong source for what shipped | Play from alexeiva/play (needs glyphslib-rs #4); Tuffy v1.272 edits; Thabit mergepsfont/mergefea |
| H. Cardo | Cardo x3 | base+mark shaping, advances, cmap | fix 10 (Cardo items) |
| I. pairing | Lohit-Bengali, Lohit-Tamil | paired with the wrong revision | section 3: 0df83ad / 361b23b |
| J. Comic Relief | ComicRelief x2 | sfdLib 2.0.0 outlines, localized names (IDs 2/17/22 in other languages), underline position | fix 11 + localized Name Table Entries |
| K. italic flag | Kristi, NovaScript | fontc sets ITALIC from the italic angle | disclosed (decided) |
| L. Wallpoet | Wallpoet (1) | FIXED 2026-10-02: gftools-rust decomposed the flipped component by default; config.yaml now says decomposeTransformedComponents: false (logs/reland-2026-10-02-components) | done |
| M. Overlock-BlackItalic line spacing | 1 | fontc 1.0.0 misses "Italic" in the master name | section 4: gftools-rust fontc bump |

Groups A, B and K are decided (disclose): 9 styles that functionally match except for
documented differences. The largest open single fix is C (8 styles).

## How the 2026-10-02 regressions were resolved (for the record)

- Russo One, Lekton x3, Cardo did not build: the GDEF class list named `.ttfautohint`,
  which fea-rs rejects. Fixed in #104 (bad16b09): names FEA cannot spell are left out.
- Miama, Ultra, Nosifer gained a GDEF table: their releases were exported without OpenType
  layout (FontForge 20110222 tottf.c: otf_dumpgdef runs only in opentype mode), so they
  have only `kern`. The recipe now passes `--fontforge-gdef-classes` only when the release
  has GDEF. #104 also skips the table when every glyph is a base (FontForge's rule).

## Scripts (copied from the 2026-10-01 outlines investigation)

| script | question | run |
|---|---|---|
| scripts/build_repo.sh | build a landed repo's sources in scratch | `sh scripts/build_repo.sh <repo> <sources dir> <build name>` (writes under ~/compartilhado/tmp/reland-research/outlines/builds/) |
| scripts/diagnose.py | which glyphs fail the gate's geometry test and why (STALE-LSB, SHIFT, ROUND1, MOVED, STRUCT, COMPONENT, ADV) | `python3 scripts/diagnose.py <shipped.ttf> <built.ttf> <workdir> > diag/<style>.g2.txt` |
| scripts/dumpglyph.py | a glyph's points, hmtx, xMin and components in each font | `python3 scripts/dumpglyph.py <glyph> <font>...` |

Python: /home/fsanches/compartilhado/gftools/venv/bin/python3 (fontTools, freetype-py).
