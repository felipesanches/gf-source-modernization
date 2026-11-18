#!/usr/bin/env python3
"""Question answered: do Manjari's upstream UFOs (gitlab.com/smc/fonts/manjari at the commit
google/fonts pins), built as they are by gftools-builder (fontc) with google/fonts' override
config, match the fonts google/fonts ships, under land.py's table and functional gates?

Usage: B3=<gftools-builder> ufo_route.py <checkout at the pinned commit> <google/fonts>/ofl/manjari
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import land  # noqa: E402
import functional_gate  # noqa: E402

repo, family = map(os.path.abspath, sys.argv[1:3])
B3 = os.environ.get("B3", land.B3)
shutil.copy(os.path.join(family, "config.yaml"), os.path.join(repo, "config.override.yaml"))
if not os.environ.get("NOBUILD"):
    b = subprocess.run([B3, "config.override.yaml"], cwd=repo, capture_output=True, text=True)
    print("builder exit", b.returncode)
    if b.returncode:
        print("\n".join((b.stderr + b.stdout).splitlines()[-8:]))
for style in ("Thin", "Regular", "Bold"):
    shipped = os.path.join(family, "Manjari-%s.ttf" % style)
    # the builder writes ../fonts relative to the config, which sits at the checkout root
    built = os.path.join(os.path.dirname(repo), "fonts", "ttf", "Manjari-%s.ttf" % style)
    if not os.path.exists(built):
        print(style, "NOT BUILT", sorted(os.listdir(os.path.dirname(built))) if os.path.isdir(os.path.dirname(built)) else "")
        continue
    work = os.path.join(repo, "gate-" + style)
    os.makedirs(work, exist_ok=True)
    n, rows = land.gate(shipped, built, work)
    gained, lost = land.cmap_difference(shipped, built)
    fg = functional_gate.run(shipped, built, "Manjari-" + style, d3_json=land.d3_json_path(built, work), workdir=work)
    print("Manjari-%s: %d blocking row(s), cmap gained %d lost %d, functional %s"
          % (style, n, len(gained), len(lost), "+".join(functional_gate.failed_checks(fg)) or "PASS"))
    for r in rows[:15]:
        print("    " + r[:300])
    for l in functional_gate.summary_lines(fg)[1:]:
        print("    functional: " + l[:300])
