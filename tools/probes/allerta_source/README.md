# Which `.sfd` was Allerta mastered from, and does it land today?

Bottleneck item 4 (2026-10-22): the Allerta Stencil landing goes into googlefonts/allerta, which
already holds Felipe's 2026 conversion of Allerta, and edits the shared config; option (a) is to
re-land Allerta Regular in today's pipeline beside the Stencil and re-pin both. Before deciding:
does Allerta Regular land CLEAN from its `.sfd` today, and from which of the two `.sfd` files
librefonts/allerta keeps per family (`src/<Family>-TTF.sfd` and `src/<Family>.sfd`; their
headers differ: Version 001.001 / 1.0, UnderlinePosition -50 / -51, OS2Version 2 / 3)?

Four scratch landings with tools/land.py (both gates), babelfont upstream main 5ff5bf04, no plan
(no edit), each from librefonts/allerta at 88a8c57b (what google/fonts pins for the Stencil):

    FAMILIES=tools/probes/allerta_source/families-allerta.tsv BF_TREE=<5ff5bf04 worktree> \
      OUT=<s>/repos LANDED=<s>/landed.tsv SCRATCH=<s>/scratch python3 tools/land.py <row> --rebuild

Result (result-2026-10-24.txt): from `-TTF.sfd`, Allerta Regular and Allerta Stencil both land
**CLEAN** (0 blocking rows, functional PASS, 0 edits). From the plain `.sfd`, both give 23 blocking
rows (OS/2 sub/superscript sizes 717/666 against 700/650, ...) and fail cmap, shaping, rendering,
names, line spacing and advances: the `-TTF.sfd` is the master of the shipped fonts, as the
Stencil row of families.tsv already assumed. The underline values the earlier probe missed in the
pinned repository (tools/probes/allerta_shared_config) are right in today's pipeline.
