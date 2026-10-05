#!/usr/bin/env python3
"""Question answered: if a landed style were re-converted with a CANDIDATE babelfont,
would its build still pass the landing gate against the font Google Fonts ships?

For each named style (families.tsv, repository in ../sfd-reland-repos):
  1. the .sfd committed just before the "Convert to .glyphs with babelfont" commit,
     converted with the candidate and with the reference, recipe.flags_for flags,
     then tools/workarounds.apply_all -- exactly as tools/land.py convert() does
  2. control: the reference's worked .glyphs must equal <convert>:sources/<Style>.glyphs
  3. two builds with gftools-builder3 e851b8b, each in its own scratch copy of the
     committed <convert>:sources/ tree (so the committed config.yaml is used, e.g.
     Allerta's includeSourceFixes):
       ctrl -- the tree as committed
       cand -- the tree with sources/<Style>.glyphs replaced by the candidate's
  4. land.py's gate on each: diffenator3 -J 1 --no-languages --no-match --json
     --succinct <shipped> <built>, then sfd-batch5/tools/table_gate.py --fonts,
     plus an exact best-cmap comparison. CLEAN = 0 blocking rows and no cmap change.
  5. which tables of the built TTF differ between ctrl and cand (ttx, head.modified
     and head.checkSumAdjustment ignored).

Per repository: the committed tree is built ONCE (ctrl); a cand tree is built only when
some style's candidate .glyphs differs from the committed one. Output per style, then a
summary. The builder3 build of a tree builds every style its config lists.

Usage: gate_candidate.py --cand BIN [--ref BIN] --out DIR [Style...]   (default: all
       styles of every repository in ../sfd-reland-repos)
"""
import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys

SFD_RELAND = "/home/fsanches/compartilhado/gf-source-modernization"
sys.path.insert(0, os.path.join(SFD_RELAND, "tools"))
import recipe  # noqa: E402
import workarounds  # noqa: E402
import land  # noqa: E402  (B3, D3, PY, TG, gate(), cmap_difference(), built_name())

REPOS = "/home/fsanches/compartilhado/sfd-reland-repos"
REF = "/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def convert_commit(repo_dir):
    out = run(["git", "-C", repo_dir, "log", "--format=%H", "--grep=^Convert to .glyphs with babelfont"],
              text=True).stdout.split()
    return out[0] if out else None


def extract_sources(repo_dir, commit, dest):
    os.makedirs(dest, exist_ok=True)
    arc = run(["git", "-C", repo_dir, "archive", commit, "sources"]).stdout
    subprocess.run(["tar", "-x", "-C", dest], input=arc, check=True)


