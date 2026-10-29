#!/usr/bin/env python3
"""Pair every shipped style of the VFB batch with the .vfb it is converted from.

Question answered: for each font google/fonts ships for a family whose source of record
is a FontLab Studio 5 .vfb, WHICH .vfb in its recorded upstream holds that font --
decided from the files' contents, not their names, and logged with the rule used, so a
later finding can be traced to its pair (tools/pair_next.py does the same for .sfd).

Rule, per shipped font:
  1. candidates: .vfb files (in the family's directory, for the googlefontdirectory-hg
     monorepo) whose PostScript font name (VFB entry 1026, `font_name`) equals the
     shipped font's PostScript name (name ID 6) and which hold glyphs;
  2. the `-TTF` variant when there is one (FontLab's TrueType-flavoured copy, the
     quadratic outlines the release was generated from), else the only candidate;
     more than one left -> AMBIGUOUS, not paired;
  3. no name match, but the family ships ONE font and has ONE .vfb that holds glyphs:
     that pair, logged with both names (a name edited after export, or a typo).
No candidate -> UNPAIRED. Both are reported, never guessed. A .vfb vfbLib cannot
parse is logged as such and is not a candidate.

Input: the batch is scope/census.tsv's families of class `vfb`, plus the `sfd+vfb`
families whose releases carry no FFTM table (not exported by FontForge, so the .vfb is
the likelier master), static only, that no earlier list holds (or the families given on
the command line).
Output: families-vfb.tsv (families.tsv's columns) on stdout; the log on stderr.
  kind: hg for the monorepo; fork for a librefonts mirror (the landing is a branch on a
  googlefonts fork of it, as families.tsv's abrilfatface and corben); upstream otherwise.

Usage (vfbLib lives in the vfblib-py-venv interpreter):
  /home/fsanches/compartilhado/vfblib-py-venv/bin/python3 tools/pair_vfb.py [family ...] \
      > families-vfb.tsv 2> logs/pair_vfb.log
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GF = "/home/fsanches/compartilhado/google/fonts"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
HG = "googlefonts/googlefontdirectory-hg"
SCRATCH = os.environ.get("TMPDIR", "/home/fsanches/compartilhado/tmp")


def git(mirror, *a):
    return subprocess.run(["git", "-C", mirror, *a], capture_output=True, check=True).stdout


def vfb_facts(mirror, commit, path, tmpdir):
    """-> (PostScript font name or None, number of glyph entries, error or '')."""
    from vfbLib.enum import F
    from vfbLib.vfb.vfb import Vfb
    blob = git(mirror, "show", "%s:%s" % (commit, path))
    p = os.path.join(tmpdir, re.sub(r"[^A-Za-z0-9._-]", "_", path))
    with open(p, "wb") as fh:
        fh.write(blob)
    try:
        vfb = Vfb(p, timing=False)
    except Exception as ex:
        return None, 0, "read: %s: %s" % (type(ex).__name__, ex)
    name, glyphs, err = None, 0, ""
    for e in vfb.entries:
        try:
            e.decompile()
        except Exception as ex:
            err = err or "entry %s (%s): %s" % (e.id, e.key, type(ex).__name__)
            continue
        if e.id == F.font_name and isinstance(e.data, str) and name is None:
            name = e.data
        elif e.key == "Glyph":
            glyphs += 1
    return name, glyphs, err


def batch(argv):
    rows = list(csv.DictReader(open(os.path.join(W, "scope", "census.tsv")), delimiter="\t"))
    if argv:
        return [r for r in rows if r["gf_path"].split("/")[1] in argv]
    return [r for r in rows if not r["already"] and "V" not in r["shipped"]
            and (r["class"] == "vfb" or (r["class"] == "sfd+vfb" and r["fftm"] == "0"))]


def family_prefix(mirror, commit, lic, fam):
    """The monorepo path of the family: <lic>/<fam>/ or, before the licence split, <fam>/."""
    for p in ("%s/%s" % (lic, fam), fam):
        if git(mirror, "ls-tree", "--name-only", commit, p).strip():
            return p + "/"
    return "%s/%s/" % (lic, fam)


def main():
    out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    out.writerow(["repo", "family", "lic", "kind", "base", "commit", "style", "source", "shipped"])
    tmpdir = tempfile.mkdtemp(prefix="pair_vfb-", dir=SCRATCH)
    for r in batch(sys.argv[1:]):
        lic, fam = r["gf_path"].split("/")
        mirror = os.path.join(ARC, r["repo"] + ".git")
        commit = git(mirror, "rev-parse", r["commit_used"]).decode().strip()
        prefix = family_prefix(mirror, commit, lic, fam) if r["repo"] == HG else ""
        paths = [p for p in git(mirror, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
                 if p.startswith(prefix) and p.lower().endswith(".vfb")]
        facts = {}
        for p in paths:
            name, n, err = vfb_facts(mirror, commit, p, tmpdir)
            facts[p] = (name, n)
            if err:
                print("%s: %s -- vfbLib: %s" % (fam, p[len(prefix):], err), file=sys.stderr)
        owner = r["repo"].split("/")[0]
        kind = "hg" if r["repo"] == HG else "fork" if owner == "librefonts" else "upstream"
        fonts = sorted(f for f in os.listdir(os.path.join(GF, lic, fam)) if f.endswith((".ttf", ".otf")))
        for f in fonts:
            shipped = os.path.join(GF, lic, fam, f)
            ps = str(TTFont(shipped, lazy=True)["name"].getDebugName(6))
            cands = [p for p, (name, n) in facts.items() if name == ps and n > 0]
            ttf = [p for p in cands if re.search(r"-TTF\.vfb$", p, re.I)]
            pick = ttf if ttf else cands
            sole = [p for p, (name, n) in facts.items() if n > 0]
            if not cands and len(sole) == 1 and len(fonts) == 1:
                pick = sole
                ttf = None
            style = os.path.splitext(f)[0]
            if len(pick) == 1:
                rule = ("sole .vfb and sole font, font_name %s differs" % facts[pick[0]][0]
                        if ttf is None else
                        "font_name match, -TTF variant" if ttf else "font_name match, only candidate")
                print("%s/%s: %s <- %s (%s; %d candidate(s))" % (fam, style, pick[0], ps, rule,
                                                                  len(cands)), file=sys.stderr)
                out.writerow([fam, fam, lic, kind, r["repo"], commit, style,
                              pick[0][len(prefix):], shipped])
            else:
                state = "AMBIGUOUS" if pick else "UNPAIRED"
                print("%s/%s: %s -- PostScript name %s; .vfb font_names: %s" % (
                    fam, style, state, ps,
                    ", ".join("%s=%s(%d)" % (p[len(prefix):], n, g) for p, (n, g) in sorted(facts.items()))),
                    file=sys.stderr)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
