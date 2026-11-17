# FontLab readers upstream on 2026-11-17, against our unpublished VFB work

Question answered: after the vfbreader release of 2026-11-17 (jenskutilek/vfbLib-rust 561ba5f, version 0.1.7, with Simon Cozens's changes of that day), what does the new reader change for the Google Fonts library's `.vfb` files, and how much of our unpublished babelfont-rs VFB branch does it replace?

Versions: vfbreader 0.1.6 = jenskutilek/vfbLib-rust e04d554; 0.1.7 = 561ba5f; babelfont-rs upstream main cc4d20e4; Python vfbLib 0.11.7. Our branch is local only (the VFB integration branch replayed onto cc4d20e4, then ported to vfbreader 0.1.7).

## Reader: 0.1.6 against 0.1.7

`vfb_reader_ab.sh <out.tsv> old=<vfbreader 0.1.6> new=<vfbreader 0.1.7>` runs each reader's own CLI (`cargo build --release` in vfbLib-rust) on every unique `.vfb` under `$C` and records ok / error / rc134 (abort after a panic). Columns: sha256 prefix, path, old, new.

| corpus                                                             | file                  | unique files | ok, ok | crash -> ok | ok -> error |
|--------------------------------------------------------------------|-----------------------|--------------|--------|-------------|-------------|
| the VFB landing clones (default `$C`)                              | `reader-ab.tsv`        | 50           | 49     | 1           | 0           |
| the 2026-09-04 inventory of every `.vfb` in the upstream repos     | `reader-ab-batch1.tsv` | 1419         | 1411   | 7           | 1           |

- Crash fixed (7): StardosStencil-Bold, five Palanquin files, Arvo_ita_MM_54_b_sorce. The issue drafted in `issues/vfbreader-global-guides-capacity-overflow.md` is no longer needed.
- New error (1): `ofl/bilboswashcaps/src/Bilbo-SwashCaps-OTF.vfb` of googlefonts/googlefontdirectory-hg. Its "OpenType Kerning Class Flags" entry (key 2026) is one byte, `8d`: a count of 2 and no class records. 0.1.6 kept the entry as raw bytes; 0.1.7 decodes it and stops with "failed to fill whole buffer ... while reading KerningClassFlags". Python vfbLib fails on the same entry (EOFError in OpenTypeKerningClassFlagsParser).

## Converter: what the new reader changes in our output

`convert_ab.sh <outdir> old=<babelfont> rebased=<babelfont> ported=<babelfont>` converts every unique `.vfb` of the landing clones to `.glyphs` with three builds: our branch before the rebase, replayed onto upstream main (vfbreader 0.1.6), and ported to vfbreader 0.1.7. `convert_ab_normalized.py <outdir> <a> <b>` compares two builds' outputs ignoring the run date and the random master ids. `convert-ab.tsv`: 49 files convert with all three; StardosStencil-Bold converts only with the ported build.

| comparison          | same | different | what differs                                                                 |
|---------------------|------|-----------|------------------------------------------------------------------------------|
| old -> rebased      | 0    | 49        | only `active = 0;` lines, gone since upstream's layers default to active     |
| rebased -> ported   | 47   | 2         | outlines of ProzaLibre-Roman-MM.vfb and ProzaLibre-Italic-MM.vfb             |

The two Proza Libre files are multiple-master. With 0.1.6 glyph `n` of the Roman spans x 176..2328 for an advance of 1258; with 0.1.7 (node coordinate deltas kept per master) it spans 176..1082.

## What vfbreader 0.1.7 replaces in our branch

0.1.7 decodes three entries our branch decoded from raw bytes: PostScript Info (x-height, cap height), OpenType Kerning Class Flags, Glyph GDEF Data (anchors). The port drops those three parsers and their tests (29 lines added, 308 removed); what the converter does with the values is unchanged, as the 47 identical outputs show. `cargo test -p babelfont --features cli`: 357 pass, 11 fail on upstream main's missing RoboCJK fixture (`designspace.json`), none in the FontLab code.
