#!/usr/bin/env python3
"""Question answered: which upstream_info.md files in google/fonts claim source formats
(their "Buildable" row: .vfb, .sfd, ...) that the recorded repository does not hold?

For each upstream_info.md on <rev> whose "Buildable" row names a source format, reads
METADATA.pb's repository_url and commit, and lists the repository at that commit in the repo
archive -- within the file's own "Source path" when it states one (the
googlefontdirectory-hg monorepo always has one), else the whole repository -- and also every
path the repository's history ever touched in that scope.

  python3 check_info_claims.py <google/fonts clone> <rev> <repo archive> > claims.tsv

Columns: family_dir, claimed, at_commit, in_history, verdict:
  OK          every claimed format is at the commit
  ONLY-EARLIER  a claimed format is missing at the commit but was in the history
  WRONG       a claimed format never was in the repository (in that scope)
  NO-REPO     no repository, or not in the archive
A "Source path" the file states that does not exist at the commit is noted after the verdict.
"""
import os
import re
import subprocess
import sys

GF, REV, ARCHIVE = sys.argv[1:4]
FORMATS = ["vfb", "sfd", "vfj", "vfc", "glyphs", "ufo", "designspace"]
_HISTORY = {}


def git(repo, *args):
    r = subprocess.run(["git", "-c", "core.quotePath=off", "-C", repo, *args], capture_output=True, text=True,
                       errors="replace")
    return r.stdout if r.returncode == 0 else None


def archive_path(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)/(.+?)(?:\.git)?/?$", url.strip())
    if not m:
        return None
    host, path = m.groups()
    parts = path.split("/")
    owner, repo = parts[0], parts[-1]
    for p in (os.path.join(ARCHIVE, owner, repo + ".git"),
              os.path.join(ARCHIVE, host, path + ".git"),
              os.path.join(ARCHIVE, "sr.ht-" + owner.lstrip("~"), repo + ".git")):
        if os.path.isdir(p):
            return p
    od = next((d for d in os.listdir(ARCHIVE) if d.lower() == owner.lower()), None)
    if od:
        rd = next((d for d in os.listdir(os.path.join(ARCHIVE, od))
                   if d.lower() == (repo + ".git").lower()), None)
        if rd:
            return os.path.join(ARCHIVE, od, rd)
    return None


def history(repo):
    if repo not in _HISTORY:
        out = git(repo, "log", "--all", "--format=", "--name-only") or ""
        _HISTORY[repo] = sorted(set(out.split("\n")) - {""})
    return _HISTORY[repo]


def formats_in(paths):
    found = set()
    for p in paths:
        for f in FORMATS:
            if re.search(r"\.%s(/|$)" % f, p, re.I):
                found.add(f)
    return found


def main():
    files = [n for n in (git(GF, "ls-tree", "-r", "--name-only", REV) or "").split("\n")
             if n.endswith("/upstream_info.md")]
    print("\t".join(["family_dir", "claimed", "at_commit", "in_history", "verdict"]))
    for path in sorted(files):
        text = git(GF, "show", "%s:%s" % (REV, path)) or ""
        row = re.search(r"^\|\s*\*\*Buildable\*\*\s*\|(.*)\|\s*$", text, re.M)
        if not row:
            continue
        claimed = {f for f in FORMATS if re.search(r"\b%s\b" % f, row.group(1), re.I)}
        if not claimed:
            continue
        d = os.path.dirname(path)
        meta = git(GF, "show", "%s:%s/METADATA.pb" % (REV, d)) or ""
        url = (re.search(r'repository_url:\s*"([^"]*)"', meta) or [None, ""])[1]
        commit = (re.search(r'commit:\s*"([^"]*)"', meta) or [None, ""])[1]
        repo = archive_path(url) if url else None
        if not repo or not commit:
            print("\t".join([d, ",".join(sorted(claimed)), "", "", "NO-REPO"]))
            continue
        sp = re.search(r"\*\*Source path\*\*\s*\|\s*`?([^`|]*?)`?\s*\|", text)
        stated = sp.group(1).strip().strip("/") if sp else ""
        tree = (git(repo, "ls-tree", "-r", "--name-only", commit) or "").split("\n")
        # In the monorepo the family's directory is <license>/<family>, whatever the file
        # states; elsewhere the whole repository counts.
        scope = d + "/" if "googlefontdirectory-hg" in url else ""
        at = [p for p in tree if p.startswith(scope)]
        hist = [p for p in history(repo) if p.startswith(scope)]
        path_note = ""
        if stated not in ("", ".") and not any(p.startswith(stated + "/") for p in tree):
            path_note = " (stated source path %s/ is not in the repository)" % stated
        f_at, f_hist = formats_in(at), formats_in(hist)
        if claimed <= f_at:
            verdict = "OK"
        elif claimed <= f_hist:
            verdict = "ONLY-EARLIER"
        else:
            verdict = "WRONG"
        print("\t".join([d, ",".join(sorted(claimed)), ",".join(sorted(f_at)),
                         ",".join(sorted(f_hist)), verdict + path_note]))


main()
