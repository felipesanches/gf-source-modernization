#!/usr/bin/env python3
"""Question answered: across EVERY style of both batches (families.tsv, 42 styles, and
families-next.tsv, 107), which converted x-height / cap height does the proposed fix
to babelfont #91 change -- looking a glyph up by its alternate codepoints too, as
FontForge's SFFindGID does -- and does each change move the value onto the release's
or away from it?

Conversion only (no compile): each style's UNMODIFIED source (from the repo archive,
as the table's base/commit/source say) is converted by the two babelfont builds with
the recipe's own flags (tools/recipe.py flags_for, the only implementation of the
recipe), and the master's x-height / cap height metricValues are read from the
.glyphs. The release's OS/2 sxHeight / sCapHeight are the reference; a release with
OS/2 version < 2 carries neither and is marked so.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 altuni_regression.py <BF-before> <BF-after> \
      > ../runs/altuni_regression.txt
"""
import os
import subprocess
import sys

import openstep_plist
from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/gf-source-modernization"
sys.path.insert(0, os.path.join(W, "tools"))
import recipe  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
SCR = "/home/fsanches/compartilhado/sfd-reland-scratch/heights/altuni-regression"


def rows(tsv):
    with open(tsv) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]


def heights(glyphs_path):
    d = openstep_plist.load(open(glyphs_path, encoding="utf-8"), use_numbers=True)
    types = [m.get("type") for m in d.get("metrics", [])]
    out = []
    for m in d["fontMaster"]:
        vals = m.get("metricValues", [])
        get = lambda t: vals[types.index(t)].get("pos", 0) if t in types and types.index(t) < len(vals) else None
        out.append((get("x-height"), get("cap height")))
    return out


def main():
    bf0, bf1 = sys.argv[1], sys.argv[2]
    os.makedirs(SCR, exist_ok=True)
    changed = same = failed = 0
    for tsv in ("families.tsv", "families-next.tsv"):
        for r in rows(os.path.join(W, tsv)):
            path = "%s/%s/%s" % (r["lic"], r["family"], r["source"]) if r["kind"] == "hg" else r["source"]
            p = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, r["base"]), "show", "%s:%s" % (r["commit"], path)],
                               capture_output=True)
            if p.returncode:
                print("%-30s %-18s NO-SOURCE" % (r["style"], tsv))
                continue
            sfd = os.path.join(SCR, r["style"] + ".sfd")
            open(sfd, "wb").write(p.stdout)
            flags = recipe.flags_for(p.stdout.decode("utf-8", "replace"), r["shipped"])
            res = []
            for tag, bf in (("0", bf0), ("1", bf1)):
                out = os.path.join(SCR, "%s.%s.glyphs" % (r["style"], tag))
                q = subprocess.run([bf, sfd, out] + flags, capture_output=True)
                res.append(heights(out) if q.returncode == 0 and os.path.exists(out) else None)
            if None in res:
                failed += 1
                print("%-30s %-18s CONVERT-FAILED" % (r["style"], tsv))
                continue
            o2 = TTFont(r["shipped"])["OS/2"]
            rel = (o2.sxHeight, o2.sCapHeight) if o2.version >= 2 else None
            a, b = res[0][0], res[1][0]
            if a == b:
                same += 1
                print("%-30s %-18s same %s release %s" % (r["style"], tsv, a, rel))
            else:
                changed += 1
                verdict = ("ONTO-RELEASE" if rel is not None and tuple(b) == tuple(rel) else
                           "AWAY-FROM-RELEASE" if rel is not None and tuple(a) == tuple(rel) else
                           "neither-matches")
                print("%-30s %-18s CHANGED %s -> %s release %s  %s" % (r["style"], tsv, a, b, rel, verdict))
    print("\n%d unchanged, %d changed, %d failed" % (same, changed, failed))


if __name__ == "__main__":
    main()
