# crater_triage -- source pins flagged in fontc_crater triage

**Model**: Claude Opus 5.5. **Date**: 2026-10-15.

Colin Rofls (fontc_crater triage, relayed 2026-10-14) flagged three pins: Intel One Mono's fix is
in the googlefonts fork Google Fonts shipped from; Cabin Condensed pins the 2017 sources while
Cabin pins the 2020 v3 ones; Coiny has a clean Glyphs 3.5 source upstream. Each was checked
against the binaries google/fonts ships (google/fonts b7c8331cf), because METADATA.pb records the
source of the shipped build. Result: google/fonts branch source-metadata-crater-triage-2026-10,
body pr-bodies/google-fonts-crater-triage-2026-10.md.

| script               | question it answers                                                                         | run                                                                               |
|----------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `shipped_in_repo.sh` | at which commits of an upstream repo are the shipped .ttf files byte-identical (blob hash)? | `sh shipped_in_repo.sh <google/fonts> ofl/<family> <bare mirror> [rev-list args]` |
| `compare_ttf.py`     | is a TTF built from a new source the same design as the shipped one?                        | `python3 compare_ttf.py <shipped.ttf> <other.ttf>`                                |

| family          | finding                                                                                             | change          |
|-----------------|-----------------------------------------------------------------------------------------------------|-----------------|
| Intel One Mono  | 12 of 12 shipped files at googlefonts/intel-one-mono 06572f3e; 0 at any intel/intel-one-mono commit | pin to the fork |
| Cabin Condensed | 4 of 4 shipped files at impallari/Cabin f0f6a1a, merged by the pinned 9476ee6                       | none (report)   |
| Coiny           | shipped file at no commit; the 2026 Glyphs TTF: 80 advances, 159 bounds differ, 16 codepoints fewer | none (report)   |

Commands that gave those rows (repo-archive mirrors, google/fonts at b7c8331cf):

    sh shipped_in_repo.sh <gf> ofl/intelonemono <archive>/googlefonts/intel-one-mono.git c6473891..0e8ab538^2
    sh shipped_in_repo.sh <gf> ofl/intelonemono <archive>/intel/intel-one-mono.git
    sh shipped_in_repo.sh <gf> ofl/cabincondensed <archive>/impallari/Cabin.git
    python3 compare_ttf.py <gf ofl/coiny/Coiny-Regular.ttf> <marcelommp/Coiny 7a15915:TTF/Coiny-Regular.ttf>

`crater-intel-one-mono.txt`: fontc_crater on the new Intel One Mono entry
(`subset-intel-one-mono.json`), googlefonts/fontc main da343d39 with its requirements.txt (gftools
0.10.3), run as in logs/crater-targets-2026-10-15/README.md. Default mode: both designspaces build,
fontc output identical to fontmake's. gftools mode: fontc rejects `--fea-include-dir`, which gftools
passes on from the config's `extraFontmakeArgs`. The entry it replaces (intel/intel-one-mono 99e2d6c)
failed the Italic in both modes in crater's 2026-10-05 run ("interpolation-incompatible paths").
