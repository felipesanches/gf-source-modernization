# babelfont upstream split -- the rewrite tools

The 13 fork-only commits on gf-sfd-conversion (8b59bc3) were split into three branches
off simoncozens/babelfont-rs main 6ab2312: pr-ff-reader-fixes, pr-ff-source-fidelity,
pr-ff-os2-defaults. These scripts are the exact record of how their comments and
messages were rewritten (for Simon's "no SFD/fontc irrelevancies" review rule); the code
was not changed by them.

| script | what it did | how it was run |
|---|---|---|
| `rewrite_comments.py` | exact-text substitutions in `//`, `///` and CLI help lines per file, then `normalize_modrs.py` | `git filter-branch --tree-filter 'python3 .../rewrite_comments.py' upstream/main..<branch>` |
| `normalize_modrs.py` | places the FontForge filter registrations in `filters/mod.rs` under the --help headings they have in 8b59bc3 | called by rewrite_comments.py, from the repo root |
| `rewrite_msg.py` | drops "(cherry picked from ...)" lines, sets the AI-attribution trailer | `git filter-branch --msg-filter` |

Whether the split changed behaviour is answered separately, by
`tools/probes/upstream_prs_equivalence/` (42 of 42 styles byte-identical to 8b59bc3).
