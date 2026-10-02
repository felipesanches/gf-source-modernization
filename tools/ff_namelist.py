#!/usr/bin/env python3
"""FontForge's glyph-name -> Unicode rule (UniFromName), as the 2008 build had it.

Promoted 2026-10-02 from investigations/next-provenance/probes/ff_namelist.py (unchanged
below this note); tools/ff_build_ops.py imports it.

Question answered: when FontForge 2008-08-08 (git eb711fd7, the build Thabit 0.02's FFTM
stamp names) loaded IBM Courier (cour.pfa), which codepoint did it give each glyph NAME?
fontTools' AGL answers differently for some names (Omega -> U+2126, micro/ohm/dbar/Pts/
minussuperior and the IBM box-drawing names SF*/SM*/SS*/SV* unmapped), so a merge that asks
fontTools would encode the merged Latin differently from the release.

This reads fontforge/namelist.c at that commit and reproduces namelist.c UniFromName():
"uniXXXX" (exactly 7 chars), "U+XXXX"/"u+XXXX", "uXXXX[XX]", a one-character name, else
the hash of psaltnames[] then the name lists agl, agl_sans, adobepua, greeksc, tex, ams,
each walked plane/block/slot ascending; psaddbucket() prepends, so the LAST entry added
for a name wins. PUA results are dropped (recognizePUA is off by default).

Usage:
  ff_namelist.py [<namelist.c>]      print "name<TAB>U+XXXX" for every hashed name
  (import) uni_from_name(name) -> int (-1 when FontForge has no codepoint)
The source file is fetched from
https://raw.githubusercontent.com/fontforge/fontforge/eb711fd7249bfc1e8fc670e63e2f71d2069b508a/fontforge/namelist.c
into the scratch cache when no path is given.
"""
import os
import re
import sys
import urllib.request

SHA = "eb711fd7249bfc1e8fc670e63e2f71d2069b508a"
CACHE = "/home/fsanches/compartilhado/sfd-reland-scratch/provenance/ff2008/namelist.c"
URL = "https://raw.githubusercontent.com/fontforge/fontforge/%s/fontforge/namelist.c" % SHA

_TABLE = None


def _source(path=None):
    path = path or CACHE
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(URL, path)
    return open(path, encoding="utf-8", errors="replace").read()


def _entries(body):
    return [None if t == "NULL" else t.strip('"') for t in re.findall(r'NULL|"(?:[^"\\]|\\.)*"', body)]


def build(path=None):
    src = _source(path)
    blocks = {m.group(1): _entries(m.group(2)) for m in
              re.finditer(r"static const char \*(\w+)\[\] = \{(.*?)\};", src, re.S)}
    planes = {m.group(1): [None if t == "NULL" else t for t in re.findall(r"NULL|\w+", m.group(2))]
              for m in re.finditer(r"static const char \*\*(\w+)\[\] = \{(.*?)\};", src, re.S)}
    lists = {}
    for m in re.finditer(r"static NameList (\w+) = \{\s*([^,]+),\s*N?U?_\(\"[^\"]*\"\),\s*\{([^}]*)\}", src, re.S):
        lists[m.group(1)] = [None if t == "NULL" else t for t in re.findall(r"NULL|\w+", m.group(3))]
    alt = re.search(r"static struct psaltnames psaltnames\[\] = \{(.*?)\n\};", src, re.S)
    table = {}
    for name, uni in re.findall(r'\{\s*"([^"]+)",\s*(0x[0-9a-fA-F]+|\d+)\s*\}', alt.group(1)):
        table[name] = int(uni, 0)
    for nl in ("agl", "agl_sans", "adobepua", "greeksc", "tex", "ams"):
        for i, plane in enumerate(lists[nl]):
            if plane is None:
                continue
            for j, blk in enumerate(planes[plane]):
                if blk is None:
                    continue
                for k, name in enumerate(blocks[blk]):
                    if name is not None:
                        table[name] = (i << 16) | (j << 8) | k     # later wins
    return table


def uni_from_name(name, path=None):
    global _TABLE
    i = -1
    if name.startswith("uni"):
        m = re.fullmatch(r"uni([0-9A-Fa-f]{4})", name)
        i = int(m.group(1), 16) if m else -1
    elif name[:1] in "Uu" and name[1:2] == "+" and len(name) in (6, 7):
        try:
            i = int(name[2:], 16)
        except ValueError:
            i = -1
    elif name[:1] == "u" and len(name) >= 5:
        try:
            i = int(name[1:], 16)
        except ValueError:
            i = -1
    elif len(name) == 1:
        i = ord(name)
    if i == -1:
        if _TABLE is None:
            _TABLE = build(path)
        i = _TABLE.get(name, -1)
    if 0xE000 <= i <= 0xF8FF:
        i = -1
    return i


if __name__ == "__main__":
    t = build(sys.argv[1] if len(sys.argv) > 1 else None)
    for name in sorted(t):
        print("%s\tU+%04X" % (name, t[name]))
