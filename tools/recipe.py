#!/usr/bin/env python3
"""The conversion recipe: which babelfont flags a style is converted with, and why.

Question answered: given a style's source and the release it must reproduce, what
exactly is passed to babelfont? Every flag is a FIDELITY flag -- it replicates what
FontForge's own TTF exporter did -- and each per-release decision is asked of the
release, never guessed. Flags that babelfont's own help calls "a correction, not a
faithful conversion" (--single-line-names, --drop-copyright-description) and
--normalise-nbsp-width are never passed: a correction belongs in the history as a
visible .sfd edit.

Order matters: babelfont applies filters in command-line order, and the height
filters MEASURE the outlines, so they run first, on the outlines exactly as the
source states them. --fontforge-height-glyph-count-mean, when chosen, runs before
--fontforge-os2-defaults, because each fills only a height still missing.

This is the only implementation of the recipe: tools/baseline.sh and tools/land.py
both call it.

Usage:
  recipe.py <Style>        print the flags for one style, one per line
"""
import os
import sys

from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FontForge's x-height/cap-height mean changed in 4d34d21ef866; FFTM records
# stamp.c's source_modtime, which for that build is 1337023489 (2012-05-14T19:24:49Z).
# The old divisor entered in 37d20840 (2009-05-27), before every stamp in this batch.
# (5fba6c9 is the same change in a history with no common ancestor with 4d34d21ef866.)
FONTFORGE_HEIGHT_MEAN_FIXED = 1337023489
# FontForge raises the OS/2 version to 4 for USE_TYPO_METRICS from tag 20150824 on; up to
# 20141230 it wrote the source's OS2Version 1-3 as stated, so bit 7 never shipped
# (investigations/reland-2026-10-01/linespacing/bit7_sweep.txt).
FONTFORGE_OS2_VERSION_RAISED = 1440374400   # 2015-08-24T00:00:00Z
UNIX_FROM_1904 = 2082844800

# Glyph names and contour directions are not babelfont flags any more: the source keeps
# both, and sources/config.yaml asks the builder for them (noProductionNames: true;
# reverseOutlineDirection: false when a release mixes directions -- see land.py).
# Near-integer reference matrices are snapped by babelfont's SFD reader (#98).
BASE = ["--fontforge-os2-defaults", "--add-instance-per-master", "--infer-mark-category",
        "--set-subcategory", "--keep-source-advances", "--fontforge-underline-position",
        "--round-coordinates"]


# makeotf's duplicate cmap entries: each maps a second codepoint to the glyph of the
# first. --add-legacy-duplicate-cmap adds all of them.
MAKEOTF_DUPLICATES = [(0x00A0, 0x0020), (0x00AD, 0x002D), (0x02C9, 0x00AF),
                      (0x2219, 0x00B7), (0x03BC, 0x00B5), (0x2126, 0x03A9),
                      (0x2206, 0x0394), (0x2215, 0x002F)]


def legacy_duplicate_cmap(shipped):
    """Does the release carry makeotf's duplicate entries -- a codepoint mapped to the
    SAME glyph as its partner? Merely mapping U+00A0 and U+00AD is not evidence: a
    source can draw them as glyphs of their own (Corben does), and the flag would then
    add U+02C9, U+2219 and U+03BC that the release does not have. (Corben-Bold
    verification, sfd-reland/investigations/corben-bold.)"""
    cm = TTFont(shipped).getBestCmap() or {}
    return "yes" if any(a in cm and b in cm and cm[a] == cm[b] for a, b in MAKEOTF_DUPLICATES) else "no"


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


def fontforge_build(shipped):
    """The build stamp of the FontForge that exported the release, as Unix time, or
    None when the release has no FFTM table (not exported by FontForge)."""
    f = TTFont(shipped)
    if "FFTM" not in f:
        return None
    return f["FFTM"].FFTimeStamp - UNIX_FROM_1904


def flags_for(sfd_text, shipped, add=(), drop=(), keep_direction=False):
    """The babelfont arguments for one style, in order. keep_direction: the repository's
    config.yaml keeps source contour directions (a release of the family mixes them)."""
    flags = list(BASE)
    built = fontforge_build(shipped)
    if built is not None and built < FONTFORGE_HEIGHT_MEAN_FIXED:
        flags.insert(0, "--fontforge-height-glyph-count-mean")
    if built is not None and built < FONTFORGE_OS2_VERSION_RAISED:
        flags.append("--fontforge-legacy-os2-version")
    # FontForge writes GDEF only when it exports OpenType layout; a release exported
    # with only the legacy 'kern' table (Miama, Ultra, Nosifer) has none to reproduce.
    if "GDEF" in TTFont(shipped):
        flags.append("--fontforge-gdef-classes")
    if not keep_direction:
        flags.append("--correct-path-direction")
    # --add-legacy-duplicate-cmap is NEVER passed. It adds makeotf's duplicate set,
    # and these releases were exported by FontForge, whose duplicate mappings come
    # from the .sfd's own AltUni2 alternates. Measured on all 42 styles
    # (probes/cmap_recipe/RESULT.tsv): without it every style outside play and tuffy
    # maps EXACTLY its release's codepoints; with it 11 landed styles gained 1-3.
    if "abvm" in sfd_text or "blwm" in sfd_text:
        flags.append("--correct-conjunct-category")
    flags += [f for f in add if f not in flags]
    return [f for f in flags if f not in set(drop)]


def keep_direction(shipped_fonts):
    """Whether a repository's builds must keep source contour directions: any release
    of it mixes the two senses (fontc --keep-direction, config reverseOutlineDirection)."""
    return any(not directions_uniform(s) for s in shipped_fonts)


def families_file():
    """The pairing table: families.tsv, or another batch's (FAMILIES=<path>)."""
    return os.environ.get("FAMILIES", os.path.join(W, "families.tsv"))


def rows():
    out = []
    with open(families_file(), encoding="utf-8") as fh:
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


if __name__ == "__main__":
    row = next(r for r in rows() if r["style"] == sys.argv[1])
    print("\n".join(flags_for(source_text(row), row["shipped"])))
