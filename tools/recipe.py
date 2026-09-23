#!/usr/bin/env python3
"""The conversion recipe: which babelfont flags a style is converted with, and why.

Question answered: given a style's source and the release it must reproduce, what
exactly is passed to babelfont? Every flag is a FIDELITY flag -- it replicates what
FontForge's own TTF exporter did -- and each per-release decision is asked of the
release, never guessed. Flags that babelfont's own help calls "a correction, not a
faithful conversion" (--single-line-names, --drop-copyright-description) and
--normalise-nbsp-width are never passed: a correction belongs in the history as a
visible .sfd edit.

Order matters: babelfont applies filters in command-line order, and
--fontforge-os2-defaults MEASURES the outlines (x-height, cap height), so it runs
first, on the outlines exactly as the source states them.

This is the same logic as tools/baseline.sh, in Python so that tools/land.py can
use it; `recipe.py --check` confirms the two agree on every style baseline.sh ran.

Usage:
  recipe.py <Style>        print the flags for one style
  recipe.py --check        compare with the flags recorded in baseline/*.gate.txt
"""
import os
import sys

from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE = ["--fontforge-os2-defaults", "--add-instance-per-master", "--infer-mark-category",
        "--set-subcategory", "--keep-source-glyph-names", "--keep-source-advances",
        "--snap-component-transforms", "--fontforge-underline-position"]


def legacy_duplicate_cmap(shipped):
    """makeotf's duplicate set: 'yes' only when the release maps both U+00A0 and U+00AD."""
    cm = TTFont(shipped).getBestCmap() or {}
    a, d = 0xA0 in cm, 0xAD in cm
    return "yes" if (a and d) else ("partial" if (a or d) else "no")


def directions_uniform(shipped):
    """Normalise contour direction only when the release does not mix the two senses."""
    f = TTFont(shipped)
    gs = f.getGlyphSet()
    cw = ccw = 0
    for name in f.getGlyphOrder():
        pen = AreaPen(gs)
        try:
            gs[name].draw(pen)
        except Exception:
            continue
        cw += pen.value < 0
        ccw += pen.value > 0
    return cw == 0 or ccw == 0


def flags_for(sfd_text, shipped, add=(), drop=()):
    """The babelfont arguments for one style, in order."""
    flags = list(BASE)
    flags.append("--correct-path-direction" if directions_uniform(shipped)
                 else "--reverse-path-direction")
    if legacy_duplicate_cmap(shipped) == "yes":
        flags.append("--add-legacy-duplicate-cmap")
    if "abvm" in sfd_text or "blwm" in sfd_text:
        flags.append("--correct-conjunct-category")
    flags += [f for f in add if f not in flags]
    return [f for f in flags if f not in set(drop)]


def rows():
    out = []
    with open(os.path.join(W, "families.tsv"), encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            out.append(dict(zip(head, line.rstrip("\n").split("\t"))))
    return out


def source_text(row):
    import subprocess
    path = f"{row['lic']}/{row['family']}/{row['source']}" if row["kind"] == "hg" else row["source"]
    arc = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
    return subprocess.run(["git", "-C", f"{arc}/{row['base']}.git", "show", f"{row['commit']}:{path}"],
                          capture_output=True, check=True).stdout.decode("utf-8", "replace")


def check():
    bad = 0
    for row in rows():
        log = os.path.join(W, "baseline", row["style"] + ".gate.txt")
        if not os.path.exists(log):
            continue
        recorded = next((l[len("flags: "):].split() for l in open(log) if l.startswith("flags: ")), None)
        ours = flags_for(source_text(row), row["shipped"])
        # baseline.sh ran before the recipe was reordered; compare as sets
        same = recorded is not None and set(recorded) == set(ours)
        bad += not same
        if not same:
            print("DIFFER %-26s baseline=%s recipe=%s" % (row["style"], recorded, ours))
    print("recipe.py agrees with baseline.sh on every recorded style" if not bad
          else "%d style(s) differ" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    row = next(r for r in rows() if r["style"] == sys.argv[1])
    print(" ".join(flags_for(source_text(row), row["shipped"])))
