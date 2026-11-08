# Which open babelfont-rs PRs does a genuine FontForge original need? (2026-11-08)

Question: Simon's principle P13 makes the -TTF.sfd and -TTF.vfb families imports that convert from their binaries, so
several babelfont-rs PRs lost the families that justified them. Which PRs does one of the six genuine FontForge
originals we convert (Comic Relief, Thabit, Lohit Bengali, Lohit Tamil, Kristi, Nova Mono) still need?

Method: each converter is babelfont-rs main [925bb242](https://github.com/simoncozens/babelfont-rs/commit/925bb242)
alone (u0), or main with one PR branch merged (or two, `a+b`). The six repositories land on each converter with
`tools/land.py <repo> --rebuild --unpublished-converter` into scratch (LANDED= set, so landed.tsv is untouched), and
`compare_need.py` prints every functional-gate line and per-style BLOCKING count that differs from u0. The branches
are the PR branches as of 2026-11-08, local heads (some commits not pushed yet), so their ids are not recorded here.

| file                     | question it answers / how to run                                                                      |
|--------------------------|-------------------------------------------------------------------------------------------------------|
| `run.sh`                 | lands the six on u0 and each branch: `sh run.sh`; combined: `BRANCHES="a+b" REPOS="thabit" sh run.sh` |
| `compare_need.py`        | what each converter changes versus u0: `python3 compare_need.py <scratch>`                            |
| `resolve_117_tfn.py`     | resolves the #117 x typographic-family-names conflict (keeps both sides) for the combined run         |
| `compare-2026-11-08.txt` | the output of `compare_need.py` for this run                                                          |

Result (gate lines versus u0; "differ" counts are shaping runs):

| PR                          | needed | what changes versus u0 on the six originals                                                           |
|-----------------------------|--------|-------------------------------------------------------------------------------------------------------|
| #119 fixed-pitch            | yes    | Nova Mono: post.isFixedPitch 0 -> 1, advances PASS                                                    |
| #120 notdef                 | yes    | Thabit x4: BLOCKING 3 -> 2, .notdef advance and ink fixed; Kristi: .notdef advance and ink fixed      |
| #106 legacy-os2-version     | yes    | line spacing equal in Thabit Regular and Oblique, Lohit Bengali, Lohit Tamil, Kristi                  |
| #110 spacing-marks          | yes    | Lohit Tamil: BLOCKING 2 -> 0, shaping 3104 -> 0 differ, rendering PASS                                |
| #112 ligature-anchors       | yes    | Thabit: shaping 577-865 -> 0-288 differ, confirmed word diffs 44-45 -> 0-1 per style                  |
| #111 no-anchor-propagation  | yes    | alone Thabit Regular/Bold 625/865 -> 577; with #112, all four Thabit styles 0 differ                  |
| #117 localized-name-entries | yes    | Comic Relief names PASS (72 rows each); Thabit 6 -> 2 rows                                            |
| typographic-family-names    | yes    | alone Thabit IDs 16/17/21/22 fixed; with #117, Thabit Regular PASS, others 6 -> 3 (Arabic ID 1/16/21) |
| #105 shadowed-kern-pairs    | no     | no difference                                                                                         |
| #109 ligature-carets        | no     | no difference                                                                                         |
| #104 gdef-classes           | no     | Comic Relief: the same 15 mark classes still differ, and GDEF becomes absent                          |

Not changed by any branch: hinting (all six), Comic Relief's 15 GDEF mark classes, Nova Mono's U+0308 (shaping,
rendering, GDEF absent), the Thabit and Kristi fsSelection/macStyle italic rows.
