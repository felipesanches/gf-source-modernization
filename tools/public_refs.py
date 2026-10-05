#!/usr/bin/env python3
"""Question answered: is everything a landed font repository refers to publicly accessible?

Rule (Felipe, 2026-10-05): every commit, file and URL a converted font repository refers to
must be public before the repository is pushed.

Checks, on the commits this programme wrote (messages ending "Assisted by an AI agent") and
on every tracked text file:
  1. no workstation path (/home/..., /tmp/..., ~/compartilhado);
  2. every hexadecimal commit id (7-40 digits, not one of the repository's own commits)
     is a commit on the published branch of a public repository: babelfont-rs main,
     gftools-rust main, google/fonts main, googlefontdirectory-hg master, this evidence
     repository's published main, or the family's own upstream (its repo-archive mirror);
  3. every file this evidence repository is cited for (plans/<x>.json, tools/<x>, logs/<x>,
     investigations/<x>, templates/<x>) exists at the cited revision;
  4. every github.com URL in those commits and in the README above "## Original README"
     answers HTTP 200 (the designer's own text below that heading is not ours to change).

Local mirrors are used for 2 and 3; fetch them first (refresh(), or --fetch on the command
line) -- push.sh does it once per run.

Usage: public_refs.py [--fetch] <landed repo dir>...      exit 1 if anything fails
"""
import os
import re
import subprocess
import sys

C = "/home/fsanches/compartilhado"
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_URL = "https://github.com/felipesanches/gf-source-modernization"
EVIDENCE_REMOTE = os.environ.get("EVIDENCE_REMOTE", EVIDENCE_URL)   # a local path, to check before publishing
# (local repository, remote, published branch)
MIRRORS = [
    (C + "/babelfont-rs-worktrees/upstream-main", "upstream", "main"),
    (C + "/gftools-rust", "origin", "main"),
    (C + "/google/fonts", "upstream", "main"),
    (C + "/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git", "origin", "master"),
]
ARCHIVE = C + "/upstream_repos/repo_archive"
LOCAL = re.compile(r"(/home/\w+|/tmp/|~/compartilhado)")
HEX = re.compile(r"(?<![0-9A-Za-z/#.-])([0-9a-f]{7,40})(?![0-9A-Za-z])")
CITED = re.compile(r"gf-source-modernization at ([0-9a-f]{7,40})")
EVFILE = re.compile(r"\b((?:plans|tools|logs|investigations|templates)/[\w./-]*\w)")
URL = re.compile(r"https://github\.com/[^\s'\"`)<>]+")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def refresh():
    for repo, remote, branch in MIRRORS:
        if repo.endswith(".git"):
            git(repo, "remote", "update")
        else:
            git(repo, "fetch", "-q", remote, branch)
    git(W, "fetch", "-q", EVIDENCE_REMOTE, "main")
    git(W, "update-ref", "refs/published/main", "FETCH_HEAD")


def published(repo, remote, branch, sha):
    ref = branch if repo.endswith(".git") else "%s/%s" % (remote, branch)
    full = git(repo, "rev-parse", "--verify", "-q", sha + "^{commit}").stdout.strip()
    return bool(full) and git(repo, "merge-base", "--is-ancestor", full, ref).returncode == 0


def upstream_mirror(d):
    """The repo-archive mirror of the family's upstream, if its history came from one."""
    url = git(d, "log", "--reverse", "--format=%B").stdout
    m = re.search(r"https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?[\s,.)]", url)
    if m:
        p = "%s/%s/%s.git" % (ARCHIVE, m.group(1), m.group(2))
        if os.path.isdir(p):
            return [(p, "origin", "HEAD")]
    return []


def ours(d):
    out = git(d, "log", "--format=%H%x00%B%x01").stdout
    for rec in out.split("\x01"):
        if "\x00" in rec:
            sha, body = rec.strip().split("\x00", 1)
            if "Assisted by an AI agent" in body:
                yield sha, body


def check(d, urls=True):
    """The problems found in one landed repository (empty list = all public)."""
    problems = []
    own = set(git(d, "log", "--format=%H").stdout.split())
    mirrors = MIRRORS + [(W, "refs/published", "main")] + upstream_mirror(d)
    texts = [("commit %s" % sha[:7], body) for sha, body in ours(d)]
    for f in git(d, "ls-files").stdout.splitlines():
        p = os.path.join(d, f)
        if f.endswith((".glyphs", ".ttf", ".otf", ".png", ".pdf", ".zip")) or not os.path.isfile(p):
            continue
        try:
            t = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if LOCAL.search(t):
            problems.append("%s: workstation path %s" % (f, LOCAL.search(t).group(0)))
        if f == "README.md":
            texts.append(("README.md", t.split("## Original README")[0]))
    for where, text in texts:
        if LOCAL.search(text):
            problems.append("%s: workstation path %s" % (where, LOCAL.search(text).group(0)))
        for h in set(HEX.findall(text)):
            if not (re.search("[a-f]", h) and re.search("[0-9]", h)):
                continue
            if any(o.startswith(h) for o in own):
                continue
            if not any(published(r, rem, b, h) if rem != "refs/published" else
                       git(W, "merge-base", "--is-ancestor", h, "refs/published/main").returncode == 0
                       for r, rem, b in mirrors):
                problems.append("%s: %s is not a commit on any published branch we know" % (where, h))
        for rev in set(CITED.findall(text)):
            for f in set(EVFILE.findall(text)):
                if git(W, "cat-file", "-e", "%s:%s" % (rev, f.rstrip("/"))).returncode != 0:
                    problems.append("%s: %s is not in %s at %s" % (where, f, EVIDENCE_URL, rev))
        if urls:
            for u in set(URL.findall(text)):
                u = u.rstrip(".,;:")
                if "{" in u or "|" in u:
                    continue
                code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-w", "%{http_code}", "-I", u],
                                      capture_output=True, text=True).stdout
                if code != "200":
                    problems.append("%s: %s answers %s" % (where, u, code or "nothing"))
    return problems


def main():
    args = sys.argv[1:]
    if "--fetch" in args:
        args.remove("--fetch")
        refresh()
    bad = 0
    for d in args:
        problems = check(d)
        print("%-24s %s" % (os.path.basename(d.rstrip("/")), "PUBLIC" if not problems else "NOT PUBLIC"))
        for p in problems:
            print("    " + p)
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
