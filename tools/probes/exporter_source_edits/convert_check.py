#!/usr/bin/env python3
"""Question answered: once an exporter-reproducing babelfont flag is replaced by a
documented .sfd edit, is every style's converted source what it was with the flag?

For every style of families.tsv and families-next.tsv, converts twice with the same
babelfont binary:

  before  the .sfd with the plans of <rev> (default HEAD), flags from <before recipe.py>
          (the recipe that still passes --fontforge-truncate-anchors,
          --fontforge-legacy-offset-metrics and --fontforge-underline-position=20190317,
          and plans/comicrelief.json's --sfdlib-interpolated-points)
  after   the .sfd with the working tree's plans (the edits), flags from the working
          tree's tools/recipe.py (without those flags)

and compares the two .glyphs files byte for byte. A style whose two conversions differ is
listed with the number of differing lines; there the build has to show the difference is
only in how the same outline is stored (sfdlib_outline_check.py, and the re-land).

Run from the gf-source-modernization checkout; writes only under $TMPDIR/exporter-source-edits/:
  BF=<babelfont binary> /home/fsanches/compartilhado/gftools/venv/bin/python3 \\
      tools/probes/exporter_source_edits/convert_check.py <before recipe.py> [<rev>]
"""
import difflib
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources  # noqa: E402

BF = os.environ.get("BF", "/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-all/"
                    "target-heights/release/babelfont")


def load_recipe(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plan_at(rev, repo):
    r = subprocess.run(["git", "-C", sources.W, "show", "%s:plans/%s.json" % (rev, repo)],
                       capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {"commits": []}


def convert(recipe, plan, row, sfd, keep, out):
    text = open(sfd, encoding="utf-8", errors="replace").read()
    f = plan.get("flags", {}).get(row["style"], {})
    flags = recipe.flags_for(text, row["shipped"], f.get("add", []), f.get("drop", []), keep_direction=keep)
    r = subprocess.run([BF, sfd, out, *flags], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("babelfont failed on %s: %s" % (sfd, r.stderr[-500:]))
    return flags


def main():
    before_recipe = load_recipe(sys.argv[1], "recipe_before")
    rev = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    after_recipe = load_recipe(os.path.join(sources.W, "tools", "recipe.py"), "recipe_after")
    by_repo = {}
    for r in sources.rows():
        by_repo.setdefault(r["repo"], []).append(r)
    out_dir = os.path.join(sources.SCRATCH, "convert")
    os.makedirs(out_dir, exist_ok=True)
    same = differ = 0
    for repo, rows in sorted(by_repo.items()):
        if rows[0]["kind"] == "glyphs":
            continue
        keep = before_recipe.keep_direction([r["shipped"] for r in rows])
        pb, pa = plan_at(rev, repo), sources.plan(repo)
        before = sources.edited(repo, tag="before", plan_override=pb)
        after = sources.edited(repo, tag="after")
        for r in rows:
            st = r["style"]
            gb, ga = os.path.join(out_dir, st + ".before.glyphs"), os.path.join(out_dir, st + ".after.glyphs")
            fb = convert(before_recipe, pb, r, before[st], keep, gb)
            fa = convert(after_recipe, pa, r, after[st], keep, ga)
            tb, ta = open(gb).read(), open(ga).read()
            dropped = [f for f in fb if f not in fa]
            if tb == ta:
                same += 1
                print("SAME    %-28s%s" % (st, "  (flags no longer passed: %s)" % " ".join(dropped) if dropped else ""))
            else:
                differ += 1
                n = sum(1 for l in difflib.unified_diff(tb.splitlines(), ta.splitlines(), n=0)
                        if l[:1] in "+-" and not l.startswith(("+++", "---")))
                print("DIFFER  %-28s %d line(s)  (flags no longer passed: %s)" % (st, n, " ".join(dropped) or "-"))
    print("%d styles convert identically, %d differ" % (same, differ))


if __name__ == "__main__":
    main()
