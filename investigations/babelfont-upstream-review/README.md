# babelfont upstream PRs -- review record

The 13 fork-only babelfont commits were split into three PR branches
(pr-ff-reader-fixes, pr-ff-source-fidelity, pr-ff-os2-defaults) and put through
adversarial review rounds, each ending with the 42-style conversion-equivalence probe.

| file | what it is |
|---|---|
| `round1-journal.jsonl` | split + first reviews + first equivalence run (workflow wf_75a9b1e2-715) |
| `round2-journal.jsonl` | fixes, second reviews, equivalence (wf_76bdd634-85d) |
| `round3-journal.jsonl` | fixes, third reviews, equivalence (wf_d1edad54-5c5) |
| `agent-scripts/<agent>/` | the agents' own one-off wrappers and helpers, kept verbatim because the numbers in the journals came from them; they hard-code session-scratch paths and will not run as they are |

To reproduce the numbers rather than replay the agents, use the canonical scripts:

- `../../tools/babelfont-upstream/check_branch.sh <branch>` -- fmt / clippy / test counts
  for a branch and upstream/main (what each PR body quotes)
- `../../tools/probes/upstream_prs_equivalence/run.py` -- do PR 90 + the three branches
  convert every style exactly as 8b59bc3 did (42/42 in every round so far)
