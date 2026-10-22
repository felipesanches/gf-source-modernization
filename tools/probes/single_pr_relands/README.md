# Which waiting repositories does ONE babelfont PR unblock?

Question: of the 49 SFD repositories that land RESIDUAL on babelfont upstream main 5ff5bf04
(logs/reland-2026-10-21-upstream), which land CLEAN when a single open babelfont PR is added?
The repositories tried for each PR are those whose upstream failures are that PR's symptom
(logs/reland-2026-10-21-upstream/triage.tsv):

| PR   | branch                        | symptom on upstream                                  |
|------|-------------------------------|------------------------------------------------------|
| #106 | fontforge-legacy-os2-version  | line_spacing: USE_TYPO_METRICS set by the build      |
| #104 | fontforge-gdef-classes        | gdef: GDEF absent / classes differ; shaping: singles |
| #105 | fontforge-shadowed-kern-pairs | shaping: pairs (kerning)                             |

Converter per PR: a scratch worktree of upstream main 5ff5bf04 with the PR branch merged
(the reworked branch head that PR-QUEUE section 2 pushes; #104's merge needed the two
appended test blocks in fontforge/tests.rs kept side by side), built with
tools/build_babelfont.sh. Builder: land.py's default. Landings went to scratch.

    sh tools/probes/single_pr_relands/run.sh <scratch dir with worktrees u104 u105 u106>

Result (result-2026-10-22.tsv, first line of each logs/reland-2026-10-22-u<PR>/<repo>.log;
the per-repository logs stay out of this repository until those repositories are pushed):

| PR alone | CLEAN                                                                                                          |
|----------|----------------------------------------------------------------------------------------------------------------|
| #106     | lekton, lilitaone, megrim, mountainsofchristmas, nothingyoucoulddo, revalia (6)                                |
| #104     | kottaone, macondo, monoton, oleoscript, oleoscriptswashcaps, poly, ruluko, salsa, smythe, titanone, unifrakturcook (11) |
| #105     | italiana, sanchez (2)                                                                                          |

Still RESIDUAL with one PR, and what is left:
- patrickhand, lustria: #106 leaves only the gdef/shaping failure, #104 only line_spacing
  (so both PRs together; not landed with both yet).
- passionone: #104 leaves PassionOne-Black's names (IDs 16/17: typographic-family-names).
- comicrelief: #104 leaves names (localized IDs 2/17/22: #117).
- tuffy: #104 fixes Bold and BoldItalic; Regular and Italic keep .notdef (#120) and
  localized ID 17 (#117).
- lohitbengali, lohittamil: #106 leaves shaping and rendering (and Tamil's advances).
- limelight: #106 leaves only rendering, the disclosed stale side bearings (bottleneck 7).
