#!/usr/bin/env python3
"""Question answered: can a family Google Fonts ships with NO sources anywhere be given a
source by converting its own binary with babelfont, and does that source rebuild the binary?

For each shipped .ttf given: babelfont reads it and writes a .glyphs (with the weight-class
workarounds of tools/workarounds.py: fontc 1.0.0 drops a single master's instance weightClass
and widthClass, so a usWeightClass other than 400 or usWidthClass other than 5 travels as FEA,
read from the binary); gftools-builder builds
that .glyphs (config: static, the source's own glyph names, no autohinting unless the binary
was ttfautohinted); the build is gated against the shipped binary exactly as tools/land.py
gates a conversion -- table gate (tools/table_gate.py), the release's exact codepoints,
tools/functional_gate.py (cmap, shaping, rendering, names, line spacing, advances, GDEF).

Usage: BF=<babelfont> B3=<gftools-builder> probe.py <scratch dir> <shipped.ttf>...
Prints one verdict line per font; the gate's blocking rows and failed checks follow it.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))   # tools/
import land  # noqa: E402
import functional_gate  # noqa: E402
import workarounds  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

BF = os.environ["BF"]
B3 = os.environ.get("B3", land.B3)


def probe(scratch, shipped):
    stem = os.path.splitext(os.path.basename(shipped))[0]
    work = os.path.join(scratch, stem)
    if os.path.isdir(work):
        assert work.startswith(scratch + os.sep) and work != scratch
        shutil.rmtree(work)
    os.makedirs(os.path.join(work, "sources"))
    glyphs = os.path.join(work, "sources", stem + ".glyphs")
    conv = subprocess.run([BF, shipped, glyphs], capture_output=True, text=True)
    if conv.returncode or not os.path.exists(glyphs):
        return stem, "CONVERT FAILED", [(conv.stderr or conv.stdout).strip()[-400:]]
    f = TTFont(shipped, lazy=True)
    for value, default, fea in ((f["OS/2"].usWeightClass, 400, workarounds.weight_class_fea),
                                (f["OS/2"].usWidthClass, 5, workarounds.width_class_fea)):
        if value != default:
            text = open(glyphs, encoding="utf-8").read()
            open(glyphs, "w", encoding="utf-8").write(fea(text, value))
    autohint = "ttfautohint" in (f["name"].getDebugName(5) or "") or "TTFA" in f
    with open(os.path.join(work, "sources", "config.yaml"), "w") as fh:
        fh.write("buildVariable: false\nproductionNames: false\n")
        if not autohint:
            fh.write("autohintTTF: false\n")
        fh.write("sources:\n  - %s.glyphs\n" % stem)
    b = subprocess.run([B3, "sources/config.yaml"], cwd=work, capture_output=True, text=True)
    ttf_dir = os.path.join(work, "fonts", "ttf")
    built = sorted(os.listdir(ttf_dir)) if os.path.isdir(ttf_dir) else []
    if len(built) != 1:
        tail = [l for l in (b.stderr + b.stdout).splitlines() if l.strip()][-3:]
        return stem, "BUILD FAILED (%s)" % (built or "nothing"), tail
    font = os.path.join(ttf_dir, built[0])
    n, blocking = land.gate(shipped, font, work)
    gained, lost = land.cmap_difference(shipped, font)
    if gained or lost:
        n += len(gained) + len(lost)
        blocking.append("CMAP gained %d lost %d" % (len(gained), len(lost)))
    fg = functional_gate.run(shipped, font, stem, d3_json=land.d3_json_path(font, work), workdir=work)
    bad = functional_gate.failed_checks(fg)
    verdict = "CLEAN" if n == 0 and not bad else "RESIDUAL"
    detail = blocking[:12] + (["functional: " + l for l in functional_gate.summary_lines(fg)[1:]] if bad else [])
    return stem, "%s: %d blocking row(s), functional %s" % (verdict, n, "PASS" if not bad else "FAIL(%s)" % "+".join(bad)), detail


def main():
    scratch = os.path.abspath(sys.argv[1])
    os.makedirs(scratch, exist_ok=True)
    for shipped in sys.argv[2:]:
        stem, verdict, detail = probe(scratch, os.path.abspath(shipped))
        print("%-32s %s" % (stem, verdict))
        for d in detail:
            print("    " + d)


if __name__ == "__main__":
    main()
