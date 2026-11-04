# Default-branch audit of our METADATA.pb source blocks (2026-11-04)

Question: does every METADATA.pb source block that points at one of our googlefonts repositories record a commit on that repository's default branch on GitHub (standing rule, Felipe 2026-11-04)?

    python3 tools/audit_metadata_branches.py <google/fonts clone> upstream/main <the pending branches of PR-QUEUE and PR-BACKLOG>

Answer, on google/fonts main 8c3ea2498: all 95 source blocks on main are OK, and so is the Abril Fatface branch. The three branches that fail (50 blocks) are not to be pushed as they are: two disclosed branches name repositories not pushed yet (they are regenerated with metadata.py after the pushes), and the September branch is superseded. Commit ids of unpushed repositories are left out of this copy; the rows are counted below.

| where                                   | source blocks | OK | not OK | why                                             |
|-----------------------------------------|---------------|----|--------|-------------------------------------------------|
| google/fonts main                       | 95            | 95 | 0      |                                                 |
| source-metadata-abrilfatface-2026-11-04 | 1             | 1  | 0      |                                                 |
| source-metadata-disclosed-2026-11-02    | 9             | 0  | 9      | repositories not pushed yet (bottleneck 7)      |
| source-metadata-disclosed-2026-11-02b   | 14            | 0  | 14     | repositories not pushed yet (bottlenecks 9, 11) |
| sfd-reland-sources-2026-09              | 27            | 0  | 27     | superseded September branch, never to push      |

`ok-rows.md`: the 96 OK rows (public commits); the 50 others are counted above.

After google/fonts #11234-#11237 merged (main bbda7253f): 176 of 176 source blocks that point at our repositories are on the default branch (`main-after-11237.md`, written by the tool as is; it now links every commit and retries a failed `ls-remote`).
