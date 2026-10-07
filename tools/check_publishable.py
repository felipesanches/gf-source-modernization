#!/usr/bin/env python3
"""Question answered: does any text we are about to publish refer to something that is not
public?

Rule (Felipe, 2026-10-05, restated 2026-10-06): everything we publish may refer only to
public commits, files and URLs -- at the moment it is written, independent of push order.

Checks every unit given:
  <repo dir>:<range>   the commit messages and the ADDED lines of each commit in the range
                       (what a push would publish)
  <file>               the whole file (a PR body, a reply)
For each text:
  1. no workstation path (/home/..., /tmp/..., ~/compartilhado);
  2. every hexadecimal id (7-40 digits, with a letter and a digit) is public: a commit on
     the published branch of a public repository mirrored here (KNOWN, or the repo-archive
     mirror of a repository the same text names), else a commit GitHub serves for a
     repository named in a github.com URL of the same text (reported "off-branch"). An
     answer GitHub refuses (rate limit) counts as NOT public, never as public;
  3. every github.com URL answers HTTP 200;
  4. no "PLACEHOLDER" is left (a draft whose links or revisions are not known yet).
A hex id that is only the unit's own unpublished commit fails too: a push does not make a
text's reference to a not-yet-pushed commit public in time for everyone reading it.
Tool output under logs/ is checked like everything else: a log can carry local hashes too.
One exception: a google-fonts-sources output (JSON with "fonts_repo_sha" and "sources"),
whose revs are google/fonts' own METADATA.pb records; only its fonts_repo_sha is checked
(it must be public), since the rest is regenerable from that public google/fonts commit.
Code under tools/ (.py, .sh) may name workstation paths -- where the tools run, as the README
says -- so check 1 does not apply to it; checks 2 and 3 do. Prose, messages and PR texts get
all three.

Usage: check_publishable.py [--fetch] <unit>...     exit 1 if anything is not public
"""
import os
import re
import subprocess
import sys

C = "/home/fsanches/compartilhado"
ARC = C + "/upstream_repos/repo_archive"
# (local repository, published ref) -- refreshed with --fetch
KNOWN = [
    (C + "/gftools", "origin", "main"),
    (C + "/gftools-rust", "origin", "main"),
    (C + "/babelfont-rs-worktrees/upstream-main", "upstream", "main"),
    (C + "/gfonts", "origin", "main"),
    (C + "/tmp_fontc_crater_investigate", "origin", "main"),
    (C + "/fontc", "origin", "main"),
    (C + "/google-fonts-sources", "origin", "main"),
    (C + "/gf-source-modernization", "https://github.com/felipesanches/gf-source-modernization", "main"),
    (ARC + "/googlefonts/googlesans.git", None, "main"),
    (ARC + "/googlefonts/googlesans-flex.git", None, "main"),
    (ARC + "/googlefonts/googlefontdirectory-hg.git", None, "master"),
]
LOCAL = re.compile(r"(/home/\w+|/tmp/|~/compartilhado)")
HEX = re.compile(r"(?<![0-9A-Za-z/#.-])([0-9a-f]{7,40})(?![0-9A-Za-z])")
URL = re.compile(r"https://github\.com/[^\s'\"`)<>\]]+")
REPO = re.compile(r"(?:github\.com/|\b)([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?=[#\s/)`'\".,:;]|$)")


def git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)


def ref(repo, remote, branch):
    if remote is None:
        return branch
    if remote.startswith("https://"):
        return "refs/published/" + branch
    return "%s/%s" % (remote, branch)


def fetch():
    for repo, remote, branch in KNOWN:
        if remote is None:
            git(repo, "remote", "update")
        elif remote.startswith("https://"):
            git(repo, "fetch", "-q", remote, branch)
            git(repo, "update-ref", "refs/published/" + branch, "FETCH_HEAD")
        else:
            git(repo, "fetch", "-q", remote, branch)


def on_published_branch(h):
    for repo, remote, branch in KNOWN:
        full = git(repo, "rev-parse", "--verify", "-q", h + "^{commit}").stdout.strip()
        if full and git(repo, "merge-base", "--is-ancestor", full, ref(repo, remote, branch)).returncode == 0:
            return "%s %s" % (os.path.basename(repo.rstrip("/")).replace(".git", ""), branch)
    return None


