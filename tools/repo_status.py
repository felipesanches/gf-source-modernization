#!/usr/bin/env python3
"""Where every repository of the conversion stands against GitHub.

Question answered: which googlefonts/<repo> destinations exist and are still EMPTY
(created for us, waiting for a push), which are MISSING (Felipe must create them), which
already have content (a landing goes there as a branch and a pull request), and what the
latest landing of each repository achieved -- so the queue can say which repositories
are ready to push today and which empty repositories are waiting for a better conversion.

Reads the pairing tables (families*.tsv), the landing ledgers (landed.tsv; landed-vfb*.tsv
are measurement only, their converter is not public) and asks GitHub once per repository
(`git ls-remote`). Writes repos-status.tsv, repos-to-create.txt (every googlefonts/<slug> that does not
exist yet, one per line, for the colleagues who create them) and prints the groups the
queue lists. The census's legacy families not yet in a pairing table are included so the
list covers the whole goal (classes in CENSUS_CLASSES; "modern" families keep theirs).

Usage: python3 -I tools/repo_status.py [--no-fetch]    (~1 min; --no-fetch reuses the tsv)
"""
import collections
import concurrent.futures
import csv
import os
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = ("families.tsv", "families-next.tsv", "families-binary.tsv", "families-vfb.tsv")
LEDGERS = (("landed.tsv", "public"), ("landed-vfb-fixes.tsv", "unpublished converter"),
           ("landed-vfb.tsv", "upstream vfb reader"))
# census classes whose families will get a modernized source repository of their own
# (families of class "modern" keep their upstream repository)
CENSUS_CLASSES = ("sfd", "vfb", "sfd+vfb", "binary-only", "no-repo", "empty")
CLONES = ("/home/fsanches/compartilhado/sfd-reland-repos",
          "/home/fsanches/compartilhado/vfb-reland-repos-fixes",
          "/home/fsanches/compartilhado/vfb-reland-repos")


def rows(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh if l.strip()]


def remote_state(url):
    """MISSING, EMPTY, or the branch names GitHub serves."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(["git", "ls-remote", "--heads", url], capture_output=True, text=True, env=env)
    if p.returncode != 0:
        # a repository that does not exist: GitHub answers 404 or, over https without
        # credentials, asks for a username
        err = p.stderr.lower()
        if "not found" in err or "could not read username" in err or "repository" in err:
            return "MISSING"
        return "ERROR " + p.stderr.strip()[:60]
    heads = ["%s=%s" % (l.split("refs/heads/", 1)[1], l[:7]) for l in p.stdout.splitlines() if "refs/heads/" in l]
    return "EMPTY" if not heads else "branches: " + " ".join(sorted(heads))


def main():
    repos = collections.OrderedDict()
    for t in TABLES:
        for r in rows(os.path.join(W, t)):
            repos.setdefault(r["repo"], {"table": t, "kind": r["kind"], "base": r["base"]})
    landed = {}
    for name, note in LEDGERS:   # the first ledger that has the repo wins; within it, the last row
        p = os.path.join(W, name)
        if not os.path.exists(p):
            continue
        here = {}
        with open(p, encoding="utf-8") as fh:
            for l in fh:
                f = l.rstrip("\n").split("\t")
                if len(f) >= 5 and f[0] in repos:
                    here[f[0]] = {"branch": f[1], "head": f[2], "verdict": f[4], "ledger": name}
        for repo, row in here.items():
            landed.setdefault(repo, row)
    # the census: every legacy-source family not yet in a pairing table (slug = its
    # google/fonts directory), so the list of repositories to create covers the whole goal
    with open(os.path.join(W, "scope", "census.tsv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            slug = r["gf_path"].rstrip("/").rsplit("/", 1)[-1]
            if slug not in repos and r["class"] in CENSUS_CLASSES:
                repos[slug] = {"table": "census", "kind": r["class"], "base": r["repo"]}
    for repo, info in repos.items():
        info["dest"] = "https://github.com/googlefonts/%s.git" % repo
        for c in CLONES:
            d = os.path.join(c, repo)
            if os.path.isdir(d):
                p = subprocess.run(["git", "-C", d, "remote", "get-url", "origin"], capture_output=True, text=True)
                if p.returncode == 0 and p.stdout.strip():
                    info["dest"] = p.stdout.strip()
                break
        info.update(landed.get(repo, {"branch": "", "head": "", "verdict": "not landed", "ledger": ""}))
    out = os.path.join(W, "repos-status.tsv")
    if "--no-fetch" in sys.argv and os.path.exists(out):
        prev = {r["repo"]: r["remote"] for r in rows(out)}
        for repo in repos:
            repos[repo]["remote"] = prev.get(repo, "?")
    else:
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            states = dict(zip(repos, ex.map(
                lambda r: remote_state("https://github.com/googlefonts/%s.git" % r), repos)))
        for repo in repos:
            repos[repo]["remote"] = states[repo]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("repo\ttable\tkind\tbase\tdestination\tremote\tlanded_branch\tlanded_head\tverdict\tledger\n")
        for repo, i in repos.items():
            fh.write("\t".join([repo, i["table"], i["kind"], i["base"], i["dest"], i["remote"],
                                i["branch"], i["head"], i["verdict"], i["ledger"]]) + "\n")
    # the repositories Felipe's colleagues must create: one name per line
    with open(os.path.join(W, "repos-to-create.txt"), "w", encoding="utf-8") as fh:
        for repo, i in repos.items():
            if i["remote"] == "MISSING":
                fh.write(repo + "\n")
    groups = collections.defaultdict(list)
    for repo, i in repos.items():
        if i["table"] == "census":
            groups["census only (not paired yet): googlefonts/<slug> " + ("MISSING" if i["remote"] == "MISSING" else "exists")].append(
                "%s (%s)" % (repo, i["kind"]))
            continue
        gf = "/googlefonts/" in i["dest"]
        public = i["ledger"] == "landed.tsv"
        clean = i["verdict"] in ("CLEAN", "CLEAN-DISCLOSED") and public
        if not gf:
            g = "landed clone's origin is not a googlefonts repository (decision); googlefonts/<repo> " + i["remote"].split(":")[0]
        elif i["remote"] == "EMPTY":
            g = "EMPTY, landed CLEAN: ready to push (push.sh --check first)" if clean else "EMPTY, waiting for a better conversion"
        elif i["remote"] == "MISSING":
            g = "MISSING, landed CLEAN: create it, then push" if clean else "MISSING, conversion not ready yet"
        elif i["remote"].startswith("branches"):
            ours = "%s=%s" % (i["branch"], i["head"][:7]) in i["remote"] if i["head"] else False
            g = "PUBLISHED: the landed head is on it" if ours else "has content: a branch and a pull request"
        else:
            g = i["remote"]
        groups[g].append("%s (%s%s)" % (repo, i["verdict"], "" if public or not i["ledger"] else ", " + dict(LEDGERS)[i["ledger"]]))
    for g in sorted(groups):
        print("\n%s: %d" % (g, len(groups[g])))
        for x in groups[g]:
            print("   " + x)
    print("\nwritten", out)


if __name__ == "__main__":
    main()
