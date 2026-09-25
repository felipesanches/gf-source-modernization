#!/usr/bin/env python3
"""Which commit of the source repository holds the .sfd state a release was exported from?

Question answered: FontForge writes the .sfd's ModificationTime into the exported font's
FFTM table (sourceModified). For a release exported by FontForge, which commits of the
upstream repository carry a source whose `ModificationTime:` equals that stamp, and do they
also agree with the release's version string and PANOSE? The pairing table may name a
commit chosen by another heuristic (a version tag of a different family, the monorepo tip);
this asks the release itself.

Prints, for every commit touching the path (newest first): ModificationTime, Version,
Panose, and MATCH when ModificationTime == the release's FFTM sourceModified.

Usage:
  fftm_source_commit.py <release.ttf> <bare-repo.git> <path/in/repo.sfd>

Example (the pairs this unit measured):
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
  GF=/home/fsanches/compartilhado/google/fonts            # at b5efa9c32e8f
  $PY fftm_source_commit.py $GF/ofl/lohitbengali/Lohit-Bengali.ttf $ARC/pravins/lohit.git bengali/Lohit-Bengali.sfd
  $PY fftm_source_commit.py $GF/ofl/lohittamil/Lohit-Tamil.ttf $ARC/pravins/lohit.git tamil/Lohit-Tamil.sfd
  $PY fftm_source_commit.py $GF/ofl/thabit/Thabit.ttf $ARC/googlefonts/googlefontdirectory-hg.git ofl/thabit/src/Thabit.sfd
"""
import datetime
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

UNIX_FROM_1904 = 2082844800


def utc(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main(release, repo, path):
    f = TTFont(release)
    if "FFTM" not in f:
        sys.exit("release has no FFTM table: not a FontForge export")
    src_mod = f["FFTM"].sourceModified - UNIX_FROM_1904
    stamp = f["FFTM"].FFTimeStamp - UNIX_FROM_1904
    ver = f["name"].getDebugName(5)
    pan = f["OS/2"].panose
    pan_s = " ".join(str(getattr(pan, k)) for k in (
        "bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast",
        "bStrokeVariation", "bArmStyle", "bLetterForm", "bMidline", "bXHeight"))
    print("release %s" % release)
    print("  FFTM FontForge build %s, sourceModified %d (%s UTC)" % (utc(stamp), src_mod, utc(src_mod)))
    print("  name 5 %r, PANOSE %s" % (ver, pan_s))
    log = subprocess.run(["git", "-C", repo, "log", "--format=%H %ad %s", "--date=iso", "--all", "--", path],
                         capture_output=True, text=True, check=True).stdout.splitlines()
    for line in log:
        sha = line.split()[0]
        r = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (sha, path)], capture_output=True)
        if r.returncode:
            print("%s  (path absent)  %s" % (sha[:9], line[41:]))
            continue
        head = r.stdout.decode("utf-8", "replace").split("\nStartChar:", 1)[0]
        g = lambda k: (re.search(r"^%s: (.*)$" % k, head, re.M) or [None, "-"])[1]
        mt = g("ModificationTime")
        mark = "MATCH" if mt != "-" and int(mt) == src_mod else "     "
        print("%s %s ModificationTime %s  Version %-8s Panose %-22s %s" % (
            mark, sha[:9], mt, g("Version"), g("Panose"), line[41:]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