def in_archive(h, text):
    """On the default branch of the repo-archive mirror of the repository named by the
    nearest github.com URL before the id (a JSON entry: repo_url, then rev), else of any of
    the first 40 repositories the text names."""
    pos = text.find(h)
    near = [m.group(1) for m in re.finditer(r"github\.com/([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?[\"/\s]", text[:pos])][-1:]
    line = text[text.rfind("\n", 0, pos) + 1:pos]          # "owner/repo/..." earlier on the same line
    near += [m.group(1) for m in re.finditer(r"\b([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/", line)][:1]
    for slug in near + sorted(set(REPO.findall(text)))[:40]:
        mirror = "%s/%s.git" % (ARC, slug)
        if not os.path.isdir(mirror):
            continue
        full = git(mirror, "rev-parse", "--verify", "-q", h + "^{commit}").stdout.strip()
        if full and git(mirror, "merge-base", "--is-ancestor", full, "HEAD").returncode == 0:
            return slug
    return None


def served_by_github(h, text):
    """(slug, None) if GitHub serves the commit; (None, reason) otherwise."""
    reason = "not found on GitHub"
    for u in sorted(set(URL.findall(text)))[:8]:
        m = re.match(r"https://github\.com/([A-Za-z0-9-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?:/|$)", u)
        if not m:
            continue
        code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                               "https://api.github.com/repos/%s/commits/%s" % (m.group(1), h)],
                              capture_output=True, text=True).stdout
        if code in ("403", "429"):
            # the API is rate-limited; the public commit page answers the same question
            code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-w", "%{http_code}", "-I",
                                   "https://github.com/%s/commit/%s" % (m.group(1), h)],
                                  capture_output=True, text=True).stdout
            if code not in ("200", "404"):
                reason = "UNVERIFIED: GitHub refused (%s)" % code
        if code == "200":
            return m.group(1), None
    return None, reason


def texts(unit):
    if ":" in unit and os.path.isdir(unit.split(":", 1)[0]):
        d, rng = unit.split(":", 1)
        for sha in git(d, "rev-list", "--reverse", rng).stdout.split():
            yield "%s %s message" % (os.path.basename(d), sha[:9]), git(d, "log", "-1", "--format=%B", sha).stdout
            diff = git(d, "show", "--format=", "--unified=0", sha).stdout
            prose, code, cur = [], [], ""
            for l in diff.splitlines():
                if l.startswith("+++ "):
                    cur = l[6:] if l.startswith("+++ b/") else l[4:]
                    blob = git(d, "show", "%s:%s" % (sha, cur)).stdout if cur.endswith(".json") else ""
                    if '"fonts_repo_sha"' in blob and '"sources"' in blob:
                        frs = re.search(r'"fonts_repo_sha": "([0-9a-f]+)"', blob).group(1)
                        yield "%s %s %s (gfs output)" % (os.path.basename(d), sha[:9], cur), \
                            "fonts_repo_sha %s of https://github.com/google/fonts" % frs
                        cur = "\0skip"
                elif l.startswith("+") and cur != "\0skip":
                    (code if cur.startswith("tools/") and cur.endswith((".py", ".sh")) else prose).append(l[1:])
            yield "%s %s added lines" % (os.path.basename(d), sha[:9]), "\n".join(prose)
            if code:
                yield "%s %s added code" % (os.path.basename(d), sha[:9]), "\n".join(code)
    else:
        yield unit, open(unit, encoding="utf-8").read()


def main():
    args = sys.argv[1:]
    if "--fetch" in args:
        args.remove("--fetch")
        fetch()
    bad = 0
    for unit in args:
        for where, text in texts(unit):
            problems, notes = [], []
            if "PLACEHOLDER" in text and not where.endswith("added code"):
                problems.append("unfinished: %d PLACEHOLDER(s)" % text.count("PLACEHOLDER"))
            m = None if where.endswith("added code") else LOCAL.search(text)
            if m:
                problems.append("workstation path %s" % m.group(0))
            for h in sorted(set(HEX.findall(text))):
                if not (re.search("[a-f]", h) and re.search("[0-9]", h)):
                    continue
                if on_published_branch(h) or in_archive(h, text):
                    continue
                slug, reason = served_by_github(h, text)
                if slug:
                    notes.append("%s: off-branch, but GitHub serves it in %s" % (h, slug))
                else:
                    problems.append("%s is not public (%s)" % (h, reason))
            for u in sorted(set(URL.findall(text))):
                u = u.rstrip(".,;:`")
                if "{" in u or "<" in u or "%s" in u:   # templates, not references
                    continue
                code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-w", "%{http_code}", "-I", u],
                                      capture_output=True, text=True).stdout
                if code != "200":
                    problems.append("%s answers %s" % (u, code or "nothing"))
            print("%-58s %s" % (where[:58], "NOT PUBLIC" if problems else "public"))
            for p in problems:
                print("    " + p)
            for n in notes:
                print("    note: " + n)
            bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
