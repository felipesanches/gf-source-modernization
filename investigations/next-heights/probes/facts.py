#!/usr/bin/env python3
"""Question answered: for each style of the "heights" unit, what do the three
candidate origins of the released OS/2 sxHeight/sCapHeight say?

  - the RELEASE (google/fonts, the pipeline's own pairing in families-next.tsv):
    OS/2 version, sxHeight, sCapHeight, usWeightClass, and its FFTM table (the
    FontForge build stamp FFTimeStamp, and sourceCreated/sourceModified);
  - the paired -TTF.sfd (base tree googlefontdirectory-hg 52f780bc): header facts
    that FontForge's exporter reads (Order2/Layer quadratic flag, Ascent/Descent,
    BlueValues, stated OS2 heights, OS2Version, TTFWeight, Creation/ModificationTime);
  - the cubic src/<X>.otf in the SAME base tree (the designer's deliverable): its OS/2
    version, sxHeight, sCapHeight, head.created/modified, its own FFTM if any, and
    the CFF Private BlueValues.

Nothing here decides anything; it lays the facts side by side so that each
hypothesis (another FontForge vintage, a stated value, a cubic source) can be
checked against them.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 facts.py > ../runs/facts.txt
"""
import datetime
import io
import subprocess
import sys

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/sfd-reland/families-next.tsv"
UNIT = """KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular""".split()
# also the unit's sibling styles that are already CLEAN, as controls
CONTROLS = "Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular".split()
E1904 = 2082844800


def ts(v):
    return datetime.datetime.fromtimestamp(v, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def rows():
    out = {}
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            out[r["style"]] = r
    return out


def show(commit, path):
    p = subprocess.run(["git", "-C", ARC, "show", f"{commit}:{path}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def fftm(f):
    if "FFTM" not in f:
        return "no FFTM"
    t = f["FFTM"]
    return (f"FFTM build {ts(t.FFTimeStamp - E1904)} ({t.FFTimeStamp - E1904}) "
            f"srcCreated {ts(t.sourceCreated - E1904)} srcModified {ts(t.sourceModified - E1904)}")


def os2(f):
    o = f["OS/2"]
    x = getattr(o, "sxHeight", None)
    c = getattr(o, "sCapHeight", None)
    return f"OS/2 v{o.version} x={x} cap={c} wc={o.usWeightClass}"


def header(text):
    hdr = text.split("\nStartChar:", 1)[0]
    keep = []
    for l in hdr.split("\n"):
        k = l.split(":", 1)[0]
        if k in ("Ascent", "Descent", "Order2", "Layer", "OS2XHeight", "OS2CapHeight",
                 "OS2Version", "TTFWeight", "CreationTime", "ModificationTime", "Version",
                 "OS2_WeightWidthSlopeOnly", "FontName", "GaspTable"):
            keep.append(l.strip())
        elif l.startswith("BlueValues") or l.startswith("OtherBlues") or l.startswith("StdVW"):
            keep.append(l.strip())
    for l in hdr.split("\n"):
        k = l.split(":", 1)[0]
        if k in ("CreationTime", "ModificationTime"):
            try:
                keep.append(f"  {k} = {ts(int(l.split(':', 1)[1]))}")
            except ValueError:
                pass
    return keep


def main():
    rs = rows()
    styles = sys.argv[1:] or UNIT + CONTROLS
    for s in styles:
        r = rs[s]
        print("=" * 78)
        print(f"{s}  pair: {r['lic']}/{r['family']}/{r['source']} <-> {r['shipped']}")
        rel = TTFont(r["shipped"])
        print(f"  RELEASE  {os2(rel)}  unitsPerEm={rel['head'].unitsPerEm}")
        print(f"           {fftm(rel)}")
        print(f"           head.created {ts(rel['head'].created - E1904)} modified {ts(rel['head'].modified - E1904)}")
        text = show(r["commit"], f"{r['lic']}/{r['family']}/{r['source']}").decode("utf-8", "replace")
        print("  SFD      " + "\n           ".join(header(text)))
        otfp = r["source"].replace("-TTF.sfd", ".otf")
        data = show(r["commit"], f"{r['lic']}/{r['family']}/{otfp}")
        if data is None:
            print(f"  OTF      {otfp}: absent")
            continue
        o = TTFont(io.BytesIO(data))
        print(f"  OTF      {otfp}: {os2(o)} upm={o['head'].unitsPerEm}")
        print(f"           {fftm(o)}")
        print(f"           head.created {ts(o['head'].created - E1904)} modified {ts(o['head'].modified - E1904)}")
        if "CFF " in o:
            pd = o["CFF "].cff.topDictIndex[0].Private
            print(f"           CFF BlueValues {getattr(pd, 'BlueValues', None)} OtherBlues {getattr(pd, 'OtherBlues', None)}")
        n = o["name"]
        for nid in (5, 3):
            rec = n.getName(nid, 3, 1, 0x409)
            if rec:
                print(f"           name{nid}: {rec.toUnicode()}")


if __name__ == "__main__":
    main()
