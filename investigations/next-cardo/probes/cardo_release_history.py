#!/usr/bin/env python3
"""Where do the Cardo releases come from, and what did google/fonts change after export?

Question answered, per style (Regular, Bold, Italic):
  1. provenance: does the paired source old/version-1.000/Cardo-<Style>-TTF.sfd at
     googlefonts/CardoFont b2bf876 (families-next.tsv) carry the CreationTime and
     ModificationTime the release's FFTM records, and the same glyph count? (FontForge
     writes the .sfd's times into FFTM at export, so equal values pair them exactly.)
  2. every google/fonts commit that changed ofl/cardo/Cardo-<Style>.ttf after the
     first: which tables' compiled bytes differ, which glyph advances changed, and
     whether the cmap MAPPINGS changed (not only their packing).
Evidence for the Italic `nbspwidth` edit: d70318ab8 (2015-04-27, "Updating
ofl/cardo/*ttf with nbspace and fsType fixes") changed only Italic, and in it only
the nonbreakingspace advance (550 -> 575, the space's).

Usage:  cardo_release_history.py
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import datetime
import io
import re
import subprocess

from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/CardoFont.git"
BASE = "b2bf876b4e251ac44b343605464dad86b336b38d"
UNIX_FROM_1904 = 2082844800


def git(*a, cwd=GF):
    return subprocess.run(["git", "-C", cwd] + list(a), capture_output=True, check=True).stdout


def iso(t):
    return datetime.datetime.fromtimestamp(t, datetime.UTC).isoformat()


for style in ("Regular", "Bold", "Italic"):
    path = "ofl/cardo/Cardo-%s.ttf" % style
    print("== Cardo-%s" % style)
    sfd = git("show", "%s:old/version-1.000/Cardo-%s-TTF.sfd" % (BASE, style), cwd=ARC).decode(
        "utf-8", "replace")
    ct = int(re.search(r"^CreationTime: (\d+)", sfd, re.M).group(1))
    mt = int(re.search(r"^ModificationTime: (\d+)", sfd, re.M).group(1))
    rel = TTFont(io.BytesIO(git("show", "HEAD:" + path)))
    ff = rel["FFTM"]
    print("  sfd CreationTime %s ModificationTime %s glyphs %d"
          % (iso(ct), iso(mt), sfd.count("\nStartChar:")))
    print("  FFTM sourceCreated %s sourceModified %s (FontForge build %s); release glyphs %d"
          % (iso(ff.sourceCreated - UNIX_FROM_1904), iso(ff.sourceModified - UNIX_FROM_1904),
             iso(ff.FFTimeStamp - UNIX_FROM_1904), rel["maxp"].numGlyphs))
    print("  paired exactly: %s" % (ct == ff.sourceCreated - UNIX_FROM_1904
                                     and mt == ff.sourceModified - UNIX_FROM_1904))
    commits = git("log", "--format=%h %ad %s", "--date=short", "--", path).decode().splitlines()
    revs = [c.split()[0] for c in reversed(commits)]
    prev = None
    for c in revs:
        try:
            f = TTFont(io.BytesIO(git("show", "%s:%s" % (c, path))))
        except subprocess.CalledProcessError:
            continue
        if prev is not None:
            tables = sorted(t for t in set(f.keys()) | set(prev.keys()) if t != "GlyphOrder"
                            and (t not in f or t not in prev
                                 or f.getTableData(t) != prev.getTableData(t)))
            if tables:
                adv = [(n, prev["hmtx"][n][0], f["hmtx"][n][0]) for n in f.getGlyphOrder()
                       if n in prev["hmtx"].metrics and prev["hmtx"][n] != f["hmtx"][n]]
                cmap_same = prev.getBestCmap() == f.getBestCmap()
                subj = next(x for x in commits if x.startswith(c))
                print("  %s: tables %s; advances changed %s; cmap mappings equal: %s"
                      % (subj, tables, adv, cmap_same))
        prev = f
