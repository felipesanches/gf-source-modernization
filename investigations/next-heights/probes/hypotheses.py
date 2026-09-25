#!/usr/bin/env python3
"""Question answered: for each style of the "heights" unit, which combination of
(FontForge vintage, outlines measured, BlueValues present) reproduces the released
OS/2 sxHeight and sCapHeight EXACTLY?

Dimensions tried, each a concrete thing the 2012 production could have done:
  vintage   2011 = FontForge b69c9652 (FFTM stamp 2011-02-22): curve mean divides the
                   sum of distinct round tops by the number of GLYPHS;
            2012 = FontForge 5a11aa4c (FFTM stamp 2012-09-06) / master: by the number
                   of DISTINCT heights (4d34d21ef866).
  outlines  sfd  = the paired quadratic src/<X>-TTF.sfd (what the converter reads);
            otf  = the cubic src/<X>.otf in the same base tree (the designer's
                   deliverable; FontForge would measure its cubic splines in memory).
  blues     none = no PS Private dict (the -TTF.sfd has none);
            otf  = the CFF Private BlueValues of src/<X>.otf, which FontForge keeps as
                   sf->private when it opens a CFF .otf; SFStandardHeight snaps to the
                   nearest zone bottom closer than (ascent+descent)/100 = 10 units.

The rule itself is the committed, independently verified implementation in
../../heights/ff_heights_probe.py (SFD) and ../../heights/cff_heights_probe.py (CFF).
Pairing: families-next.tsv (style -> source, shipped), base tree
googlefontdirectory-hg 52f780bc.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 hypotheses.py > ../runs/hypotheses.txt
  ... hypotheses.py dump <Style>      per-glyph tops for every combination
"""
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "heights"))
import ff_heights_probe as P  # noqa: E402
import cff_heights_probe as C  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/sfd-reland/families-next.tsv"
SCR = "/home/fsanches/compartilhado/sfd-reland-scratch/heights/otf"
E1904 = 2082844800
FIX = 1337023489      # FFTM stamp of 4d34d21ef866 (tools/recipe.py)
UNIT = """KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular""".split()
CONTROLS = "Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular".split()


def rows():
    out = {}
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            out[r["style"]] = r
    return out


def show(r, rel):
    p = subprocess.run(["git", "-C", ARC, "show", f"{r['commit']}:{r['lic']}/{r['family']}/{rel}"],
                       capture_output=True, check=True)
    return p.stdout


def fonts(r):
    sfd = P.parse(show(r, r["source"]).decode("utf-8", "replace"))
    otf_rel = r["source"].replace("-TTF.sfd", ".otf")
    os.makedirs(SCR, exist_ok=True)
    path = os.path.join(SCR, os.path.basename(otf_rel))
    with open(path, "wb") as fh:
        fh.write(show(r, otf_rel))
    otf = C.load(path)
    return sfd, otf


def measure(font, year, blues, lst, trace=None):
    f = dict(font)
    f["blues"] = blues
    res = P.standard_height(P.V(year), f, lst, trace)[0]
    return P.exported(res), res


def main():
    rs = rows()
    if len(sys.argv) > 2 and sys.argv[1] == "dump":
        return dump(rs[sys.argv[2]])
    print("combination = vintage/outlines/blues; value = exported (raw before snapping)")
    for s in UNIT + CONTROLS:
        r = rs[s]
        rel = TTFont(r["shipped"])
        o = rel["OS/2"]
        stamp = rel["FFTM"].FFTimeStamp - E1904 if "FFTM" in rel else None
        vint = 2011 if stamp is not None and stamp < FIX else 2012
        sfd, otf = fonts(r)
        print("=" * 78)
        print(f"{s}  release x={o.sxHeight} cap={o.sCapHeight}  FFTM-selected vintage {vint}"
              f"  otf blues {otf['blues']}")
        for label, lst, want in (("x", P.XH, o.sxHeight), ("cap", P.CAP, o.sCapHeight)):
            hits = []
            for year in (2011, 2012):
                for oname, font in (("sfd", sfd), ("otf", otf)):
                    for bname, blues in (("none", None), ("otf", otf["blues"])):
                        v, res = measure(font, year, blues, lst)
                        raw = None if res is None else round(res[0], 3)
                        tag = f"{year}/{oname}/{bname}"
                        mark = "MATCH" if v == want else ""
                        if v == want:
                            hits.append(tag)
                        star = " <- converter today" if (year == vint and oname == "sfd" and bname == "none") else ""
                        print(f"  {label:3s} {tag:15s} {v:5d} (raw {raw}) {mark}{star}")
            print(f"  {label:3s} matches: {', '.join(hits) or 'NONE'}")


def dump(r):
    sfd, otf = fonts(r)
    for oname, font in (("sfd", sfd), ("otf", otf)):
        for year in (2011, 2012):
            for label, lst in (("x", P.XH), ("cap", P.CAP)):
                tr = []
                v, res = measure(font, year, otf["blues"], lst, tr)
                print(f"== {oname} {year} {label}: exported {v} raw {res}")
                for ch, gname, t, f in tr:
                    print("  U+%04X %-14s %-8s %.6f" % (ch, gname, f, t))


if __name__ == "__main__":
    main()
