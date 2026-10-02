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
     A `glyphs` row (the source already is .glyphs): the upstream history at its
     commit, the template, then "Add a gftools-builder config for <source>" last,
     adding only sources/config.yaml; no edit commits (land.py refuses them), so
     the source at HEAD is byte-identical to the upstream's.
  4. CORRESPONDENCE: a fresh clone builds from its own sources/config.yaml, every
     style gates at 0 blocking rows against the release, and maps EXACTLY the
     release's codepoints (the gate itself tolerates gained ones).
  5. MESSAGES: ASCII only; each ends with "Assisted by an AI agent (Claude ...)";
     none carries Co-Authored-By.
  6. REMOTE: origin points at the repository it will be pushed to.
  7. FUNCTIONAL: every style built in step 4 behaves like its release under
     tools/functional_gate.py -- cmap, HarfBuzz shaping, rendering, names, line
     spacing, advances, GDEF (the table gate is structural and accepts rows that
     change behaviour).

Usage: verify_landed.py <repo> [<repo> ...]     exit 1 if anything fails
       (FAMILIES=families-next.tsv for the next batch; SCRATCH=<dir> for the
       fresh clones, default the session scratchpad)
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import functional_gate  # noqa: E402
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


def glyphs_shape(d, rows, log, subjects):
    """SHAPE of a `glyphs` repository: template, then the config commit, nothing else."""
    problems = []
    want = "Add a gftools-builder config for %s" % rows[0]["source"]
    if subjects[-1] != want:
        problems.append("SHAPE: the last commit is %r, not %r" % (subjects[-1], want))
    for c, s in zip(log[1:-1], subjects[1:-1]):
        if s != "Adopt the Unified Font Repository template":
            problems.append("SHAPE: %s %r: a glyphs row allows no edit commits" % (c[:7], s))
    if subjects[1:-1] != ["Adopt the Unified Font Repository template"]:
        problems.append("SHAPE: want exactly one template commit before the config, got %s"
                        % subjects[1:-1])
    changed = run("git", "-C", d, "diff-tree", "--no-commit-id", "--name-status", "-r",
                  log[-1]).stdout.splitlines()
    if not re.fullmatch(r"[AM]\tsources/config\.yaml", "\n".join(changed)):
        problems.append("SHAPE: the config commit must change only sources/config.yaml: %s" % changed)
    return problems


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
    if kind == "glyphs":
        for src in sorted({r["source"] for r in rows}):
            want = run("git", "-C", mirror, "rev-parse", "%s:%s" % (commit, src)).stdout.strip()
            got = run("git", "-C", d, "rev-parse", "HEAD:%s" % src).stdout.strip()
            if not want or want != got:
                problems.append("ORIGINAL: %s at HEAD is not byte-identical to %s@%s (%s vs %s)"
                                % (src, base, commit[:12], got, want))
        branch = run("git", "-C", d, "symbolic-ref", "--short", "HEAD").stdout.strip()
        if branch != land.BRANCH[kind]:
            problems.append("SHAPE: on branch %r, want %r" % (branch, land.BRANCH[kind]))

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
    if kind == "glyphs":
        problems += glyphs_shape(d, rows, log, subjects)
    elif not subjects[-1].startswith("Convert to .glyphs with babelfont "):
        problems.append("SHAPE: the last commit is %r, not the conversion" % subjects[-1])
    middle = log[start:-1] if kind != "glyphs" else []
    for c, s in zip(middle, subjects[start:-1]):
        if s == "Adopt the Unified Font Repository template":
            continue
        changed = run("git", "-C", d, "diff-tree", "--no-commit-id", "--name-only", "-r", c).stdout.split()
        if not changed or any(not p.lower().endswith(".sfd") for p in changed):
            problems.append("SHAPE: %s %r touches non-.sfd files: %s" % (c[:7], s, changed))
    retired = run("git", "-C", d, "diff-tree", "--no-commit-id", "--name-status", "-r", log[-1]).stdout
    for r in rows if kind != "glyphs" else []:
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
    os.makedirs(land.SCRATCH, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="verify-%s-" % repo, dir=land.SCRATCH) as tmp:
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
            # one .glyphs file with several instances: each style is its own instance
            name = (r["style"] + ".ttf" if kind == "glyphs" else
                    land.built_name(os.path.join(clone, "sources", r["style"] + ".glyphs")))
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
            gained, lost = land.cmap_difference(r["shipped"], os.path.join(ttf, name))
            if gained or lost:
                problems.append("CMAP: %s gains %s, loses %s" % (
                    r["style"], ["U+%04X" % c for c in gained], ["U+%04X" % c for c in lost]))
            # 7. behaviour, reusing the diffenator3 run the table gate just made
            font = os.path.join(ttf, name)
            try:
                fg = functional_gate.run(r["shipped"], font, r["style"],
                                         d3_json=land.d3_json_path(font, tmp), workdir=tmp)
            except Exception as e:        # a gate that crashed has not passed
                problems.append("FUNCTIONAL: %s: the gate crashed: %r" % (r["style"], e))
                continue
            for check in functional_gate.failed_checks(fg):
                c = fg["checks"][check]
                problems.append("FUNCTIONAL: %s %s: %s%s" % (
                    r["style"], check, c["summary"],
                    "" if not c["failures"] else " -- " + c["failures"][0][:200]))
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
