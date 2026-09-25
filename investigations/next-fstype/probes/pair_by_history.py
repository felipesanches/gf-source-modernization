#!/usr/bin/env python3
"""pair_by_history.py -- prototype of a 4th pairing rule for tools/pair_next.py.

Question answered: a shipped font whose CURRENT PostScript name matches no .sfd
FontName (pair_next.py logs it UNPAIRED) -- did the same file carry another
PostScript name earlier in its history, one that DOES match an .sfd? If so, which
google/fonts commit renamed it, and is the binary still the same FontForge export
(same FFTM stamp) across the rename?

Rule 4 (applies only where rules 1-3 left a font UNPAIRED, so it cannot change any
existing pair): collect the name ID 6 of every google/fonts revision of the file
(`git log --follow`, oldest first) plus the binary the base commit holds at the same
path (googlefontdirectory-hg keeps the exported .ttf next to src/); if exactly one
historic name matches .sfd FontNames, pair it by rules 1-2 (-TTF variant preferred)
and log the renaming commit. Anything else stays UNPAIRED.

Run over the rows logs/pair_next.log reports UNPAIRED:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY investigations/next-fstype/probes/pair_by_history.py \
      > investigations/next-fstype/runs/pair_by_history.txt
"""
import io
import os
import re
import subprocess

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/sfd-reland"
GF = "/home/fsanches/compartilhado/google/fonts"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
HG = "googlefonts/googlefontdirectory-hg"


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, check=True).stdout


def unpaired():
    out = []
    for line in open(os.path.join(W, "logs/pair_next.log")):
        m = re.match(r"^(\w+)/(\S+): UNPAIRED", line)
        if m:
            out.append(m.groups())
    return out


def base_of(fam):
    """The (repo, commit, prefix) pair_next.py used for this family: read from
    scope/census.tsv exactly as pair_next.batch() does."""
    import csv
    for r in csv.DictReader(open(os.path.join(W, "scope", "census.tsv")), delimiter="\t"):
        lic, f = r["gf_path"].split("/")
        if f == fam:
            mirror = os.path.join(ARC, r["repo"] + ".git")
            commit = git(mirror, "rev-parse", r["commit_used"]).decode().strip()
            return lic, mirror, commit, ("%s/%s/" % (lic, fam) if r["repo"] == HG else "")
    raise SystemExit("no census row for %s" % fam)


def facts(blob):
    f = TTFont(io.BytesIO(blob), lazy=True)
    ff = f["FFTM"].FFTimeStamp if "FFTM" in f else None
    return str(f["name"].getDebugName(6)), ff


def main():
    for fam, style in unpaired():
        lic, mirror, commit, prefix = base_of(fam)
        path = "%s/%s/%s.ttf" % (lic, fam, style)
        print("=" * 80)
        print("%s/%s" % (fam, style))
        history = []
        for line in reversed(git(GF, "log", "--follow", "--format=%h %ad %s", "--date=short",
                                 "--", path).decode().splitlines()):
            h = line.split()[0]
            try:
                ps, ff = facts(git(GF, "show", "%s:%s" % (h, path)))
            except subprocess.CalledProcessError:
                continue
            history.append(("google/fonts " + line[:55], ps, ff))
        try:
            ps, ff = facts(git(mirror, "show", "%s:%s%s.ttf" % (commit, prefix, style)))
            history.append(("%s %s binary" % (os.path.basename(mirror), commit[:9]), ps, ff))
        except subprocess.CalledProcessError:
            pass
        for where, ps, ff in history:
            print("  %-75s ps=%-32s FFTM=%s" % (where, ps, ff))
        paths = [p for p in git(mirror, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
                 if p.startswith(prefix) and p.lower().endswith(".sfd")]
        names = {}
        for p in paths:
            text = git(mirror, "show", "%s:%s" % (commit, p)).decode("utf-8", "replace")
            m = re.search(r"^FontName: *(\S+)", text, re.M)
            if m and re.search(r"^StartChar:", text, re.M):
                names.setdefault(m.group(1), []).append(p[len(prefix):])
        hist_names = sorted({ps for _, ps, _ in history} & set(names))
        stamps = {ff for _, _, ff in history}
        if len(hist_names) == 1:
            cands = names[hist_names[0]]
            ttf = [p for p in cands if re.search(r"-TTF\.sfd$", p, re.I)]
            pick = ttf if ttf else cands
            if len(pick) == 1:
                print("  RULE 4 PAIR: %s <- historic PostScript name %s; FFTM stamps across the "
                      "history: %s" % (pick[0], hist_names[0],
                                       "one (same FontForge export)" if len(stamps) == 1 else sorted(stamps)))
                continue
        print("  still UNPAIRED (historic names matching an .sfd: %s)" % (hist_names or "none"))


if __name__ == "__main__":
    main()
