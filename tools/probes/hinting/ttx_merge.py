"""Can `ttx -m` carry a release's glyph programs into a built font?

Answers Simon's question on googlefonts/gftools#1248 (merge a TTX dump instead
of a hinting file). Two merges into a copy of the release itself:

1. a TTX dump of fpgm, prep, cvt and gasp: whole tables, expected to work;
2. a TTX dump of glyf holding one glyph (with its program): if `ttx -m` merged
   per glyph this would compile; if it replaces the whole table it fails on the
   first glyph the dump lacks.

Usage: python -I ttx_merge.py <scratch dir> <release.ttf>
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont


def ttx(*args):
    return subprocess.run(
        [sys.executable, "-I", "-m", "fontTools.ttx", "-q", *args],
        capture_output=True,
        text=True,
    )


def main():
    scratch, release = Path(sys.argv[1]), Path(sys.argv[2])
    scratch.mkdir(parents=True, exist_ok=True)
    base = scratch / "base.ttf"
    shutil.copyfile(release, base)
    print(f"release: {release.name}")

    tables = [t for t in ("fpgm", "prep", "cvt ", "gasp") if t in TTFont(base)]
    dump = scratch / "programs.ttx"
    ttx(*sum((["-t", t] for t in tables), []), "-o", str(dump), str(base))
    merged = scratch / "merged-programs.ttf"
    r = ttx("-m", str(base), "-o", str(merged), str(dump))
    same = r.returncode == 0 and all(
        TTFont(merged).getTableData(t) == TTFont(base).getTableData(t) for t in tables
    )
    print(f"1. merge {','.join(t.strip() for t in tables)}: exit {r.returncode}, tables identical: {same}")

    full = scratch / "glyf.ttx"
    ttx("-t", "glyf", "-o", str(full), str(base))
    s = full.read_text()
    head, rest = s.split("<glyf>", 1)
    body, tail = rest.split("</glyf>", 1)
    glyphs = re.findall(r'<TTGlyph name="[^"]*".*?</TTGlyph>', body, re.S)
    keep = next(g for g in glyphs if "<instructions>" in g and "<assembly>" in g and "<contour>" in g)
    name = re.match(r'<TTGlyph name="([^"]*)"', keep).group(1)
    one = scratch / "glyf-one.ttx"
    one.write_text(head + "<glyf>\n" + keep + "\n</glyf>" + tail)
    r = ttx("-m", str(base), "-o", str(scratch / "merged-glyf.ttf"), str(one))
    last = (r.stderr.strip().splitlines() or [""])[-1]
    print(f"2. merge glyf holding only {name!r} of {len(glyphs)} glyphs: exit {r.returncode}: {last}")


if __name__ == "__main__":
    main()
