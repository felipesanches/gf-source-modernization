#!/usr/bin/env python3
"""Question answered: is each "-TTF.sfd" / "-OTF.sfd" source we convert a FontForge import of
a shipped binary (the archival batch conversion Simon describes on google/fonts#10490,
2026-05-01: "they're batch-converted from the binary files ... generate fresh sources using
babelfont from the existing Google Fonts binaries"), or a working source?

Signals read from the .sfd at the commit families*.tsv pins, and from its directory:
  quadratic  the foreground layer is quadratic ("Layer: 1 1 ..."), as a TrueType import is;
             a designer's FontForge working file is cubic unless set otherwise
  instrs     the file keeps TrueType instructions (TtInstrs / prep / fpgm): copied from a
             hinted binary
  sameday    CreationTime and ModificationTime fall on the same day (no editing history)
  vfb_twin   a .vfb of the same style sits next to it (the "SFD *and* VFB of the same file"
             pattern)
Verdict: IMPORT when quadratic and (instrs or vfb_twin); LIKELY-IMPORT when quadratic alone;
WORKING otherwise. A verdict is evidence for the source-format decision, not the decision.

Usage: python3 -I tools/probes/ttf_sfd_origin/origin.py > tools/probes/ttf_sfd_origin/results-<date>.tsv
"""
import csv, datetime, os, re, subprocess, sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"


def git(mirror, *a):
    return subprocess.run(("git", "-C", mirror) + a, capture_output=True, text=True).stdout


def main():
    rows = []
    for t in ("families.tsv", "families-next.tsv"):
        rows += [dict(r, table=t) for r in csv.DictReader(open(os.path.join(W, t)), delimiter="\t")]
    print("\t".join(["repo", "style", "table", "source", "quadratic", "instrs", "sameday", "vfb_twin", "verdict"]))
    for r in rows:
        src = r["source"]
        if not re.search(r"-(TTF|OTF)\.sfd$", src):
            continue
        mirror = os.path.join(ARC, r["base"] + ".git")
        prefix = "%s/%s/" % (r["lic"], r["family"]) if r["kind"] == "hg" else ""
        path = prefix + src
        text = git(mirror, "show", "%s:%s" % (r["commit"], path))
        if not text:
            print("\t".join([r["repo"], r["style"], r["table"], path, "?", "?", "?", "?", "UNREADABLE"]))
            continue
        head = text[:20000]
        quad = bool(re.search(r"^Layer: 1 1 ", head, re.M)) or bool(re.search(r"^Order2: 1", head, re.M))
        instrs = bool(re.search(r"^(TtInstrs:|TtTable: (prep|fpgm))", text, re.M))
        ct = re.search(r"^CreationTime: (\d+)", head, re.M)
        mt = re.search(r"^ModificationTime: (\d+)", head, re.M)
        same = "?"
        if ct and mt:
            d = lambda s: datetime.datetime.fromtimestamp(int(s), datetime.timezone.utc).date()
            same = "yes" if d(ct.group(1)) == d(mt.group(1)) else "no"
        sib = git(mirror, "ls-tree", "--name-only", r["commit"], os.path.dirname(path) + "/").split()
        stem = re.sub(r"-(TTF|OTF)\.sfd$", "", os.path.basename(path))
        twin = any(os.path.basename(s).startswith(stem) and s.endswith(".vfb") for s in sib)
        if quad and (instrs or twin):
            v = "IMPORT"
        elif quad:
            v = "LIKELY-IMPORT"
        else:
            v = "WORKING"
        print("\t".join([r["repo"], r["style"], r["table"], path, "yes" if quad else "no",
                         "yes" if instrs else "no", same, "yes" if twin else "no", v]))


if __name__ == "__main__":
    sys.exit(main())
