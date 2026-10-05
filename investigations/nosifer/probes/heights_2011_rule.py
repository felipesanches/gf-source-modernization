#!/usr/bin/env python3
"""Question answered: do the released OS/2 sxHeight/sCapHeight of Nosifer and
Nosifer Caps (925/854) come from FontForge 20110222's exporter rule applied to
the unmodified -TTF.sfd named in families.tsv?

FontForge 20110222 (tag v20110222, commit 9ec8bff8; the build the releases'
FFTM table names: FFTimeStamp 2011-02-22 13:48:33) differs from the 2012/master
SFStandardHeight in ONE line of the no-flat-tops branch (splinefont.c:1709):

    2011:  test += curves[i].pos;  tot += curves[i].cnt;   /* sum of DISTINCT tops / number of GLYPHS */
    2012+: test += curves[i].pos;  ++tot;                   /* mean of the distinct tops              */

This probe reuses tools/ff_heights_oracle.py (the master-rule port) for parsing
and per-glyph top measurement and prints, per style, the per-glyph tops, the
master-rule result and the 2011-rule result, next to the release.

Usage: /home/fsanches/compartilhado/gftools/venv/bin/python3 heights_2011_rule.py
"""
import subprocess
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
import ff_heights_oracle as O  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

TSV = "/home/fsanches/compartilhado/gf-source-modernization/families.tsv"
STYLES = ("Nosifer-Regular", "NosiferCaps-Regular")


def measure(sfd, lst):
    flats, curves, per = [], [], []
    for ch in O.expand(lst):
        gid = sfd.by_uni.get(ch)
        if gid is None:
            continue
        t, f = O.sc_max(sfd, gid)
        per.append((chr(ch), t, f))
        bucket = flats if f == O.FLAT else (curves if f != O.UNKNOWN else None)
        if bucket is None:
            continue
        for e in bucket:
            if e[0] == t:
                e[1] += 1
                break
        else:
            bucket.append([t, 1])
    return flats, curves, per


def snap(sfd, result):
    if not sfd.blues:
        return result
    vals = []
    for tok in sfd.blues.replace("[", " ").replace("]", " ").split():
        try:
            vals.append(float(tok))
        except ValueError:
            break
    best, bestdiff = result, (sfd.ascent + sfd.descent) / 100.0
    for v in vals[0::2]:
        if abs(v - result) < bestdiff:
            best, bestdiff = v, abs(v - result)
    return best


def rule(flats, curves, year):
    if len(flats) == 1:
        return flats[0][0]
    if flats:
        top = max(c for _, c in flats)
        tied = [p for p, c in flats if c == top]
        return sum(tied) / len(tied)
    if not curves:
        return None
    num = sum(p for p, _ in curves)
    den = sum(c for _, c in curves) if year == 2011 else len(curves)
    return num / den


def main():
    rows = [l.rstrip("\n").split("\t") for l in open(TSV)][1:]
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        if style not in STYLES:
            continue
        path = f"{lic}/{fam}/{src}" if kind == "hg" else src
        text = subprocess.run(["git", "-C", f"{O.ARC}/{base}.git", "show", f"{commit}:{path}"],
                              capture_output=True, check=True).stdout.decode("utf-8", "replace")
        sfd = O.Sfd(text)
        o2 = TTFont(shipped)["OS/2"]
        print("== %s  source %s@%s:%s" % (style, base, commit[:12], path))
        print("   release %s: sxHeight %d  sCapHeight %d" % (shipped.split("/")[-1], o2.sxHeight, o2.sCapHeight))
        for name, lst, rel in (("x-height", O.XH, o2.sxHeight), ("cap-height", O.CAP, o2.sCapHeight)):
            flats, curves, per = measure(sfd, lst)
            print("   %s: %d glyphs measured; flat tops %s; round/pointy distinct tops %d, glyphs %d"
                  % (name, len(per), flats, len(curves), sum(c for _, c in curves)))
            print("     per glyph: " + " ".join("%s=%g%s" % (c if c.isascii() else "U+%04X" % ord(c), t, f[0]) for c, t, f in per))
            for year in (2012, 2011):
                raw = rule(flats, curves, year)
                val = O.exported(None if raw is None else snap(sfd, raw))
                print("     rule %s: raw %s -> exported %d  %s" % (
                    "2011 (v20110222)" if year == 2011 else "2012+ (master)",
                    "none" if raw is None else "%.4f" % raw, val,
                    "MATCHES release" if val == rel else "differs from release %d" % rel))


if __name__ == "__main__":
    main()
