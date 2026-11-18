# The 17 googlefontdirectory-hg families with a librefonts fork: convert from the binaries?

Krona One, Oldenburg, Ovo, Passero One, Poller One, Pompiere, Rye, Sarina, Short Stack, Snowburst One,
Sonsie One, Spinnaker, Stoke (Light, Regular), Supermercado One, Tauri, Vast Shadow and Wellfleet: 18 styles.
google/fonts METADATA.pb points each at googlefonts/googlefontdirectory-hg 52f780bc. googlefonts/<family>
exists and is a fork of librefonts/<family>: same master, no pull requests (checked 2026-11-18). Its src/
holds a FontLab .vfb and FontForge -TTF.sfd (some also -OTF.sfd) files.

| file                            | question it answers                                                                  | command                                                                                                    |
|---------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| families-hg-forks.tsv           | (input) the TTF .sfd of each style at the fork's master                              | -                                                                                                          |
| results-hg-forks-2026-11-18.tsv | is each TTF .sfd an import of the binary (P13)?                                      | `python3 -I tools/probes/ttf_sfd_origin/origin.py tools/probes/hg_forks_from_binary/families-hg-forks.tsv` |
| run_probe.sh                    | do the shipped binaries convert and rebuild to the release, under the landing gates? | `sh tools/probes/hg_forks_from_binary/run_probe.sh <scratch dir>`                                          |
| results-2026-11-18.txt          | run_probe.sh's output: google/fonts 7af0d90b4, babelfont 26fdcfa9, builder 1e638bd   | -                                                                                                          |

## Results, 2026-11-18

All 18 TTF .sfd files are IMPORTs: quadratic, with TrueType instructions or a .vfb twin. So under P13 the
sources come from the binaries. Converting the binaries (tools/probes/binary_to_source/probe.py) gives:

| outcome                                                 | styles                                                                       |
|---------------------------------------------------------|------------------------------------------------------------------------------|
| CLEAN                                                   | KronaOne-Regular, Ovo-Regular, ShortStack-Regular, SonsieOne-Regular         |
| GDEF: the release classes dotaccentcmb (U+0307) as base | Pompiere-Regular (113 shaping runs differ), PollerOne (2 runs; also hinting) |
| hinting only: the release's 7-byte prep ends in SVTCA   | Oldenburg, PasseroOne, Sarina, Stoke-Light, VastShadow, Wellfleet-Regular    |
| hinting only: glyph programs, fpgm, cvt                 | Rye, SnowburstOne, Spinnaker, Stoke-Regular, SupermercadoOne, Tauri-Regular  |

Every other check passes on every style: 0 table-gate rows, the exact codepoints, names, line spacing and
advances. The 7-byte prep pushes 4 for SCANTYPE but ends in SVTCA[0], so the scan type is never set. The
builder writes the smart-dropout prep with SCANTYPE, and the hinting check counts the two programs as different.

The hinting rows wait on gftools-rust#2 (apply a font's own TrueType hinting), as Bonbon, Federo and Lancelot do.
Plan key gdef_classes_fea (plans/pollerone.json, plans/pompiere.json) states the GDEF classes.

## Pompiere and Poller One after the GDEF statement (land.py, 2026-11-18)

With gdef_classes_fea the GDEF classes match, but some base+mark runs still shape differently. Neither font has
GSUB or GPOS, so HarfBuzz places combining marks itself from the glyph bounding boxes, and the release's glyf
bounding boxes are stale where a compiled font's are exact. fallback_mark_delta.py measures this on every
cmap base followed by every U+0300-036F mark, against a build of the landed sources:

| style            | stale glyf bboxes in the release | base+mark pairs | differ | largest offset difference (of 2048) |
|------------------|----------------------------------|-----------------|--------|-------------------------------------|
| Pompiere-Regular | 174                              | 26656           | 25596  | 35                                  |
| PollerOne        | 3                                | 25648           | 59     | 1                                   |

Command: `python3 -I tools/probes/hg_forks_from_binary/fallback_mark_delta.py <release.ttf> <build.ttf>`
(uharfbuzz from the gftools venv). No source can restate a stale bounding box, so plans/pompiere.json and
plans/pollerone.json disclose it. Pompiere's shaping row is accepted, which makes it CLEAN-DISCLOSED. Poller One
also waits on hinting.
