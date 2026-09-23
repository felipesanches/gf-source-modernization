#!/usr/bin/env python3
"""Question answered: does a landed repository really have the history it claims?

Independent of tools/land.py -- it re-reads the committed history and rebuilds from
a fresh clone -- and checks, for every repository given:

  1. ORIGINAL: the first commit holds the family's files byte-for-byte as the
     archive does at the revision METADATA.pb records (fresh repositories); a fork
     branches from exactly that revision; a restored file is byte-identical.
  2. LICENCE: OFL.txt at HEAD is the family's own, unchanged, and never the
     template's (which is Bentham's).
  3. SHAPE: every commit between the template and the conversion changes only .sfd
     files (criterion B: each edit to the font is its own commit); the convert
     commit is last and retires the converted sources.
  4. CORRESPONDENCE: a fresh clone builds from its own sources/config.yaml, and
     every style gates at 0 blocking rows against the release.
  5. MESSAGES: ASCII only; each ends with "Assisted by an AI agent (Claude ...)";
     none carries Co-Authored-By.
  6. REMOTE: origin points at the repository it will be pushed to.

Usage: verify_landed.py <repo> [<repo> ...]     exit 1 if anything fails
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land     # noqa: E402
import recipe   # noqa: E402

TEMPLATE_OFL = os.path.join(land.TEMPLATE, "OFL.txt")


def run(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def blobs(repo_dir, rev, prefix=""):
    """{path: blob} for a tree, paths relative to `prefix`."""
    out = run("git", "-C", repo_dir, "ls-tree", "-r", rev, "--", prefix or ".").stdout
    got = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if prefix and not path.startswith(prefix):
            continue
        got[path[len(prefix):]] = meta.split()[2]
    return got


def verify(repo):
    rows = land.family_rows(repo)
    kind, fam, lic, base, commit = (rows[0][k] for k in ("kind", "family", "lic", "base", "commit"))
    d = os.path.join(land.OUT, repo)
    mirror = os.path.join(land.ARC, base + ".git")
    problems = []
    log = run("git", "-C", d, "log", "--reverse", "--format=%H", "HEAD").stdout.split()
    first = log[0]

    # 1. the original
    if kind == "hg":
        ours = blobs(d, first)
        theirs = blobs(mirror, commit, "%s/%s/" % (lic, fam))
        if ours != theirs:
            diff = sorted(set(ours.items()) ^ set(theirs.items()))[:5]
            problems.append("ORIGINAL: first commit differs from %s/%s@%s: %s" % (lic, fam, commit[:12], diff))
        start = 1
    elif kind == "allerta":
        master = run("git", "-C", d, "rev-parse", "master").stdout.strip()
        if run("git", "-C", d, "merge-base", "--is-ancestor", master, "HEAD").returncode:
            problems.append("ORIGINAL: branch does not start from master")
        restore = run("git", "-C", d, "rev-list", "--reverse", "master..HEAD").stdout.split()[0]
        src = rows[0]["source"]
        want = run("git", "-C", mirror, "rev-parse", "%s:%s" % (commit, src)).stdout.strip()
        got = run("git", "-C", d, "rev-parse", "%s:%s" % (restore, src)).stdout.strip()
        if want != got:
            problems.append("ORIGINAL: restored %s is not byte-identical (%s vs %s)" % (src, got, want))
        log = [master] + run("git", "-C", d, "rev-list", "--reverse", "master..HEAD").stdout.split()
        start = 2
    else:
        if run("git", "-C", d, "merge-base", "--is-ancestor", commit, "HEAD").returncode:
            problems.append("ORIGINAL: %s is not an ancestor of HEAD" % commit[:12])
        log = [commit] + run("git", "-C", d, "rev-list", "--reverse", "%s..HEAD" % commit).stdout.split()
        start = 1

    # 2. the licence
    ofl_head = run("git", "-C", d, "show", "HEAD:OFL.txt").stdout
    ofl_orig = run("git", "-C", d, "show", "%s:OFL.txt" % log[0]).stdout
    if ofl_head != ofl_orig:
        problems.append("LICENCE: OFL.txt changed since the original")
    if os.path.exists(TEMPLATE_OFL) and ofl_head and ofl_head == open(TEMPLATE_OFL).read() \
            and ofl_orig != ofl_head:
        problems.append("LICENCE: OFL.txt is the template's (Bentham's)")

    # 3. the shape
    subjects = [run("git", "-C", d, "log", "-1", "--format=%s", c).stdout.strip() for c in log]
    if not subjects[-1].startswith("Convert to .glyphs with babelfont "):
        problems.append("SHAPE: the last commit is %r, not the conversion" % subjects[-1])
    middle = log[start:-1]
    for c, s in zip(middle, subjects[start:-1]):
        if s == "Adopt the Unified Font Repository template":
            continue
        changed = run("git", "-C", d, "diff-tree", "--no-commit-id", "--name-only", "-r", c).stdout.split()
        if not changed or any(not p.lower().endswith(".sfd") for p in changed):
            problems.append("SHAPE: %s %r touches non-.sfd files: %s" % (c[:7], s, changed))
    retired = run("git", "-C", d, "diff-tree", "--no-commit-id", "--name-status", "-r", log[-1]).stdout
    for r in rows:
        if not re.search(r"^D\t%s$" % re.escape(r["source"]), retired, re.M):
            problems.append("SHAPE: the conversion does not retire %s" % r["source"])
        if not re.search(r"^[AM]\tsources/%s\.glyphs$" % re.escape(r["style"]), retired, re.M):
            problems.append("SHAPE: the conversion does not add sources/%s.glyphs" % r["style"])

    # 5. messages
    for c in log[start - 1 if kind == "hg" else start:]:
        msg = run("git", "-C", d, "log", "-1", "--format=%B", c).stdout
        if any(ord(ch) > 127 for ch in msg):
            problems.append("MESSAGE: %s is not ASCII" % c[:7])
        if "Co-Authored-By" in msg:
            problems.append("MESSAGE: %s carries Co-Authored-By" % c[:7])
        if not re.search(r"^Assisted by an AI agent \(Claude [^)]+\)$", msg.strip().splitlines()[-1]):
            problems.append("MESSAGE: %s lacks the AI attribution line" % c[:7])

    # 6. remote
    origin = run("git", "-C", d, "remote", "get-url", "origin").stdout.strip()
    want = ("https://github.com/%s.git" % base if kind == "upstream"
            else "https://github.com/googlefonts/%s.git" % repo)
    if origin != want:
        problems.append("REMOTE: origin is %r, want %r" % (origin, want))

    # 4. correspondence, from a fresh clone
    with tempfile.TemporaryDirectory(prefix="verify-%s-" % repo,
                                     dir="/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/"
                                         "f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad") as tmp:
        clone = os.path.join(tmp, "clone")
        run("git", "clone", "-q", d, clone)
        b = run(land.B3, "sources/config.yaml", cwd=clone)
        ttf = os.path.join(clone, "fonts", "ttf")
        built = sorted(os.listdir(ttf)) if os.path.isdir(ttf) else []
        # a repository extended with a family (allerta) also builds what it had
        expected = len(rows) + (len(built) - len(rows) if kind == "allerta" else 0)
        if len(built) != expected or len(built) < len(rows):
            problems.append("BUILD: %d fonts built for %d styles: %s" % (len(built), len(rows), built))
        for r in rows:
            name = land.built_name(os.path.join(clone, "sources", r["style"] + ".glyphs"))
            if name not in built:
                problems.append("BUILD: %s not produced" % name)
                continue
            try:
                n, blocking = land.gate(r["shipped"], os.path.join(ttf, name), tmp)
            except land.LandError as e:
                problems.append("GATE: %s" % e)
                continue
            if n:
                problems.append("GATE: %s %d blocking row(s): %s" % (r["style"], n, blocking[:3]))
    return problems


def main():
    bad = 0
    for repo in sys.argv[1:]:
        try:
            problems = verify(repo)
        except Exception as e:           # a verifier that crashes has not verified
            problems = ["VERIFIER CRASHED: %r" % e]
        bad += bool(problems)
        print("%-20s %s" % (repo, "VERIFIED" if not problems else "FAILED"))
        for p in problems:
            print("    " + p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
