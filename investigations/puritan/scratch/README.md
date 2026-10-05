# puritan -- the investigator's two small measurement scripts

Recovered from session scratch; the numbers they printed are quoted in `../FINDINGS.md`
and in the commit that landed puritan.

| script | question it answers |
|---|---|
| `widths.py` | Scaling each `.sfd` advance by 1024/1000, which rounding reproduces the released advance widths? Prints, per style, how many match under rint / truncation / floor / ceil -- the source of "truncation 237/237, rint only 107/97/113/113". |
| `dumpmetrics.py` | The header, hhea, OS/2 and post values of any number of fonts side by side (TSV), for comparing the release with the unscaled `.otf` and with our builds. |

Both read files relative to the current directory. To rerun:

    PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
    W=$(mktemp -d) && cd $W && mkdir mono rel
    git -C /home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git \
        archive 52f780bc9d197280a9f430574e179a5f233c56b6 ofl/puritan | tar -x -C mono --strip-components=2
    cp /home/fsanches/compartilhado/google/fonts/ofl/puritan/*.ttf rel/
    $PY /home/fsanches/compartilhado/gf-source-modernization/investigations/puritan/scratch/widths.py
    $PY /home/fsanches/compartilhado/gf-source-modernization/investigations/puritan/scratch/dumpmetrics.py rel/*.ttf mono/src/*.otf

The FontForge 20100501 source the investigation read (and whose libtool `ltmain.sh`
stayed in scratch) is disposable: it is
`downloads.sourceforge.net/project/fontforge/fontforge-source/fontforge_full-20100501.tar.bz2`,
sha256 `ee4928b0df7480c31a422645854d9f3f4f6718dd423b6885bd33e87a8a6edd79`.
