#!/usr/bin/env python3
"""Question answered: built with fontc, how close do Comic Relief's outlines come to the
release's with (a) babelfont's --sfdlib-interpolated-points filter (the 2026-10-02 state),
(b) the `sfdlibinterpolated` .sfd edit with --round-coordinates, (c) the edit without it
(plans/comicrelief.json as committed)?

Each variant converts both styles (sources.py + the recipe's flags), builds them with
gftools-builder from the landed config, and compares every glyph's glyf outline with the
release's: the points of each contour as a cycle in either direction (the release's run
the other way), after dropping each on-curve point exactly midway between two off-curve
neighbours on both sides (write-fonts drops those, ufo2ft keeps them: storage, not
shape). Prints, per variant and style, how many simple glyphs match and which differ.

  BF=<babelfont> B3=<gftools-builder> $PY tools/probes/exporter_source_edits/comic_build_check.py \\
      <recipe.py with the filters> [<plans rev before the edits>]
"""
import os
import shutil
import subprocess
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import convert_check as cc  # noqa: E402
import sources  # noqa: E402

B3 = os.environ.get("B3", "/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder")
CONFIG = ("buildVariable: false\nremoveOutlineOverlaps: false\nnoProductionNames: true\n"
          "reverseOutlineDirection: false\nsources:\n  - ComicRelief-Regular.glyphs\n  - ComicRelief-Bold.glyphs\n")


def contours(font, g):
    gl = font["glyf"][g]
    if gl.isComposite():
        return None
    c, ends, fl = gl.getCoordinates(font["glyf"])
    out, s = [], 0
    for e in ends:
        out.append([(c[i][0], c[i][1], fl[i] & 1) for i in range(s, e + 1)])
        s = e + 1
    return out


def drop_implied(c):
    n = len(c)
    return [p for i, p in enumerate(c)
            if not (p[2] and not c[i - 1][2] and not c[(i + 1) % n][2]
                    and 2 * p[0] == c[i - 1][0] + c[(i + 1) % n][0]
                    and 2 * p[1] == c[i - 1][1] + c[(i + 1) % n][1])]


def same_cycle(a, b):
    if len(a) != len(b):
        return False
    return any(s[k:] + s[:k] == a for s in (b, b[::-1]) for k in range(len(s) or 1))


def compare(built, release):
    f, r = TTFont(built), TTFont(release)
    ok, bad = 0, []
    for g in f.getGlyphOrder():
        if g not in r["glyf"]:
            continue
        a, b = contours(f, g), contours(r, g)
        if a is None or b is None:
            continue
        if len(a) == len(b) and all(same_cycle(drop_implied(x), drop_implied(y)) for x, y in zip(a, b)):
            ok += 1
        else:
            bad.append(g)
    return ok, bad


def variant(name, recipe, plan, srcs, extra_drop, rows, keep):
    d = os.path.join(sources.SCRATCH, "comic-build", name)
    assert os.path.realpath(d).startswith(os.path.realpath(sources.SCRATCH) + os.sep)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, "sources"))
    open(os.path.join(d, "sources", "config.yaml"), "w").write(CONFIG)
    for r in rows:
        p = dict(plan)
        fl = {k: dict(v) for k, v in plan.get("flags", {}).items()}
        st = fl.setdefault(r["style"], {})
        st["drop"] = [x for x in st.get("drop", []) if x not in extra_drop.get("keep", [])] + extra_drop.get("drop", [])
        p["flags"] = fl
        cc.convert(recipe, p, r, srcs[r["style"]], keep, os.path.join(d, "sources", r["style"] + ".glyphs"))
    b = subprocess.run([B3, "sources/config.yaml"], cwd=d, capture_output=True, text=True)
    if b.returncode:
        raise SystemExit("build failed for %s: %s" % (name, b.stderr[-400:]))
    for r in rows:
        ok, bad = compare(os.path.join(d, "fonts", "ttf", r["style"] + ".ttf"), r["shipped"])
        print("%-34s %-20s %3d glyph outlines equal the release's, %2d differ: %s"
              % (name, r["style"], ok, len(bad), " ".join(bad)))


def main():
    before_recipe = cc.load_recipe(sys.argv[1], "recipe_before")
    rev = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    after_recipe = cc.load_recipe(os.path.join(sources.W, "tools", "recipe.py"), "recipe_after")
    rows = [r for r in sources.rows() if r["repo"] == "comicrelief"]
    keep = after_recipe.keep_direction([r["shipped"] for r in rows])
    pb, pa = cc.plan_at(rev, "comicrelief"), sources.plan("comicrelief")
    before = sources.edited("comicrelief", tag="comic-before", plan_override=pb)
    after = sources.edited("comicrelief", tag="comic-after")
    variant("a-filter", before_recipe, pb, before, {}, rows, keep)
    variant("b-edit+round-coordinates", after_recipe, pa, after, {"keep": ["--round-coordinates"]}, rows, keep)
    variant("c-edit-as-planned", after_recipe, pa, after, {}, rows, keep)


if __name__ == "__main__":
    main()
