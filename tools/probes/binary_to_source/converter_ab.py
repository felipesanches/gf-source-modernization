#!/usr/bin/env python3
"""Question answered: which binary-only families get a different source from converter B than
from converter A? With A the measured babelfont (every unmerged branch the landings used) and B
a babelfont with fewer of those branches, a family that converts the SAME with B does not need
the branches B leaves out.

Each shipped TTF of families-binary.tsv is converted as tools/land.py converts it (`babelfont
<ttf> <out.glyphs>`, no flags) by both converters, and the two .glyphs files are compared as
same_sources.py compares them (each `date` line dropped, master UUIDs replaced by their order
of first appearance).

  GF=<google/fonts clone> ARCHIVE=<repo archive> \
    python3 converter_ab.py <babelfont A> <babelfont B> <scratch dir> [repo ...]

Shipped fonts come from the google/fonts clone at each row's commit or, for a row whose base
is another repository, from its bare mirror in the repo archive, read with `git show` only.
Prints one line per repo (SAME, or DIFFERENT with the number of styles that differ and the
first differing line of the first one) and a total; writes each differing style's diff to
<scratch dir>/<repo>/<style>.diff.
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from same_sources import normalised  # noqa: E402

TSV = os.path.join(HERE, "..", "..", "..", "families-binary.tsv")
GF = os.environ.get("GF", "")            # a google/fonts clone
ARCHIVE = os.environ.get("ARCHIVE", "")  # the repo archive of bare mirrors


def shipped_bytes(row):
    if row["base"] == "google/fonts":
        repo, path = GF, row["shipped"]
    else:
        repo, path = os.path.join(ARCHIVE, row["base"] + ".git"), row["source"]
    return subprocess.run(["git", "-C", repo, "show", "%s:%s" % (row["commit"], path)],
                          capture_output=True, check=True).stdout


def convert(bf, ttf, out):
    r = subprocess.run([bf, ttf, out], capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        return None, (r.stderr.strip().splitlines() or ["exit %d" % r.returncode])[-1]
    return normalised(out), None


def main():
    if len(sys.argv) < 4 or not GF or not ARCHIVE:
        sys.exit(__doc__)
    bf_a, bf_b, scratch = sys.argv[1:4]
    only = set(sys.argv[4:])
    rows = [r for r in csv.DictReader(open(TSV), delimiter="\t") if not only or r["repo"] in only]
    by_repo = {}
    for r in rows:
        by_repo.setdefault(r["repo"], []).append(r)
    total = {"SAME": 0, "DIFFERENT": 0, "ERROR": 0}
    for repo, styles in by_repo.items():
        d = os.path.join(scratch, repo)
        os.makedirs(d, exist_ok=True)
        differing, first, error = [], "", ""
        for r in styles:
            ttf = os.path.join(d, r["style"] + ".ttf")
            with open(ttf, "wb") as fh:
                fh.write(shipped_bytes(r))
            a, err_a = convert(bf_a, ttf, os.path.join(d, r["style"] + ".a.glyphs"))
            b, err_b = convert(bf_b, ttf, os.path.join(d, r["style"] + ".b.glyphs"))
            if err_a or err_b:
                error = error or "%s: A %s / B %s" % (r["style"], err_a or "ok", err_b or "ok")
                continue
            if a == b:
                continue
            # GNU diff: difflib is quadratic on a CJK font's .glyphs file
            na, nb = (os.path.join(d, r["style"] + ext) for ext in (".a.norm", ".b.norm"))
            open(na, "wb").write(a)
            open(nb, "wb").write(b)
            out = subprocess.run(["diff", "-U2", "--label", "A/" + r["style"], "--label",
                                  "B/" + r["style"], na, nb], capture_output=True).stdout
            open(os.path.join(d, r["style"] + ".diff"), "wb").write(out)
            differing.append(r["style"])
            if not first:
                lines = out.decode("utf-8", "replace").splitlines()[2:]
                first = next((l for l in lines if l[:1] in "+-" and l[1:].strip(" {}(),;")), "").strip()
        if error:
            verdict = "ERROR %s" % error
            total["ERROR"] += 1
        elif differing:
            verdict = "DIFFERENT %d/%d styles; first: %s" % (len(differing), len(styles), first[:160])
            total["DIFFERENT"] += 1
        else:
            verdict = "SAME %d styles" % len(styles)
            total["SAME"] += 1
        print("%-22s %s" % (repo, verdict), flush=True)
    print("total: %d repos; %s" % (len(by_repo), ", ".join("%s %d" % kv for kv in total.items())))


if __name__ == "__main__":
    main()
