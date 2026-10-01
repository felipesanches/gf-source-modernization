# Patches kept out of upstream PRs

| patch | what | why it is not in a PR |
|---|---|---|
| `0001-Add-a-filter-to-drop-FontForge-AltUni-alternate-code.patch` | babelfont-rs `--drop-alternate-unicodes` (was 02f76b2 in PR #93, based on 496e904) | Nothing uses it. Its premise (FontForge's export omits AltUni alternates) was wrong, and dropping alternates lost 88 codepoints the releases carry in 54 of 100 families (sfd-batch5/REGATE_FINDINGS.md, updates 10-11). Removed from #93 on 2026-09-30. |

Apply with `git am <patch>` on a babelfont-rs checkout (may need a rebase onto current main).
| `0001-Add-a-filter-to-reverse-every-closed-contour.patch` | babelfont-rs `--reverse-path-direction` (was 5d759d8 in PR #93, based on 496e904) | Not needed: builder3's `reverseOutlineDirection: false` (fontc `--keep-direction`) gives the same result. Lekton Italic converted without the filter and built with `--keep-direction` matched the filter + default build in all 199 outlined glyphs (points and directions; probe `GoogleFonts/data/babelfont-pr93-split/cmp_dirs.py`). Removed from #93 on 2026-10-01 at Simon's question. Re-landed repos that used it need `reverseOutlineDirection: false` in config.yaml instead. |
