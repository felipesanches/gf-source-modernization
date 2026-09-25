#!/usr/bin/env python3
"""Question answered: which PostScript BlueValues did FontForge hold in memory when it
exported a style's release, for the styles whose release was exported from the font
FontForge loaded from src/<X>.otf?

googlefontdirectory-hg's tools/generate/HOWTOGEN.txt (base tree 52f780bc) records the
2012 production: FontLab generated <X>-OTF.otf; tools/nonhinting/
setquadraticaddextremasimplify-fontforge.py opened that .otf in FontForge, made the
layer quadratic, added extrema, simplified, corrected directions and generated the
TTF; setnonhinting-fonttools.py added prep+gasp; the files were renamed (<X>.otf,
<X>.ttf); tools/nonhinting/ttf2sfd.py then opened the TTF and saved <X>-TTF.sfd.
A TTF carries no PostScript private dictionary, so the -TTF.sfd has none, while the
exporter had the one FontForge read from the .otf's CFF (parsettf.c
cffprivatefillup -> realarray2str: "%g " per value, trailing zeros dropped, one
zero put back when an odd count ends negative) and snapped its x-height and cap
height to those zones (splinefont.c SFStandardHeight).

This prints, per style, the `addprivate` arguments that restore that entry, exactly
as FontForge's CFF reader wrote it into sf->private, read from the .otf in the SAME
base tree as the paired -TTF.sfd (families-next.tsv). The value comes from the .otf;
nothing is read from the release.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 otf_bluevalues.py [Style...]
"""
import io
import subprocess
import sys

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/sfd-reland/families-next.tsv"


def realarray2str(values, must_be_even=True):
    """fontforge/parsettf.c realarray2str at b69c9652 and 5a11aa4c."""
    arr = list(values)
    i = len(arr) - 1
    while i >= 0 and arr[i] == 0:
        i -= 1
    if i == -1:
        return None
    if must_be_even and not (i & 1) and arr[i] < 0:
        i += 1
        if i >= len(arr):
            arr.append(0)
    return "[" + " ".join("%g" % float(v) for v in arr[:i + 1]) + "]"


def row(style):
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            if r["style"] == style:
                return r
    raise SystemExit("no row for %s" % style)


def blue_values(style):
    r = row(style)
    otf = r["source"].replace("-TTF.sfd", ".otf")
    data = subprocess.run(["git", "-C", ARC, "show", "%s:%s/%s/%s" % (r["commit"], r["lic"], r["family"], otf)],
                          capture_output=True, check=True).stdout
    pr = TTFont(io.BytesIO(data))["CFF "].cff.topDictIndex[0].Private
    return "%s/%s/%s" % (r["lic"], r["family"], otf), realarray2str(pr.BlueValues)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        src, bv = blue_values(s)
        print("%s\t%s\tBlueValues %s" % (s, src, bv))
