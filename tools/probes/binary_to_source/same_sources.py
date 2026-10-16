#!/usr/bin/env python3
"""Question answered: did re-landing a family give it the same sources as the generation
before (land.py keeps that one as <repos>/<repo>.prev), once what babelfont's Glyphs writer
makes up on every run is set aside?

babelfont writes two values that change on every run with the same input: the file's `date`
(the time of writing) and a random UUID for each master id, which every layer then repeats as
its layerId/associatedMasterId. So each `date = ...;` line is dropped and each UUID is replaced
by its order of first appearance in the file. Every other file under sources/ must be identical.

  python3 same_sources.py <repos dir> [repo ...]     # default: every repo of families-binary.tsv

Prints one line per repo (SAME, DIFFERENT with the first differing file, or NO-PREV) and a
total; exits 1 if any repo is DIFFERENT.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "..", "..", "..", "families-binary.tsv")
UUID = re.compile(rb"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
DATE = re.compile(rb"^date = .*;\n", re.M)


def normalised(path):
    data = open(path, "rb").read()
    if not path.endswith(".glyphs"):
        return data
    data = DATE.sub(b"", data)
    seen = {}
    return UUID.sub(lambda m: b"<uuid %d>" % seen.setdefault(m.group(0).lower(), len(seen)), data)


def files(root):
    out = []
    for dirpath, _dirs, names in os.walk(root):
        out += [os.path.relpath(os.path.join(dirpath, n), root) for n in names]
    return sorted(out)


def compare(repos, repo):
    new, old = os.path.join(repos, repo, "sources"), os.path.join(repos, repo + ".prev", "sources")
    if not os.path.isdir(old):
        return "NO-PREV", ""
    fn, fo = files(new), files(old)
    if fn != fo:
        return "DIFFERENT", "file lists: %s" % sorted(set(fn) ^ set(fo))
    for f in fn:
        if normalised(os.path.join(new, f)) != normalised(os.path.join(old, f)):
            return "DIFFERENT", f
    return "SAME", "%d file(s)" % len(fn)


def main():
    repos = sys.argv[1]
    names = sys.argv[2:]
    if not names:
        with open(TSV) as fh:
            rows = [line.rstrip("\n").split("\t") for line in fh][1:]
        names = list(dict.fromkeys(r[0] for r in rows if len(r) > 3 and r[3] == "binary"))
    tally = {}
    for repo in names:
        verdict, detail = compare(repos, repo)
        tally[verdict] = tally.get(verdict, 0) + 1
        print("%-24s %-9s %s" % (repo, verdict, detail))
    print("total: " + ", ".join("%s %d" % kv for kv in sorted(tally.items())))
    sys.exit(1 if tally.get("DIFFERENT") else 0)


if __name__ == "__main__":
    main()
