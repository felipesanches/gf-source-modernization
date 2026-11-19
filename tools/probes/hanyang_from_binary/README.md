# The eight HanYang families: convert from the binaries?

google/fonts takes Batang, BatangChe, Gungsuh and GungsuhChe from googlefonts/batang (6c1e09f),
and Gulim, GulimChe, Dotum and DotumChe from googlefonts/gulim (012723a). Neither repository has an
outline source: process.py and a Makefile run the vendor's TTFs (sources/) into fonts/ttc and
fonts/ttf/{bitmap,hinted,unhinted}. google/fonts ships the hinted TTFs, edited after onboarding
(f203c090b "Updated metadata and vertical metrics", 9ade71526), so the shipped files are not the
repositories' files. Both repositories are archived on GitHub (2026-11-19).

| file                   | question it answers                                                                 | command                                                            |
|------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| run_probe.sh           | do the shipped binaries convert and rebuild to the release, under the landing gates? | `sh tools/probes/hanyang_from_binary/run_probe.sh <scratch dir>`   |
| results-2026-11-19.txt | run_probe.sh's output: google/fonts c36d6f24, babelfont 26fdcfa9, builder 1e638bd    | -                                                                  |

## Results, 2026-11-19

All eight are RESIDUAL, about 22,500-22,800 glyphs each. The functional gate passes cmap, shaping
(1,961,806 runs for Batang, 0 differ), rendering, names, line spacing and advances everywhere.
What remains:

| difference                                                   | fonts | what it is                                                                                                                                         |
|--------------------------------------------------------------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| hinting (glyph programs, fpgm, cvt, prep, gasp)              | 8     | full TrueType hinting; waits for gftools-rust#2                                                                                                    |
| GSUB.lookup_list                                             | 8     | names only: the release is post format 3, so fontTools names glyphs `space`, the build `uni0020`; the `vert` lookup is equal glyph index by index |
| head.font_direction_hint 1 vs 2                              | 8     | deprecated field a .glyphs source cannot state; disclosed elsewhere (plans/nanummyeongjo.json)                                                     |
| vhea.version 1.0 vs 1.1                                      | 8     | fontc writes 1.1                                                                                                                                   |
| vhea min top/bottom side bearing, y_max_extent               | 5     | the release's values disagree with its own vmtx (min tsb 0 there); fontc computes them from the outlines, consistent with the vmtx, which is equal |
| post.isFixedPitch 1 vs 0 (the four Che fonts, "advances")    | 4     | probe.py does not apply land.py's fixed-pitch workaround (tools/workarounds.py); a landing states it                                               |

by_index.py compares tables with every glyph renamed to its index (`python3 -I
tools/probes/hanyang_from_binary/by_index.py <release.ttf> <build.ttf>`). On Batang-Regular (the
release against run_probe.sh's build): vmtx equal, GSUB equal, hmtx different in one entry only,
the empty `.notdef` (left side bearing 154 in the release, 0 in the build; no outline to place).

The repositories' layout (what the conversion does with process.py, the vendor TTFs and the TTC
and bitmap outputs) waits for Aaron (Felipe, 2026-11-19).
