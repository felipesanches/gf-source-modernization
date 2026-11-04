#!/usr/bin/env python3
"""Question answered: does every METADATA.pb source block that points at one of our
googlefonts repositories record a commit on that repository's default branch, as GitHub
publishes it? (Standing rule, Felipe 2026-11-04: never a commit of an open pull request.)

Scans google/fonts main and, for every prepared branch, the families its own commits
touch (upstream/main..branch). "Our" repositories: landed.tsv plus the
googlefonts-workflow-fix list. Each repository's default branch is read with
`git ls-remote --symref` and fetched (commits only) into a bare cache under
$TMPDIR/metadata-audit, where the recorded commit must be an ancestor of it.

Usage: audit_metadata_branches.py <google/fonts git dir> <main ref> [<branch>...]
Prints one aligned row per source block; exit 1 if any row is not OK.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.environ.get("TMPDIR", "/home/fsanches/compartilhado/tmp"), "metadata-audit")
WF = "/home/fsanches/compartilhado/googlefonts-workflow-fix/repos.tsv"


def git(d, *a, check=True):
    r = subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit("FATAL git %s: %s" % (" ".join(a), r.stderr))
    return r


def ours():
    names = {l.split("\t")[0] for l in open(os.path.join(HERE, "..", "landed.tsv")) if l.strip()}
    if os.path.exists(WF):
        names |= {l.split("\t")[0] for l in open(WF) if l.strip()}
    return names


SRC = re.compile(r'repository_url: "https://github\.com/googlefonts/([\w.-]+?)(?:\.git)?"')


def blocks(gf, ref, paths):
    for p in paths:
        text = git(gf, "show", "%s:%s" % (ref, p), check=False).stdout
        m = SRC.search(text)
        if not m:
            continue
        commit = re.search(r'^\s*commit: "([0-9a-f]+)"', text, re.M)
        branch = re.search(r'^\s*branch: "([^"]+)"', text, re.M)
        yield p.rsplit("/", 1)[0], m.group(1), commit.group(1) if commit else "", branch.group(1) if branch else ""


DEFAULT = {}


def verdict(repo, commit, branch):
    url = "https://github.com/googlefonts/%s.git" % repo
    if repo not in DEFAULT:
        for _ in range(3):        # a network failure is retried, never read as "not pushed"
            r = subprocess.run(["git", "ls-remote", "--symref", url, "HEAD"], capture_output=True, text=True)
            if r.returncode == 0:
                break
        if r.returncode:
            return "UNVERIFIED (ls-remote failed 3 times)", None
        m = re.search(r"^ref: refs/heads/(\S+)\tHEAD$", r.stdout, re.M)
        DEFAULT[repo] = m.group(1) if m else None
        if m:
            bare = os.path.join(CACHE, repo + ".git")
            if not os.path.isdir(bare):
                subprocess.run(["git", "init", "-q", "--bare", bare], check=True)
            git(bare, "fetch", "-q", "--filter=blob:none", url, "+refs/heads/%s:refs/heads/%s" % (m.group(1), m.group(1)))
    default = DEFAULT[repo]
    if not default:
        return "NOT PUSHED (no default branch on GitHub)", default
    if not commit:
        return "NO COMMIT", default
    if branch != default:
        return "BRANCH %r IS NOT THE DEFAULT" % branch, default
    bare = os.path.join(CACHE, repo + ".git")
    if git(bare, "merge-base", "--is-ancestor", commit, default, check=False).returncode:
        return "COMMIT NOT ON %s" % default, default
    return "OK", default


def main():
    gf, main_ref, branches = sys.argv[1], sys.argv[2], sys.argv[3:]
    mine = ours()
    rows = []
    paths = [p for p in git(gf, "ls-tree", "-r", "--name-only", main_ref).stdout.split()
             if p.endswith("/METADATA.pb")]
    for fam, repo, commit, branch in blocks(gf, main_ref, paths):
        if repo in mine:
            rows.append(("main", fam, repo, commit[:12], branch) + verdict(repo, commit, branch))
    for b in branches:
        touched = sorted({p for p in git(gf, "diff", "--name-only", "%s...%s" % (main_ref, b)).stdout.split()
                          if p.endswith("/METADATA.pb")})
        for fam, repo, commit, branch in blocks(gf, b, touched):
            if repo in mine:
                rows.append((b, fam, repo, commit[:12], branch) + verdict(repo, commit, branch))
    head = ("where", "family", "repo", "commit", "branch", "verdict", "default")
    # each commit as a link to its repository, so the table can be published as is
    rows = [r[:3] + ("[%s](https://github.com/googlefonts/%s/commit/%s)" % (r[3], r[2], r[3]) if r[3] else "",)
            + r[4:] for r in rows]
    table = [head] + [tuple(str(c or "-") for c in r) for r in rows]
    w = [max(len(r[i]) for r in table) for i in range(len(head))]
    fmt = lambda r: "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(r)) + " |"
    print(fmt(head))
    print("|" + "|".join("-" * (x + 2) for x in w) + "|")
    for r in table[1:]:
        print(fmt(r))
    bad = [r for r in rows if r[5] != "OK"]
    print("\n%d source blocks, %d not OK" % (len(rows), len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
