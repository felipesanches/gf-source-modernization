# Open PRs: conflicts and reviewers' comments

| script         | question it answers                                                                              | command                                                                                   |
|----------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `conflicts.sh` | which open PR heads, and which local branches, merge with the repository's main without conflict | `sh tools/probes/open_prs/conflicts.sh <babelfont-rs clone> simoncozens/babelfont-rs <branch>...` |
| `comments.sh`  | what others have said on felipesanches's open PRs since a date                                   | `sh tools/probes/open_prs/comments.sh simoncozens/babelfont-rs 2026-09-01 <scratch dir>`  |

Signal: `git merge-tree --write-tree` exits 0 for a clean merge and 1 for a conflict (git 2.47 has no
`--quiet`; behind `2>/dev/null` its usage error, exit 129, reads like a conflict). A squash-merged PR
still shows a conflict, so read the PR list against the open PRs (`comments.sh` writes `open.json`).
"refusing to merge unrelated histories" lines are old PR heads below #100 that share no history with main.

## 2026-11-03, simoncozens/babelfont-rs main a93e1325

`results-2026-11-03-babelfont.txt`: of the 14 open PRs by felipesanches, the GitHub heads of 7 conflict
with main (#105 #108 #109 #110 #117 #119 #120); every local branch (the 13 merge-carrying PR branches,
typographic-family-names, glyphs3-family-ids-entries) merges clean. The local heads are not pushed yet.

`results-2026-11-03-babelfont-comments.txt`: unanswered since 2026-10-02/04 -- #105 (Simon), #120
(Simon, twice), #121 (Simon, Khaled). Their replies are drafted in pr-bodies/replies-2026-10-02/ and
the reworks are commits on the local branches.

logs/babelfont-verify-2026-11-03 built #117 at a merge of a93e1325 into its local head, since dropped, a merge of a93e1325 into its local head that was then
dropped (the branch stays at its local head): its tree, the same tree, is the tree `git merge-tree --write-tree
a93e1325 its local head` gives, i.e. what GitHub builds for the PR once its local head is pushed (kept as
refs/backup/glyphs3-localized-name-entries-merge-a93e1325).
