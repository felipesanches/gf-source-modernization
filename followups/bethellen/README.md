# Beth Ellen follow-up: the 2019 outline revision

Branch `followup-2019-outline-revision` of googlefonts/BethEllen, stacked on the landing
`modernize-sfd-to-glyphs` (logs/bethellen-2026-11-19). It takes the Glyphs revision Felipe
made after the release (0bb8bdf, 354558f, May 2019; never shipped) as the source. Not an
equivalence change: every difference below is for design review and QA.

| commit                                               | what                                                              |
|------------------------------------------------------|-------------------------------------------------------------------|
| Take the 2019 outline revision as the source         | sources/BethEllen-Regular.glyphs = 354558f's, byte-identical      |
| State the release's underline position and thickness | -249 / 99, which the 2019 file did not state (it built -100 / 50) |

## Round 1 measurement (measure-2e9f690.txt)

`python3 -I tools/followup/measure.py <worktree> BethEllen-Regular=<google/fonts>/ofl/bethellen/BethEllen-Regular.ttf`
(builder 1e638bd, google/fonts c36d6f24). Against the shipped font:

| area           | change                                                                                                                          | for review                                         |
|----------------|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| outlines       | 116 of 231 changed outlines draw different ink; accented capitals most (Atilde, Agrave, ...)                                    | the redesign itself                                |
| accents        | accented letters become base + combining mark (mark feature, 7 new marks U+0300-0327); 56 advances change (Aacute 1529 -> 1731) | intended? accented widths now equal the base's     |
| alternates     | 16 asterisk alternates and question.alt1 lose their FontForge PUA codepoints (U+F009-F035) and are unreachable                  | reach them through a feature (salt/ss01), or drop? |
| GSUB           | aalt changes (1404 of 1494 runs differ); the question.alt1 single substitution goes                                             | which alternates aalt should list                  |
| cmap           | CR and LF go; U+0131 dotlessi becomes idotless (same outline)                                                                   | fine for Google Fonts                              |
| OS/2           | fsType 0 -> 8; sub/superscript size and offset become Glyphs defaults                                                           | fsType must be 0 for Google Fonts: fix             |
| shaping        | 150,839 of 549,210 runs differ (pairs, words: the outline and accent changes)                                                   | follows from the above                             |
| names, spacing | names, line spacing, hinting, GDEF pass                                                                                         | -                                                  |

The visual report: `diffenator3 --html --output <dir> <shipped.ttf> <build.ttf>` (diffenator3 of
tools/land.py D3), regenerable from the branch with measure.py's build.
