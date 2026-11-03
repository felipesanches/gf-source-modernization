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
import re
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
            # only what is public: whether the landed head is on the remote (not its id), a destination as
            # owner/repo (a repository still to create has no URL that answers)
            head = "on-remote" if i["head"] and i["head"][:7] in i["remote"] else "-"
            dest = re.sub(r"^https?://github\.com/", "", i["dest"])
            remote = re.sub(r"=[0-9a-f]{7,40}", "", i["remote"])     # the branches, not their ids
            fh.write("\t".join([repo, i["table"], i["kind"], i["base"], dest, remote,
                                i["branch"], head, i["verdict"], i["ledger"]]) + "\n")
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
    if "--queue" in sys.argv:
        queue = sys.argv[sys.argv.index("--queue") + 1]
        block = markdown(repos, groups)
        q = open(queue, encoding="utf-8").read()
        a, b = q.index(BEGIN) + len(BEGIN), q.index(END)
        open(queue, "w", encoding="utf-8").write(q[:a] + "\n" + block + "\n" + q[b:])
        print("queue block refreshed in", queue)
    elif "--markdown" in sys.argv:
        print(markdown(repos, groups))
    else:
        for g in sorted(groups):
            print("\n%s: %d" % (g, len(groups[g])))
            for x in groups[g]:
                print("   " + x)
    print("\nwritten", out)


BEGIN = "<!-- repo-status begin (generated by gf-source-modernization tools/repo_status.py; edit repo-notes.tsv, not this) -->"
END = "<!-- repo-status end -->"


def table(rows):
    """An aligned GFM table from a list of rows (first row = header)."""
    w = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    line = lambda r: "| " + " | ".join(str(r[i]).ljust(w[i]) for i in range(len(w))) + " |"
    return "\n".join([line(rows[0]), "|" + "|".join("-" * (x + 2) for x in w) + "|"] + [line(r) for r in rows[1:]])


def notes():
    p = os.path.join(W, "repo-notes.tsv")
    with open(p, encoding="utf-8") as fh:
        return collections.OrderedDict((r["repo"], r["note"]) for r in csv.DictReader(fh, delimiter="\t"))


def by_note(names, note_of):
    """Groups of repositories per note, in the order the notes file lists them."""
    order, groups = [], collections.defaultdict(list)
    for repo in note_of:
        if repo in names and note_of[repo] not in order:
            order.append(note_of[repo])
    for n in sorted(names):
        groups[note_of.get(n, "(no note yet in repo-notes.tsv)")].append(n)
    for g in groups:
        if g not in order:
            order.append(g)
    return [(g, groups[g]) for g in order]


def markdown(repos, groups):
    import datetime
    today = datetime.date.today().isoformat()
    note_of = notes()
    name = lambda x: x.split(" (")[0]
    g = lambda key: [name(x) for k, v in groups.items() if k.startswith(key) for x in v]
    empty_clean = g("EMPTY, landed CLEAN")
    empty_wait = g("EMPTY, waiting")
    create_clean = g("MISSING, landed CLEAN")
    create_wait = g("MISSING, conversion")
    create_origin = g("landed clone's origin")
    create_census = g("census only (not paired yet): googlefonts/<slug> MISSING")
    census_exists = g("census only (not paired yet): googlefonts/<slug> exists")
    content = g("has content")
    published = g("PUBLISHED")
    to_create = len(create_clean) + len(create_wait) + len(create_origin) + len(create_census)
    out = ["**Repositories under github.com/googlefonts, %s** (`python3 -I tools/repo_status.py --queue "
           "/home/fsanches/compartilhado/GoogleFonts/PR-QUEUE.md` refreshes this block; the lists are repos-status.tsv and repos-to-create.txt):" % today, ""]
    out.append(table([["group", "count"],
                      ["to create, landing CLEAN now", len(create_clean)],
                      ["to create, paired but the conversion is not CLEAN yet", len(create_wait)],
                      ["to create, landed in a clone whose origin is the upstream repository (bottleneck 13a)", len(create_origin)],
                      ["to create, census families not paired yet", len(create_census)],
                      ["already created empty, landing CLEAN, blocked only by a push or a yes", len(empty_clean)],
                      ["already created empty, waiting for a better conversion", len(empty_wait)],
                      ["existing with content: a branch and a pull request each", len(content)],
                      ["published: the landed head is on GitHub", len(published)]]))
    out += ["", "**For your colleagues: create these %d repositories, empty (no README, no license file):**" % to_create,
            "", "    /home/fsanches/compartilhado/gf-source-modernization/repos-to-create.txt", ""]
    out.append("Of them, CLEAN now: " + " ".join(sorted(create_clean)) + ". Not under googlefonts at all yet, by census class: "
               + ", ".join("%d %s" % (n, k) for k, n in collections.Counter(
                   repos[s]["kind"] for s in create_census).most_common()) + ".")
    out += ["", "**Already created empty, landing CLEAN: %d. Blocked by:**" % len(empty_clean)]
    for note, names in by_note(empty_clean, note_of):
        out.append("- %s: %s" % (note, " ".join(names)))
    out += ["", "**Already created empty, waiting for a better conversion: %d, the priority for conversion work, in this order:**" % len(empty_wait)]
    for note, names in by_note(empty_wait, note_of):
        out.append("- %s: %s" % (note, " ".join(names)))
    out += ["", "**Existing repositories with content, a branch and a pull request each: %d.** " % len(content)
            + "; ".join("%s (%s)" % (n, note_of.get(n, "?")) for n in sorted(content)) + "."]
    out += ["", "**Published: %d.** %d census families already have a googlefonts repository with content and land there as pull requests: %s." % (
        len(published), len(census_exists), " ".join(sorted(census_exists)))]
    return "\n".join(out)


if __name__ == "__main__":
    main()
