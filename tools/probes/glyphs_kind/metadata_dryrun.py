#!/usr/bin/env python3
"""Question answered: what would tools/metadata.py write for these landed repositories?

Runs metadata.main() unchanged, but redirected so nothing real is touched:
  - the google/fonts worktree is a throwaway git repository under <scratch> holding only
    each family's METADATA.pb and upstream_info.md, read from google/fonts <gf-ref>
    (no fetch, no worktree added to google/fonts);
  - landed.tsv is a synthetic one marking each repository CLEAN at its HEAD, so a
    RESIDUAL landing (e.g. Play with the unpublished builder) can be previewed.
Prints, per commit made, the commit message and the two files it wrote. Nothing in
the output depends on time or hashes of the throwaway repository, so two runs (before
and after a change to metadata.py) can be compared with diff.

Usage: OUT=<landed repos dir> [FAMILIES=<tsv>] metadata_dryrun.py <scratch> <gf-ref> <repo>...
"""
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, TOOLS)
import land      # noqa: E402
import metadata  # noqa: E402


def git(d, *a, **kw):
    return subprocess.run(["git", "-C", d, *land.IDENT, *a], capture_output=True, text=True,
                          check=True, **kw).stdout


def main():
    scratch, gf_ref, repos = sys.argv[1], sys.argv[2], sys.argv[3:]
    wt = os.path.join(scratch, "wt")
    fake_w = os.path.join(scratch, "w")
    subprocess.run(["rm", "-rf", wt, fake_w], check=True)
    os.makedirs(wt)
    os.makedirs(fake_w)
    os.symlink(os.path.join(land.W, "plans"), os.path.join(fake_w, "plans"))
    git(wt, "init", "-q")
    with open(os.path.join(fake_w, "landed.tsv"), "w") as fh:
        for repo in repos:
            rows = land.family_rows(repo)
            lic, fam = rows[0]["lic"], rows[0]["family"]
            for f in ("METADATA.pb", "upstream_info.md"):
                p = "%s/%s/%s" % (lic, fam, f)
                r = subprocess.run(["git", "-C", land.GF, "show", "%s:%s" % (gf_ref, p)],
                                   capture_output=True)
                if r.returncode == 0:
                    os.makedirs(os.path.join(wt, lic, fam), exist_ok=True)
                    open(os.path.join(wt, p), "wb").write(r.stdout)
            head = git(os.path.join(land.OUT, repo), "rev-parse", "--short", "HEAD").strip()
            fh.write("\t".join([repo, "-", head, "-", "CLEAN", "-"]) + "\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "base")
    land.W = fake_w
    metadata.worktree = lambda branch: wt
    sys.argv = ["metadata.py", "dryrun"] + repos
    devnull = open(os.devnull, "w")
    real, sys.stdout = sys.stdout, devnull     # main prints throwaway hashes
    try:
        metadata.main()
    finally:
        sys.stdout = real
    for c in git(wt, "rev-list", "--reverse", "HEAD~%d..HEAD" % len(repos)).split():
        print("=" * 72)
        print(git(wt, "log", "-1", "--format=%B", c).rstrip("\n"))
        for p in git(wt, "diff-tree", "--no-commit-id", "--name-only", "-r", c).split():
            print("-" * 30, p)
            print(git(wt, "show", "%s:%s" % (c, p)).rstrip("\n"))


if __name__ == "__main__":
    main()
