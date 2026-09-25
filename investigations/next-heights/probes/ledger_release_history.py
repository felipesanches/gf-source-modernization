#!/usr/bin/env python3
"""Question answered: what did google/fonts' two 2020 commits to
ofl/ledger/Ledger-Regular.ttf change, and was the 2012 binary the release in the
base tree googlefontdirectory-hg 52f780bc?

  90abd17b4  2015-03-07  Initial commit (the 2012 binary)
  0436d99c0  2020-06-23  "ledger: fixed nbsp width (#2353)"   (Measure + Fit)
  f8265bddf  2020-06-23  "ledger: v1.003 added (#2514)"         (Marc Foley)

For each consecutive pair it prints every table whose bytes differ and, for the
fields this unit's gate rows are about, the values: hmtx of uni00A0 and space,
OS/2 sxHeight/sCapHeight, head.fontRevision, name ID 5.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 ledger_release_history.py
"""
import io
import subprocess

from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts"
HG = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
PATH = "ofl/ledger/Ledger-Regular.ttf"
REVS = [("hg 52f780bc", HG, "52f780bc9d197280a9f430574e179a5f233c56b6"),
        ("gf 90abd17b4", GF, "90abd17b4"), ("gf 0436d99c0", GF, "0436d99c0"),
        ("gf f8265bddf", GF, "f8265bddf"), ("gf b5efa9c32e8f", GF, "b5efa9c32e8f")]


def load(repo, rev):
    data = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (rev, PATH)],
                          capture_output=True, check=True).stdout
    return data, TTFont(io.BytesIO(data))


def summary(f):
    o = f["OS/2"]
    hm = f["hmtx"].metrics
    cmap = f.getBestCmap()
    return ("nbsp(U+00A0 -> %s) adv=%s space adv=%s | OS/2 x=%d cap=%d | head.fontRevision=%.3f | name5=%r"
            % (cmap.get(0xA0), hm.get(cmap.get(0xA0), ("-",))[0], hm[cmap[0x20]][0], o.sxHeight,
               o.sCapHeight, f["head"].fontRevision, f["name"].getDebugName(5)))


def main():
    prev = None
    for label, repo, rev in REVS:
        data, f = load(repo, rev)
        print("%-17s %d bytes  %s" % (label, len(data), summary(f)))
        if prev is not None:
            pdata, pf = prev
            if pdata == data:
                print("  byte-identical to the previous revision")
            else:
                tags = sorted(set(pf.keys()) | set(f.keys()))
                diff = [t for t in tags if t != "GlyphOrder" and
                        (t not in pf or t not in f or pf.getTableData(t) != f.getTableData(t))]
                print("  tables whose bytes differ from the previous: %s" % " ".join(diff))
        prev = (data, f)


if __name__ == "__main__":
    main()
