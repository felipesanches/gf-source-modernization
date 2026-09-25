#!/usr/bin/env python3
"""Candidate .sfd edit: what FontForge's LEGACY `kern` export did to a kerning class
whose first class 0 is listed.

Question: Ultra's release kerns through a legacy `kern` table only (no GPOS; FFTM
names FontForge 20110222). Its source's KernClass2 is "26+ 27": the `+` means first
class 0 is listed (the A group). FontForge 20110222's SFKernClassTempDecompose
(splinesaveafm.c:2038, see ff-excerpts.txt) decomposes classes into kern pairs from
first class 1 upward, so class 0's row never reached the release: the release has
no pair whose first glyph is in the A group, while the build kerns them (A-T -55,
A-V -60, A-quotedbl -80, ...). Zeroing that row reproduces the release's pairs.
FontForge's GPOS writer (OpenType mode) DOES use class 0, so this applies only to a
release exported without OpenType tables.

Proposed as a new tools/sfd_edit.py operation (not added there: that file has
uncommitted changes from another session):
    kernclass0zero <subtable name>   zero every value in first-class-0's row of the
                                     named KernClass2; FATAL if the class has no
                                     listed class 0 ('+') or the matrix does not have
                                     first_cnt * second_cnt entries

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 sfd_kernclass0.py \
        <in.sfd> <out.sfd> "<KernClass2 subtable name>"
Prints the row before and after.
"""
import re
import sys


def kernclass0zero(text, subtable):
    lines = text.split("\n")
    head_re = re.compile(r'^KernClass2: (\d+)(\+?) (\d+)(\+?) "(.*)" ?$')
    for i, line in enumerate(lines):
        m = head_re.match(line)
        if not m or m.group(5) != subtable:
            continue
        n1, plus1, n2, plus2 = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        if not plus1:
            raise SystemExit("FATAL: %r lists no first class 0 (no '+'); nothing to zero"
                             % subtable)
        first_lines = n1 if plus1 else n1 - 1
        second_lines = n2 if plus2 else n2 - 1
        j = i + 1 + first_lines + second_lines
        tokens = re.findall(r"(-?\d+) (\{[^}]*\})", lines[j])
        if len(tokens) != n1 * n2:
            raise SystemExit("FATAL: matrix line has %d entries, expected %d x %d"
                             % (len(tokens), n1, n2))
        before = [int(v) for v, _ in tokens[:n2]]
        new = [("0", dev) if k < n2 else (v, dev) for k, (v, dev) in enumerate(tokens)]
        lead = re.match(r"^\s*", lines[j]).group(0)
        lines[j] = lead + " ".join("%s %s" % t for t in new)
        return "\n".join(lines), before
    raise SystemExit("FATAL: no KernClass2 named %r" % subtable)


def main():
    src, out, subtable = sys.argv[1:4]
    text = open(src, encoding="utf-8", errors="surrogateescape").read()
    new, before = kernclass0zero(text, subtable)
    open(out, "w", encoding="utf-8", errors="surrogateescape").write(new)
    print("first-class-0 row before: %s" % before)
    print("first-class-0 row after : all %d zero" % len(before))


if __name__ == "__main__":
    main()
