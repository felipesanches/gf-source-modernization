#!/usr/bin/env python3
"""Pair every shipped style of the next SFD batch with the .sfd it is converted from.

Question answered: for each font google/fonts ships for a family in the batch, WHICH
.sfd in its recorded upstream holds that font -- decided from the files' contents, not
their names, and logged with the rule used, so a later finding can be traced to its pair.

Rule, per shipped font:
  1. candidates: .sfd files (in the family's directory, for the googlefontdirectory-hg
     monorepo) whose `FontName:` equals the shipped font's PostScript name (name ID 6)
     and which declare glyphs (StartChar > 0);
  2. the `-TTF` variant when there is one (it is the quadratic outline FontForge
     exported), else the only candidate; more than one left -> AMBIGUOUS, not paired;
  3. no name match, but the family ships ONE font and has ONE .sfd that declares glyphs:
     that pair, logged with both names (a name edited after export, or a typo).
No candidate -> UNPAIRED. Both are reported, never guessed.

Input: the batch is scope/census.tsv's static, FFTM-shipping families with .sfd sources
that no earlier list holds (or the families given on the command line).
Output: families-next.tsv (families.tsv's columns) on stdout; the log on stderr.

Usage: tools/pair_next.py [family ...] > families-next.tsv 2> logs/pair_next.log
"""
import csv
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GF = "/home/fsanches/compartilhado/google/fonts"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
HG = "googlefonts/googlefontdirectory-hg"


def git(mirror, *a):
    return subprocess.run(["git", "-C", mirror, *a], capture_output=True, check=True).stdout


def sfd_facts(mirror, commit, path):
    text = git(mirror, "show", "%s:%s" % (commit, path)).decode("utf-8", "replace")
    m = re.search(r"^FontName: *(\S+)", text, re.M)
    return (m.group(1) if m else None), len(re.findall(r"^StartChar:", text, re.M))


def batch(argv):
    rows = list(csv.DictReader(open(os.path.join(W, "scope", "census.tsv")), delimiter="\t"))
    if argv:
        return [r for r in rows if r["gf_path"].split("/")[1] in argv]
    return [r for r in rows if r["class"] in ("sfd", "sfd+vfb") and not r["already"]
            and int(r["fftm"]) > 0 and "V" not in r["shipped"]]


def main():
    out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    out.writerow(["repo", "family", "lic", "kind", "base", "commit", "style", "source", "shipped"])
    for r in batch(sys.argv[1:]):
        lic, fam = r["gf_path"].split("/")
        mirror = os.path.join(ARC, r["repo"] + ".git")
        commit = git(mirror, "rev-parse", r["commit_used"]).decode().strip()
        prefix = "%s/%s/" % (lic, fam) if r["repo"] == HG else ""
        paths = [p for p in git(mirror, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
                 if p.startswith(prefix) and p.lower().endswith(".sfd")]
        facts = {p: sfd_facts(mirror, commit, p) for p in paths}
        kind = "hg" if r["repo"] == HG else "upstream"
        for f in sorted(os.listdir(os.path.join(GF, lic, fam))):
            if not f.endswith((".ttf", ".otf")):
                continue
            shipped = os.path.join(GF, lic, fam, f)
            ps = str(TTFont(shipped, lazy=True)["name"].getDebugName(6))
            cands = [p for p, (name, n) in facts.items() if name == ps and n > 0]
            ttf = [p for p in cands if re.search(r"-TTF\.sfd$", p, re.I)]
            pick = ttf if ttf else cands
            sole = [p for p, (name, n) in facts.items() if n > 0]
            n_shipped = sum(x.endswith((".ttf", ".otf")) for x in os.listdir(os.path.join(GF, lic, fam)))
            if not cands and len(sole) == 1 and n_shipped == 1:
                pick = sole
                ttf = None
            style = os.path.splitext(f)[0]
            if len(pick) == 1:
                rule = ("sole .sfd and sole font, FontName %s differs" % facts[pick[0]][0]
                        if ttf is None else
                        "FontName match, -TTF variant" if ttf else "FontName match, only candidate")
                print("%s/%s: %s <- %s (%s; %d candidate(s))" % (fam, style, pick[0], ps, rule,
                                                                  len(cands)), file=sys.stderr)
                out.writerow([fam, fam, lic, kind, r["repo"], commit, style,
                              pick[0][len(prefix):], shipped])
            else:
                state = "AMBIGUOUS" if pick else "UNPAIRED"
                print("%s/%s: %s -- PostScript name %s; .sfd FontNames: %s" % (
                    fam, style, state, ps,
                    ", ".join("%s=%s(%d)" % (p[len(prefix):], n, g) for p, (n, g) in sorted(facts.items()))),
                    file=sys.stderr)


if __name__ == "__main__":
    main()
