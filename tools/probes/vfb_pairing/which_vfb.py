#!/usr/bin/env python3
"""Question answered: of the .vfb files a family's upstream holds at the recorded commit,
which one agrees with the shipped font -- by advance widths and glyph set, read from a
conversion of each candidate, not from its name?

tools/pair_vfb.py pairs by PostScript name and prefers the -TTF variant; this probe checks
that choice where a family has several candidates (Alfa Slab One: the -TTF variant differs
from the release on 157 of 235 advances). For each shipped style of the families given, every
.vfb in the family's directory is converted with babelfont (BF=), its glyph widths are read
from the .glyphs, and the row reports, per candidate: glyphs it has that the release has,
advances equal, advances differing. The best candidate is the one with the most equal
advances; the probe never edits families-vfb.tsv -- the pairing is still decided there.

Usage: BF=<babelfont> python3 which_vfb.py <scratch dir> <family slug>...
Prints one line per (style, candidate); `*` marks the family table's current pick.
"""
import csv
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
HG = "googlefonts/googlefontdirectory-hg"
BF = os.environ["BF"]


def git(mirror, *a):
    return subprocess.run(["git", "-C", mirror, *a], capture_output=True, check=True).stdout


def glyph_widths(glyphs_path):
    """{glyph name: width of its first layer} from a Glyphs 3 file as babelfont writes it."""
    text = open(glyphs_path, encoding="utf-8").read()
    out = {}
    names = list(re.finditer(r"^glyphname = (\S+?);$", text, re.M))
    for i, m in enumerate(names):
        end = names[i + 1].start() if i + 1 < len(names) else len(text)
        w = re.search(r"^width = ([-\d.]+);", text[m.end():end], re.M)
        if w:
            out[m.group(1).strip('"')] = round(float(w.group(1)))
    return out


def main():
    scratch, fams = sys.argv[1], sys.argv[2:]
    os.makedirs(scratch, exist_ok=True)
    rows = [r for r in csv.DictReader(open(os.path.join(W, "families-vfb.tsv")), delimiter="\t")
            if r["repo"] in fams]
    for fam in fams:
        frows = [r for r in rows if r["repo"] == fam]
        if not frows:
            print("%s: not in families-vfb.tsv" % fam)
            continue
        r0 = frows[0]
        mirror = os.path.join(ARC, r0["base"] + ".git")
        prefix = "%s/%s/" % (r0["lic"], r0["family"]) if r0["base"] == HG else ""
        if r0["base"] == HG and not git(mirror, "ls-tree", "--name-only", r0["commit"], prefix.rstrip("/")).strip():
            prefix = r0["family"] + "/"
        paths = [p for p in git(mirror, "ls-tree", "-r", "--name-only", r0["commit"]).decode().splitlines()
                 if p.startswith(prefix) and p.lower().endswith(".vfb")]
        widths = {}
        for p in paths:
            local = os.path.join(scratch, fam + "__" + p[len(prefix):].replace("/", "__"))
            with open(local, "wb") as fh:
                fh.write(git(mirror, "show", "%s:%s" % (r0["commit"], p)))
            g = local + ".glyphs"
            res = subprocess.run([BF, local, g], capture_output=True, text=True)
            widths[p] = glyph_widths(g) if res.returncode == 0 else None
        for r in frows:
            f = TTFont(r["shipped"])
            rel = {n: f["hmtx"][n][0] for n in f.getGlyphOrder()}
            for p in paths:
                mark = "*" if p[len(prefix):] == r["source"] else " "
                if widths[p] is None:
                    print("%s %s/%s %s: conversion failed" % (mark, fam, r["style"], p[len(prefix):]))
                    continue
                common = [n for n in widths[p] if n in rel]
                eq = sum(widths[p][n] == rel[n] for n in common)
                print("%s %s/%s %-40s glyphs %d (%d in release) advances equal %d differ %d"
                      % (mark, fam, r["style"], p[len(prefix):], len(widths[p]), len(common), eq, len(common) - eq))


if __name__ == "__main__":
    main()
