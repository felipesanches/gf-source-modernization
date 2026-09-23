#!/usr/bin/env python3
"""Proposed source_corrections.py op: renameglyphgid <gid> <old> <new>

Question it answers: can a .sfd that holds TWO glyphs with the same name be made
convertible without changing which glyph every by-name reference binds to?

The existing `renameglyph <old> <new>` renames the FIRST "StartChar: <old>" and then
every standalone occurrence of <old> in the file (kern classes, substitutions). With a
duplicated name that is wrong twice over: it renames the glyph FontForge treated as the
real one and rebinds all by-name references to the new name.

This op renames exactly one StartChar -- the one whose "Encoding:" line carries <gid>
as its third field (the glyph's index in the SFD) -- and touches nothing else, so
by-name references keep resolving to the remaining <old> glyph, exactly as FontForge
resolved them when it exported the release. Lines inside the renamed glyph's own block
(its Substitution2/Kerns2 lines) are data OF that glyph and move with it.

FATAL unless: exactly one StartChar named <old> has that gid, <old> is duplicated
(otherwise use renameglyph), and <new> is not already a StartChar.

Usage: renameglyphgid.py <in.sfd> <out.sfd> <gid> <old> <new>
"""
import re
import sys


def main():
    src, dst, gid, old, new = sys.argv[1:6]
    gid = int(gid)
    text = open(src, encoding="utf-8", errors="surrogateescape").read()
    starts = [m for m in re.finditer(r"^StartChar: (.*)\n", text, re.M)]
    same = [m for m in starts if m.group(1) == old]
    if len(same) < 2:
        sys.exit("FATAL: %s is not duplicated (%d StartChar); use renameglyph" % (old, len(same)))
    if any(m.group(1) == new for m in starts):
        sys.exit("FATAL: StartChar: %s already exists" % new)
    hit = []
    for m in same:
        enc = re.match(r"Encoding: (-?\d+) (-?\d+) (\d+)", text[m.end():m.end() + 80])
        if enc and int(enc.group(3)) == gid:
            hit.append(m)
    if len(hit) != 1:
        sys.exit("FATAL: %d StartChar: %s with gid %d" % (len(hit), old, gid))
    m = hit[0]
    text = text[:m.start()] + "StartChar: %s\n" % new + text[m.end():]
    open(dst, "w", encoding="utf-8", errors="surrogateescape").write(text)
    print("renamed StartChar %s (gid %d) -> %s" % (old, gid, new))


if __name__ == "__main__":
    main()
