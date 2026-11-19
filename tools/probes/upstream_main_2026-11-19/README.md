# Does babelfont-rs main of 2026-11-19 land more of the backlog clean?

Question answered: with babelfont-rs main f253aa84 (Simon Cozens's FontLab work of 2026-11-16..18,
"Remove dead mark classes from layout rules", the fontc v2 move, and our merged #139) as the
converter instead of our pinned branches, which backlog families land CLEAN or closer to it?

Backlog (`backlog.tsv`): every family in families*.tsv that is not CLEAN or CLEAN-DISCLOSED in its
ledger and not pushed, leaving out those that fail only hinting and those waiting for hinting before
their first landing (Bonbon, Federo, Iceberg, Iceland, Lancelot, Poller One): 21 SFD, 3 binary-route,
40 VFB families. Each is landed into scratch with tools/land.py (recipe flags main does not know are
dropped, recipe.NOT_YET_UPSTREAM); builder gftools-rust 1e638bd, fontc 1.0.0.

| file                              | question it answers                                                       | command                                                                                            |
|-----------------------------------|---------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| sweep.sh                          | land every backlog family with a given babelfont-rs worktree              | `[LAND_ARGS=--unpublished-converter] sh sweep.sh <scratch> <babelfont-rs worktree> [backlog file]` |
| compare.py                        | how does each new verdict compare with the ledger's (hinting set aside)?  | `python3 -I compare.py <results.tsv>`                                                              |
| results-main-f253aa84.tsv         | sweep of all 64 with main                                                 | -                                                                                                  |
| results-vfb-layerfix-46603a17.tsv | the 40 VFB families with main plus our free-floating-layer fix (46603a17) | -                                                                                                  |

Hinting is set aside because land.py applies a release's own hinting only on the opt-in route
(HINTING_EXTRACT), which waits for gftools-rust#2: every instructed family fails it whatever the
converter. HINTING-ONLY = 0 table rows and no other failing check: CLEAN once hinting is applied.

## Results (compare-main-f253aa84.txt, compare-vfb-layerfix-46603a17.txt)

No family lands CLEAN with main. SFD and binary-route families (24):

| outcome                                               | families                                                                                                                                                                                                     |
|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hinting-only now (was gdef+names+shaping)             | Smythe                                                                                                                                                                                                       |
| near: 3 GSUB structural rows per style, shaping equal | Play (was 718 rows, six failing checks)                                                                                                                                                                      |
| names now pass, other checks remain                   | Nosifer, Nova Mono, Tuffy, UnifrakturMaguntia, Corben, Comic Relief, Lohit Bengali, Lohit Tamil, Overlock (4 of 6 styles hinting-only), Poly, Ribeye Marrow, Sanchez, Thabit (1846 rows to 12), Varela, Viga |
| builds now (did not before), residual                 | Cardo                                                                                                                                                                                                        |
| worse than our branches                               | Miama, Ultra (advancing combining marks get width 0: our #110); Passion One Black, Overlock Black (typographic family names: our typographic-family-names branch)                                            |

VFB families (40):

| converter        | do not build | build, residual | what stops the build                                                                                                                                                                                                                |
|------------------|--------------|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| main             | 27           | 13              | the mask and img layers are written free-floating, as master layers of masters that do not exist ("missing master 'img'")                                                                                                           |
| main + layer fix | 21           | 19              | 20: the VFB's own kern feature names FontLab kerning classes (@_kernA_leftpair) that main now turns into kerning groups and no longer defines (Aclonica: 2595 FEA errors); Stardos Stencil: fontc stalls ("122 jobs stuck pending") |

The 19 that build are worse than with our VFB branch (more table rows; line spacing and names
fail where our branch applied FontLab's export rules, which are to become source edits).
