#!/usr/bin/env python3
"""Question: does a prepared Glyphs source rebuild the shipped static font? Builds it with
gftools-builder (the config tools/land.py writes, from tools/recipe.py) and gates the build
against the shipped binary exactly as tools/probes/binary_to_source/probe.py does (table gate,
codepoints, functional gate) -- only the conversion step is skipped.

Usage: B3=<gftools-builder> gate_source.py <gf-source-modernization> <work dir with sources/X.glyphs> <shipped.ttf>
With BUILT=<font.ttf> the build step is skipped and that font is gated (a build made by
another compiler: fontc directly, or Python gftools).
"""
import os, subprocess, sys
gsm, work, shipped = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
sys.path.insert(0, os.path.join(gsm, "tools"))
import land, recipe, functional_gate  # noqa: E402

B3 = os.environ.get("B3", land.B3)
stem = [f for f in os.listdir(os.path.join(work, "sources")) if f.endswith(".glyphs")][0][:-7]
if os.environ.get("BUILT"):
    font = os.path.abspath(os.environ["BUILT"])
else:
    with open(os.path.join(work, "sources", "config.yaml"), "w") as fh:
        fh.write("buildVariable: false\nremoveOutlineOverlaps: false\n"
                 + recipe.builder_keys([shipped], False) + "sources:\n  - %s.glyphs\n" % stem)
    b = subprocess.run([B3, "sources/config.yaml"], cwd=work, capture_output=True, text=True)
    ttf_dir = os.path.join(work, "fonts", "ttf")
    built = sorted(os.listdir(ttf_dir)) if os.path.isdir(ttf_dir) else []
    if len(built) != 1:
        print(stem, "BUILD FAILED", built)
        print("\n".join([l for l in (b.stderr + b.stdout).splitlines() if l.strip()][-12:]))
        sys.exit(1)
    font = os.path.join(ttf_dir, built[0])
n, blocking = land.gate(shipped, font, work)
gained, lost = land.cmap_difference(shipped, font)
if gained or lost:
    n += len(gained) + len(lost); blocking.append("CMAP gained %d lost %d" % (len(gained), len(lost)))
fg = functional_gate.run(shipped, font, stem, d3_json=land.d3_json_path(font, work), workdir=work)
bad = functional_gate.failed_checks(fg)
print("%s %s: %d blocking row(s), functional %s" % (stem, "CLEAN" if n == 0 and not bad else "RESIDUAL", n,
      "PASS" if not bad else "FAIL(%s)" % "+".join(bad)))
for d in blocking[:40]:
    print("    " + d[:700])
for l in functional_gate.summary_lines(fg)[1:]:
    print("    functional: " + l)
