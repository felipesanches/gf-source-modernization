#!/usr/bin/env python3
"""Question answered: for every style in families.tsv, which underline rule turns
the .sfd's own UnderlinePosition/UnderlineWidth into the post.underlinePosition
the release ships -- and which toolchain exported that release?

Rules (FontForge's UnderlinePosition is the underline's CENTRE; post's is its TOP):
  raw      UnderlinePosition, unchanged (babelfont without a filter)
  pre2019  trunc(pos - width/2)   FontForge tottf.c dumppost() through 20170731
                                  == babelfont --fontforge-underline-position
  post2019 otRound(pos + width/2) sfdLib 2.0.0.post0 sfd2ufo + ufo2ft (floor(x+.5));
                                  FontForge >= 20190317 truncates instead, which
                                  gives the same value whenever pos + width/2 <= 0
Toolchain: the FFTM table's FontForge build timestamp, or "no FFTM".

Only the source named in families.tsv for each style is read (no name matching).
Usage: gftools/venv/bin/python3 probes/underline_rules.py
"""
import csv
import datetime
import math
import subprocess

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/sfd-reland"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"


def field(text, name):
    for line in text.split("\nStartChar:", 1)[0].splitlines():
        if line.startswith(name + ": "):
            return float(line.split(": ", 1)[1])
    return None


def main():
    rows = list(csv.DictReader(open(W + "/families.tsv", encoding="utf-8"), delimiter="\t"))
    print("%-26s %-6s %-6s %-9s %-9s %-9s %-8s %s" % (
        "style", "pos", "width", "raw", "pre2019", "post2019", "release", "matches / toolchain"))
    for r in rows:
        path = r["source"] if r["kind"] != "hg" else "%s/%s/%s" % (r["lic"], r["family"], r["source"])
        try:
            text = subprocess.check_output(
                ["git", "-C", "%s/%s.git" % (ARC, r["base"]), "show", "%s:%s" % (r["commit"], path)]
            ).decode("utf-8", "replace")
        except subprocess.CalledProcessError:
            print("%-26s NO-SOURCE" % r["style"])
            continue
        pos, width = field(text, "UnderlinePosition"), field(text, "UnderlineWidth")
        f = TTFont(r["shipped"])
        rel = f["post"].underlinePosition
        if pos is None or width is None:
            print("%-26s source states no UnderlinePosition/UnderlineWidth; release %d" % (r["style"], rel))
            continue
        cand = {"raw": int(pos), "pre2019": int(pos - width / 2),
                "post2019": math.floor(pos + width / 2 + 0.5)}
        match = [k for k, v in cand.items() if v == rel] or ["NONE"]
        if "FFTM" in f:
            ts = f["FFTM"].FFTimeStamp  # FontForge build stamp, seconds since 1904
            tool = "FFTM FontForge %s" % (datetime.datetime(1904, 1, 1) + datetime.timedelta(seconds=ts)).date()
        else:
            tool = "no FFTM"
        print("%-26s %-6g %-6g %-9d %-9d %-9d %-8d %s / %s" % (
            r["style"], pos, width, cand["raw"], cand["pre2019"], cand["post2019"], rel,
            ",".join(match), tool))


if __name__ == "__main__":
    main()
