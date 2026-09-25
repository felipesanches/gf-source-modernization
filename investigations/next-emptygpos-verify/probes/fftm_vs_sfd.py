#!/usr/bin/env python3
"""Is the paired .sfd the file the release was exported from?

Question: for every row of a pairing table (families.tsv / families-next.tsv), does
the release's FFTM sourceModified / sourceCreated equal the paired .sfd's
ModificationTime / CreationTime? FontForge copies both .sfd fields into FFTM at
export (FFTM stores them as seconds since 1904; subtract 2082844800 for Unix time).
A release whose sourceModified is OLDER than the .sfd's ModificationTime was
exported from an earlier state of the file: the pairing names a later revision
than the one that shipped (Ultra-Regular: see runs/02-ultra-may-sfd).

Signal read: FFTM.sourceCreated/sourceModified of the release; `CreationTime:` and
`ModificationTime:` of the .sfd read with `git show <commit>:<path>` from the repo
archive (for kind hg the path is <lic>/<fam>/<src>, as tools/baseline.sh extracts
it). Output one line per style: MATCH / SFD-NEWER / SFD-OLDER / NO-FFTM / NO-SFD.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 fftm_vs_sfd.py <families.tsv> [<Style> ...]
"""
import csv
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
EPOCH = 2082844800


def sfd_times(base, commit, path):
    try:
        data = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show", "%s:%s" % (commit, path)],
                              capture_output=True, check=True).stdout[:200000].decode("latin-1")
    except subprocess.CalledProcessError:
        return None
    c = re.search(r"^CreationTime: (\d+)", data, re.M)
    m = re.search(r"^ModificationTime: (\d+)", data, re.M)
    return (int(c.group(1)) if c else None, int(m.group(1)) if m else None)


def main():
    fam = sys.argv[1]
    only = set(sys.argv[2:])
    for r in csv.reader(open(fam), delimiter="\t"):
        if r[0] == "repo" or len(r) < 9:
            continue
        repo, family, lic, kind, base, commit, style, src, shipped = r[:9]
        if only and style not in only:
            continue
        path = "%s/%s/%s" % (lic, family, src) if kind == "hg" else src
        t = sfd_times(base, commit, path)
        f = TTFont(shipped)
        if "FFTM" not in f:
            print("%-32s NO-FFTM" % style)
            continue
        if t is None:
            print("%-32s NO-SFD %s" % (style, path))
            continue
        created, modified = f["FFTM"].sourceCreated - EPOCH, f["FFTM"].sourceModified - EPOCH
        verdict = "MATCH" if modified == t[1] else ("SFD-NEWER" if t[1] and t[1] > modified else "SFD-OLDER")
        print("%-32s %-9s release sourceModified %s created %s | sfd ModificationTime %s CreationTime %s" % (
            style, verdict, modified, created, t[1], t[0]))


if __name__ == "__main__":
    main()