def convert(binary, src, out, flags):
    r = run([binary, src, out] + flags, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise SystemExit("conversion failed: %s %s\n%s" % (binary, src, r.stderr[-2000:]))


def build_and_gate(tree, style_glyphs, shipped):
    r = run([land.B3, "sources/config.yaml"], cwd=tree, text=True)
    open(os.path.join(tree, "builder3.log"), "w").write(r.stdout + r.stderr)
    name = land.built_name(style_glyphs)
    ttf = os.path.join(tree, "fonts", "ttf", name)
    if not os.path.exists(ttf):
        return None, None, ["BUILD: %s not produced (exit %d)" % (name, r.returncode)]
    n, blocking = land.gate(shipped, ttf, tree)
    gained, lost = land.cmap_difference(shipped, ttf)
    if gained or lost:
        n += len(gained) + len(lost)
        blocking = blocking + ["CMAP gained %s lost %s" % (["U+%04X" % c for c in gained],
                                                           ["U+%04X" % c for c in lost])]
    return ttf, n, blocking


def ttx_tables(ttf, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    run(["/home/fsanches/compartilhado/gftools/venv/bin/ttx", "-q", "-s", "-o", dest, ttf])
    base = os.path.splitext(dest)[0]
    return {f[len(os.path.basename(base)) + 1:-4]: os.path.join(os.path.dirname(dest), f)
            for f in os.listdir(os.path.dirname(dest))
            if f.startswith(os.path.basename(base) + ".") and f.endswith(".ttx") and f != os.path.basename(dest)}


def strip_volatile(text):
    text = re.sub(r'<modified value="[^"]*"/>', "", text)
    text = re.sub(r'<checkSumAdjustment value="[^"]*"/>', "", text)
    return text


def table_diff(ctrl_ttf, cand_ttf, out_dir):
    a = ttx_tables(ctrl_ttf, os.path.join(out_dir, "ttx-ctrl", "f.ttx"))
    b = ttx_tables(cand_ttf, os.path.join(out_dir, "ttx-cand", "f.ttx"))
    report = []
    for t in sorted(set(a) | set(b)):
        if t not in a or t not in b:
            report.append("table %s only in %s" % (t, "cand" if t in b else "ctrl"))
            continue
        ta = strip_volatile(open(a[t]).read()).splitlines()
        tb = strip_volatile(open(b[t]).read()).splitlines()
        if ta != tb:
            d = [x for x in difflib.unified_diff(ta, tb, "ctrl/" + t, "cand/" + t, lineterm="", n=0)]
            report.append("table %s differs:" % t)
            report += ["    " + x for x in d[:30]]
            if len(d) > 30:
                report.append("    ... (%d more lines)" % (len(d) - 30))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--out", required=True)
    ap.add_argument("styles", nargs="*", help="default: every style of a landed repository")
    a = ap.parse_args()
    rows = recipe.rows()
    landed = [r for r in rows if os.path.isdir(os.path.join(REPOS, r["repo"], ".git"))]
    wanted = [r for r in landed if not a.styles or r["style"] in a.styles]
    repos = []
    for r in wanted:
        if r["repo"] not in repos:
            repos.append(r["repo"])
    verdicts = []
    for repo in repos:
        repo_dir = os.path.join(REPOS, repo)
        c = convert_commit(repo_dir)
        styles = [r for r in wanted if r["repo"] == repo]
        wr = os.path.join(a.out, repo)
        shutil.rmtree(wr, ignore_errors=True)
        os.makedirs(wr)
        print("== %s  (convert %s)" % (repo, c[:7]))
        changed = {}
        for row in styles:
            style = row["style"]
            w = os.path.join(wr, style)
            os.makedirs(w)
            src = os.path.join(w, "landed.sfd")
            open(src, "wb").write(run(["git", "-C", repo_dir, "show", "%s^:%s" % (c, row["source"])]).stdout)
            flags = recipe.flags_for(open(src, encoding="utf-8", errors="replace").read(), row["shipped"])
            committed = os.path.join(w, "committed.glyphs")
            open(committed, "wb").write(run(["git", "-C", repo_dir, "show",
                                             "%s:sources/%s.glyphs" % (c, style)]).stdout)
            worked = {}
            for who, binary in (("ref", a.ref), ("cand", a.cand)):
                g = os.path.join(w, "%s.glyphs" % who)
                convert(binary, src, g, flags)
                worked[who] = os.path.join(w, "%s.worked.glyphs" % who)
                shutil.copy(g, worked[who])
                with open(os.devnull, "w") as devnull:
                    stdout, sys.stdout = sys.stdout, devnull
                    try:
                        workarounds.apply_all(worked[who], src)
                    finally:
                        sys.stdout = stdout
            ref_eq = open(worked["ref"], "rb").read() == open(committed, "rb").read()
            cand_eq = open(worked["cand"], "rb").read() == open(committed, "rb").read()
            if not cand_eq:
                changed[style] = worked["cand"]
                d = list(difflib.unified_diff(open(committed).read().splitlines(),
                                              open(worked["cand"]).read().splitlines(),
                                              "committed/%s.glyphs" % style,
                                              "candidate+workarounds/%s.glyphs" % style, lineterm="", n=1))
                open(os.path.join(w, "glyphs.diff"), "w").write("\n".join(d) + "\n")
            print("   %-28s ref+workarounds %s committed; cand+workarounds %s committed"
                  % (style, "==" if ref_eq else "!=", "==" if cand_eq else "!="))
        trees = {"ctrl": os.path.join(wr, "build-ctrl")}
        if changed:
            trees["cand"] = os.path.join(wr, "build-cand")
        res = {}
        for who, tree in trees.items():
            extract_sources(repo_dir, c, tree)
            for style, g in (changed.items() if who == "cand" else ()):
                shutil.copy(g, os.path.join(tree, "sources", style + ".glyphs"))
            for row in styles:
                ttf, n, blocking = build_and_gate(tree, os.path.join(tree, "sources", row["style"] + ".glyphs"),
                                                  row["shipped"]) if row is styles[0] else \
                    gate_only(tree, os.path.join(tree, "sources", row["style"] + ".glyphs"), row["shipped"])
                res[(who, row["style"])] = (ttf, n, blocking)
                print("   %-4s %-28s %s -> %s blocking%s" % (
                    who, row["style"], os.path.basename(ttf) if ttf else "NONE", n,
                    "" if not blocking else "\n        " + "\n        ".join(blocking)))
        for row in styles:
            style = row["style"]
            ctrl = res[("ctrl", style)]
            cand = res.get(("cand", style), ctrl)
            if style in changed and ctrl[0] and cand[0]:
                same = open(ctrl[0], "rb").read() == open(cand[0], "rb").read()
                print("   %s built TTF ctrl vs cand: %s" % (style, "byte-identical" if same else "differ"))
                if not same:
                    for line in table_diff(ctrl[0], cand[0], os.path.join(wr, style)):
                        print("     " + line)
            verdicts.append((style, repo, "changed" if style in changed else "same .glyphs",
                             ctrl[1], cand[1], "CLEAN" if cand[1] == 0 else "NOT CLEAN"))
        print()
    print("== summary (blocking rows incl. cmap; ctrl = committed sources as landed, "
          "cand = re-landed with the candidate)")
    for v in verdicts:
        print("   %-28s %-20s %-13s ctrl %s  cand %s  %s" % v)
    print("   %d styles, %d CLEAN, %d NOT CLEAN" % (len(verdicts), sum(v[5] == "CLEAN" for v in verdicts),
                                                  sum(v[5] != "CLEAN" for v in verdicts)))


def gate_only(tree, style_glyphs, shipped):
    name = land.built_name(style_glyphs)
    ttf = os.path.join(tree, "fonts", "ttf", name)
    if not os.path.exists(ttf):
        return None, None, ["BUILD: %s not produced" % name]
    n, blocking = land.gate(shipped, ttf, tree)
    gained, lost = land.cmap_difference(shipped, ttf)
    if gained or lost:
        n += len(gained) + len(lost)
        blocking = blocking + ["CMAP gained %s lost %s" % (["U+%04X" % c for c in gained],
                                                           ["U+%04X" % c for c in lost])]
    return ttf, n, blocking


if __name__ == "__main__":
    main()
