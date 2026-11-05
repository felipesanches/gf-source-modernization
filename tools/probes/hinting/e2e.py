#!/usr/bin/env python3
"""Route (a) end to end: release -> babelfont (TTF reader) -> .glyphs -> compiled font ->
hinting file applied -> functional_gate `hinting`. Which part still loses the release's
hinting?

Per release font:
  convert   <BF> <release.ttf> <scratch>/<stem>/sources/<stem>.glyphs
  fontmake  fontmake -g ... -o ttf --no-production-names --keep-overlaps (fontmake keeps
            on-curve points; overlap removal would rewrite them), then
            hinting_file.py extract <release> / apply, then the gate's hinting check
  fontc     gftools-builder (gftools-rust, <B3>) with buildVariable, removeOutlineOverlaps,
            productionNames, flattenComponents and decomposeTransformedComponents false
            (each would change the glyphs' names or points), then the same apply and check
            (the hinting file restores the explicit midpoint on-curves fontc drops)
Prints per font: points.py's summary for each build and the gate's status.

Usage: e2e.py <BF> <B3> <scratch> <release.ttf>...
FONTMAKE=<fontmake> picks another fontmake than the one beside this Python.
With EXTRACT=<gftools-extract-hinting> and APPLY=<gftools-apply-hinting> in the environment the
gftools builder step's own commands replace hinting_file.py. With HINTING_STEP=1 the hinting file
goes into sources/ and config.yaml names it under `hintingFiles`, so that <B3> applies it while
building (a gftools-builder with that step); the gate then checks the built font as it is.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import functional_gate as fg  # noqa: E402

PY = sys.executable
FONTMAKE = os.environ.get("FONTMAKE") or os.path.join(os.path.dirname(PY), "fontmake")
CONFIG = ("buildVariable: false\nremoveOutlineOverlaps: false\nproductionNames: false\n"
          "flattenComponents: false\ndecomposeTransformedComponents: false\nsources:\n  - %s.glyphs\n")


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def points(release, built):
    out = run([PY, os.path.join(HERE, "points.py"), release, built]).stdout
    return next((l for l in out.splitlines() if "point-identical" in l), out.strip()[-120:])


def check(release, built):
    A, B = fg.Font(release), fg.Font(built)
    _, _, ka, kb = fg.correspondence(A, B)
    c = fg.check_hinting(A, B, ka, kb, 3)
    return c["status"] + ("" if c["status"] == "PASS" else " (%s)" % "; ".join(f[:80] for f in c["failures"][:2]))


def gate(release, hfile, built, out):
    if os.environ.get("APPLY"):
        r = run([os.environ["APPLY"], "-o", out, built, hfile])
    else:
        r = run([PY, os.path.join(HERE, "hinting_file.py"), "apply", hfile, built, out])
    if r.returncode:
        # name the hinting file, not where the scratch directory is
        msg = r.stderr.strip().splitlines()[-1].replace(os.path.dirname(hfile) + os.sep, "")
        return "APPLY-REFUSED (%s)" % msg[:120]
    A, B = fg.Font(release), fg.Font(out)
    _, _, ka, kb = fg.correspondence(A, B)
    c = fg.check_hinting(A, B, ka, kb, 3)
    return c["status"] + ("" if c["status"] == "PASS" else " (%s)" % "; ".join(f[:80] for f in c["failures"][:2]))


def main():
    bf, b3, scratch = sys.argv[1:4]
    for release in sys.argv[4:]:
        stem = os.path.splitext(os.path.basename(release))[0]
        d = os.path.join(scratch, stem)
        os.makedirs(os.path.join(d, "sources"), exist_ok=True)
        glyphs = os.path.join(d, "sources", stem + ".glyphs")
        r = run([bf, release, glyphs])
        if r.returncode:
            print("%-26s convert FAILED %s" % (stem, r.stderr.strip()[-120:]), flush=True)
            continue
        hfile = os.path.join(d, stem + ".hinting.json")
        if os.environ.get("EXTRACT"):
            subprocess.run([os.environ["EXTRACT"], "-o", hfile, release], check=True)
        else:
            with open(hfile, "w") as fh:
                subprocess.run([PY, os.path.join(HERE, "hinting_file.py"), "extract", release], stdout=fh, check=True)
        fm = os.path.join(d, stem + ".fontmake.ttf")
        r = run([FONTMAKE, "-g", glyphs, "-o", "ttf", "--output-path", fm, "--no-production-names", "--keep-overlaps"], cwd=d)
        fm_res = ("%s | gate %s" % (points(release, fm), gate(release, hfile, fm, fm[:-4] + ".hinted.ttf"))
                  if os.path.exists(fm) else "fontmake FAILED " + r.stderr.strip()[-100:])
        print("%-26s fontmake %s" % (stem, fm_res), flush=True)
        step = os.environ.get("HINTING_STEP") == "1"
        with open(os.path.join(d, "sources", "config.yaml"), "w") as fh:
            fh.write(CONFIG % stem)
            if step:
                shutil.copy(hfile, os.path.join(d, "sources", stem + ".hinting.json"))
                fh.write("hintingFiles:\n  %s.ttf: %s.hinting.json\n" % (stem, stem))
        r = run([b3, "sources/config.yaml"], cwd=d)
        fc = os.path.join(d, "fonts", "ttf", stem + ".ttf")
        if not os.path.exists(fc):
            fc_res = "gftools-builder FAILED " + (r.stderr.strip() or r.stdout.strip())[-160:].replace(d + os.sep, "")
        elif step:
            fc_res = "%s | gate %s (hinted by the builder)" % (points(release, fc), check(release, fc))
        else:
            fc_res = "%s | gate %s" % (points(release, fc), gate(release, hfile, fc, fc[:-4] + ".hinted.ttf"))
        print("%-26s fontc    %s" % (stem, fc_res), flush=True)


main()
