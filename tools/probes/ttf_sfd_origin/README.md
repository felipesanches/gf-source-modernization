# Are our "-TTF.sfd" sources imports of the binaries, and what if we convert the binaries instead?

Prompted by Simon on google/fonts#10490 (2026-05-01): the "-Regular-TTF"/"-OTF" .sfd/.vfb files are
"batch-converted from the binary files ... my advice would be to generate fresh sources using babelfont
from the existing Google Fonts binaries" (notes/simon-feedback-audit-2026-11-03, P13).

| script                     | question it answers                                                                                                                                                 | command                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| origin.py                  | is each -TTF/-OTF .sfd we convert an import (quadratic + TrueType instructions or a .vfb twin)?                                                                     | `python3 -I tools/probes/ttf_sfd_origin/origin.py > results-<date>.tsv` |
| reland_from_binary.sh      | do the unpublished imports land CLEAN from their binaries, with the published converter (felipesanches/babelfont-rs 2026-11-02, 26fdcfa9) and no open FontForge PR? | `sh tools/probes/ttf_sfd_origin/reland_from_binary.sh`                  |
| reland_from_binary_gdef.sh | of the RESIDUAL ones, which land CLEAN once the source states the release's GDEF classes (plan key gdef_classes_fea, as Carlito)?                                   | `sh tools/probes/ttf_sfd_origin/reland_from_binary_gdef.sh`             |

Inputs: families-from-binary.tsv (40 repositories, 68 styles; binary rows at google/fonts 2fe1e8c6b,
written as <repo>-bin so no SFD plan applies). Landings, scratch and per-repository logs go to
the scratch directory (TMPDIR) ttfimport-from-binary-2026-11-03/ (regenerable; the logs name unpublished scratch
commits, so they stay out of this repository).

## Results, 2026-11-03

results-2026-11-03.tsv: 124 -TTF.sfd styles in 84 repositories; 123 quadratic, 112 also with TrueType
instructions or a .vfb twin; Ultra unreadable. Per repository: 81 IMPORT (43 published, 38 not), 2 likely
(titilliumweb, tuffy), 1 unknown.

results-from-binary-2026-11-03.md: the 40 unpublished imports, on three routes.

| route                                                  | CLEAN |
|--------------------------------------------------------|-------|
| .sfd, published babelfont (reland-2026-10-21-upstream) | 2     |
| .sfd, all 13 open PRs (reland-2026-10-24-integration)  | 25    |
| the binary, published converter                        | 13    |
| the binary + a documented GDEF-classes statement       | 27    |

The binary route loses one: Abril Fatface (its binary does not build; it stays on the .sfd route, CLEAN).
Of the 13 still RESIDUAL from the binary, seven fail only table rows or one functional check (poly,
ribeyemarrow, sanchez, smokum, tuffy, nosifercaps, overlock); cardo, miama, nosifer, varela, viga fail
shaping. The GDEF statement is the font's own source stating classes no category expresses -- what Simon
called "a matter for its source" (babelfont#131) -- and needs land.py to allow a documented source-edit
commit after a binary's conversion (today it sits inside the convert commit, as in carlito).

## The VFB imports, 2026-11-03

families-vfb-from-binary.tsv: the 100 repositories (120 styles) of families-vfb.tsv whose .vfb is a "-TTF"/"-OTF"
FontLab import; reland_vfb_from_binary.sh lands them from their binaries (summary-vfb-from-binary-2026-11-03.txt).

| route                                                       | CLEAN |
|-------------------------------------------------------------|-------|
| .vfb, every local VFB branch (reland-vfb-fixes4-2026-10-29) | 0     |
| the binary, published converter                             | 55    |

Of the 45 RESIDUAL from the binary, 39 differ only in table-gate rows (functional PASS on every style); 6
fail a functional check or do not build. The GDEF-statement pass (reland_vfb_from_binary_gdef.sh,
summary-vfb-from-binary-gdef-2026-11-03.txt) makes one more CLEAN: unlike the SFD imports, the VFB residuals are
not class problems. 41 of the 44 left block only on GSUB.feature_list / GSUB.lookup_list -- lookups renumbered
or repacked (e.g. Audiowide's frac and ordn), shaping identical: fontc problems 12 and 13
(gfonts-ai-usage-report 22-fontc-problems), which the 2026-10-02 decision discloses rather than works around.
