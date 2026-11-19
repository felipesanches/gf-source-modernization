#!/usr/bin/env python3
"""Question answered: what does a follow-up branch (font development on top of a landed,
equivalent conversion) change in the fonts, compared with the fonts Google Fonts ships?

A follow-up is NOT held to equivalence: every difference it makes is meant to be reviewed
and QA'd. This builds the branch exactly as tools/land.py builds a landing (its own
sources/config.yaml, the pinned gftools-builder, in a scratch copy) and runs the same
gates, so the report lists what a reviewer has to look at: the table gate's blocking rows,
codepoints gained and lost, and every functional check (cmap, shaping, rendering, names,
line spacing, advances, GDEF, hinting) with examples.

Usage: measure.py <checkout> <style>=<shipped.ttf> [<style>=<shipped.ttf> ...]
  <checkout>   the follow-up branch, checked out (a worktree of the landed repository)
  <style>      the built file's name without .ttf (fonts/ttf/<style>.ttf)
Environment: B3=<gftools-builder> (default: tools/land.py B3_DEFAULT); SCRATCH as land.py.
Prints the report; the build stays in the scratch directory it names.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # tools/
import land  # noqa: E402
import functional_gate  # noqa: E402


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    d = os.path.abspath(sys.argv[1])
    pairs = [a.split("=", 1) for a in sys.argv[2:]]
    os.makedirs(land.SCRATCH, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="followup-", dir=land.SCRATCH)
    shutil.copytree(os.path.join(d, "sources"), os.path.join(scratch, "sources"))
    r = subprocess.run([land.B3, "sources/config.yaml"], cwd=scratch, capture_output=True, text=True)
    head = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    b3 = subprocess.run([land.B3, "--version"], capture_output=True, text=True).stdout.strip()
    print("follow-up %s at %s, built in %s with %s" % (d, head, scratch, b3 or land.B3))
    for style, shipped in pairs:
        font = os.path.join(scratch, "fonts", "ttf", style + ".ttf")
        if not os.path.exists(font):
            tail = [l for l in (r.stderr + r.stdout).splitlines() if l.strip()][-5:]
            print("%s: BUILD FAILED\n  %s" % (style, "\n  ".join(tail)))
            continue
        n, blocking = land.gate(shipped, font, scratch)
        gained, lost = land.cmap_difference(shipped, font)
        print("%s: %d blocking table row(s); codepoints gained %d, lost %d" % (style, n, len(gained), len(lost)))
        if gained:
            print("  gained: " + " ".join("U+%04X" % c for c in gained))
        if lost:
            print("  lost:   " + " ".join("U+%04X" % c for c in lost))
        for row in blocking:
            print("  " + row[:300])
        fg = functional_gate.run(shipped, font, style, d3_json=land.d3_json_path(font, scratch), workdir=scratch)
        for line in functional_gate.summary_lines(fg, per_check=8):
            print("  " + line)


if __name__ == "__main__":
    main()
