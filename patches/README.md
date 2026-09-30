# Patches kept out of upstream PRs

| patch | what | why it is not in a PR |
|---|---|---|
| `0001-Add-a-filter-to-drop-FontForge-AltUni-alternate-code.patch` | babelfont-rs `--drop-alternate-unicodes` (was 02f76b2 in PR #93, based on 496e904) | Nothing uses it. Its premise (FontForge's export omits AltUni alternates) was wrong, and dropping alternates lost 88 codepoints the releases carry in 54 of 100 families (sfd-batch5/REGATE_FINDINGS.md, updates 10-11). Removed from #93 on 2026-09-30. |

Apply with `git am <patch>` on a babelfont-rs checkout (may need a rebase onto current main).
