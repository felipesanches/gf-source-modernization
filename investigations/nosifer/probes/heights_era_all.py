#!/usr/bin/env python3
"""Question answered: across EVERY style in families.tsv, does choosing the
FontForge height rule by the era of the FontForge that exported the release
(read from the release's FFTM table) reproduce more releases than the master
rule alone -- and does it break any the master rule already reproduces?

FontForge's SFStandardHeight divided the sum of the distinct round/pointy tops
by the NUMBER OF GLYPHS from 37d20840 (2009-05-27) until Khaled Hosny's fix
4d34d21e (2012-05-14), which divides by the number of distinct tops. Only a
font with NO flat top in the letter list is affected.

Columns: FFTM FontForge build date (FFTimeStamp) | release x/cap | master-rule
x/cap | 2009-2012-rule x/cap | which rule(s) match | era-chosen verdict.
The era choice: buggy rule iff 2009-05-27 <= FFTimeStamp < 2012-05-14.

Usage: /home/fsanches/compartilhado/gftools/venv/bin/python3 heights_era_all.py
"""
import datetime
import subprocess
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/investigations/nosifer/probes")
import ff_heights_oracle as O  # noqa: E402
from heights_2011_rule import measure, snap, rule  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from fontTools.misc.timeTools import epoch_diff  # noqa: E402

TSV = "/home/fsanches/compartilhado/gf-source-modernization/families.tsv"
LO = datetime.datetime(2009, 5, 27)
HI = datetime.datetime(2012, 5, 14)


def val(sfd, flats, curves, year, stated):
    if stated:
        return int(stated)
    raw = rule(flats, curves, year)
    return O.exported(None if raw is None else snap(sfd, raw))


def main():
    rows = [l.rstrip("\n").split("\t") for l in open(TSV)][1:]
    n = {"master": 0, "era": 0, "total": 0}
    print("%-28s %-10s %-10s %-10s %-10s %-12s %s" % ("style", "FF build", "release", "master", "2009-12", "matches", "era-choice"))
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        path = f"{lic}/{fam}/{src}" if kind == "hg" else src
        text = subprocess.run(["git", "-C", f"{O.ARC}/{base}.git", "show", f"{commit}:{path}"],
                              capture_output=True, check=True).stdout.decode("utf-8", "replace")
        sfd = O.Sfd(text)
        hdr = {k: v for k, v in (l.split(":", 1) for l in text.split("\nStartChar:", 1)[0].split("\n") if ":" in l)}
        sx = float(hdr.get("OS2XHeight", 0) or 0)
        sc = float(hdr.get("OS2CapHeight", 0) or 0)
        f = TTFont(shipped)
        o2 = f["OS/2"]
        if o2.version < 2:
            continue
        stamp = None
        if "FFTM" in f:
            stamp = datetime.datetime.utcfromtimestamp(f["FFTM"].FFTimeStamp + epoch_diff)
        xf, xc, _ = measure(sfd, O.XH)
        cf, cc, _ = measure(sfd, O.CAP)
        m = (val(sfd, xf, xc, 2012, sx), val(sfd, cf, cc, 2012, sc))
        b = (val(sfd, xf, xc, 2011, sx), val(sfd, cf, cc, 2011, sc))
        rel = (o2.sxHeight, o2.sCapHeight)
        era_buggy = stamp is not None and LO <= stamp < HI
        chosen = b if era_buggy else m
        which = "+".join(k for k, v in (("master", m), ("2009-12", b)) if v == rel) or "neither"
        n["total"] += 1
        n["master"] += m == rel
        n["era"] += chosen == rel
        print("%-28s %-10s %-10s %-10s %-10s %-12s %s" % (
            style, stamp.date() if stamp else "no-FFTM", "%d/%d" % rel, "%d/%d" % m, "%d/%d" % b,
            which, ("MATCH" if chosen == rel else "differ") + (" (2009-12 rule)" if era_buggy else "")))
    print()
    print("master rule alone reproduces %d of %d; era-chosen rule reproduces %d of %d"
          % (n["master"], n["total"], n["era"], n["total"]))


if __name__ == "__main__":
    main()
