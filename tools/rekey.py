#!/usr/bin/env python3
"""Question answered: does a landed repository still build the shipped fonts once its
sources/config.yaml says `productionNames: false` instead of `noProductionNames: true`
(gftools-builder renamed the key), and its CI pins the gftools-rust that reads it?

For each repository given (a landed one whose last commit is the conversion, or a
previous "Builder config:" commit):
  1. in its sources/config.yaml, `noProductionNames: true` becomes `productionNames: false`;
     in .github/workflows/build.yaml, GFTOOLS_RUST_REV becomes the builder this run
     cites (land.B3_ID, or NEW_PIN= for a run with an unpublished builder);
  2. that state is built in a scratch copy with land.B3, and every style is gated as
     tools/land.py gates a conversion: table gate, the release's exact codepoints,
     tools/functional_gate.py;
  3. the change is committed as "Builder config: productionNames: false replaces
     noProductionNames", with the measured claim, and a row is appended to landed.tsv
     (CLEAN only if every style passes; -UNPUBLISHED-BUILDER / -UNCOMMITTED-EVIDENCE as
     land.py marks them, so push.sh refuses those).
--redo first drops an unpushed "Builder config:" commit this tool made (kept under
refs/rekey-backup/), so a run with the published builder can replace a provisional one.

Usage: [B3=<gftools-builder> B3_NOTE=<what it is> NEW_PIN=<rev>] rekey.py [--redo] <repo>...
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land  # noqa: E402
import functional_gate  # noqa: E402

SUBJECT = "Builder config: productionNames: false replaces noProductionNames"
OLD, NEW = "noProductionNames: true", "productionNames: false"
WORKFLOW = ".github/workflows/build.yaml"
PIN = os.environ.get("NEW_PIN") or land.B3_ID


def git(d, *a, check=True):
    r = subprocess.run(["git", "-C", d, *land.IDENT, *a], capture_output=True, text=True)
    if check and r.returncode:
        raise land.LandError("git %s: %s" % (" ".join(a), r.stderr.strip()))
    return r.stdout


def rows_for(repo):
    """The family rows, from whichever pairing table lists the repository."""
    for table in ("families.tsv", "families-next.tsv"):
        os.environ["FAMILIES"] = os.path.join(land.W, table)
        try:
            return land.family_rows(repo)
        except land.LandError:
            continue
    raise land.LandError("no rows for %s in families.tsv or families-next.tsv" % repo)


def drop_provisional(d):
    """Remove an unpushed rekey commit (kept under refs/rekey-backup/)."""
    if git(d, "log", "-1", "--format=%s").strip() != SUBJECT:
        return
    head = git(d, "rev-parse", "HEAD").strip()
    remote = git(d, "ls-remote", "origin", "refs/heads/main", check=False).split()
    if remote and subprocess.run(["git", "-C", d, "merge-base", "--is-ancestor", head, remote[0]],
                                 capture_output=True).returncode == 0:
        raise land.LandError("HEAD is already pushed; it cannot be redone")
    git(d, "update-ref", "refs/rekey-backup/%d" % int(time.time()), head)
    git(d, "reset", "-q", "--hard", "HEAD~1")


def rekey(repo, redo):
    d = os.path.join(land.OUT, repo)
    if git(d, "status", "--porcelain", "--untracked-files=no").strip():
        raise land.LandError("%s has uncommitted changes" % repo)
    if redo:
        drop_provisional(d)
    last = git(d, "log", "-1", "--format=%s").strip()
    if not (last.startswith("Convert to .glyphs with babelfont ") or last.startswith("Builder config: ")):
        raise land.LandError("%s: the last commit is %r, not the conversion" % (repo, last))
    cfg = os.path.join(d, "sources", "config.yaml")
    text = open(cfg).read()
    if OLD + "\n" not in text:
        raise land.LandError("%s: sources/config.yaml has no %r" % (repo, OLD))
    rows = rows_for(repo)

    # 1. the change
    open(cfg, "w").write(text.replace(OLD + "\n", NEW + "\n"))
    wf = os.path.join(d, WORKFLOW)
    wtext = open(wf).read()
    old_pin = re.search(r"GFTOOLS_RUST_REV: (\w+)", wtext)
    if not old_pin:
        raise land.LandError("%s: no GFTOOLS_RUST_REV in %s" % (repo, WORKFLOW))
    open(wf, "w").write(wtext.replace(old_pin.group(0), "GFTOOLS_RUST_REV: %s" % PIN))

    # 2. build that state and gate it
    os.makedirs(land.SCRATCH, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="rekey-%s-" % repo, dir=land.SCRATCH)
    shutil.copytree(os.path.join(d, "sources"), os.path.join(scratch, "sources"))
    b = subprocess.run([land.B3, "sources/config.yaml"], cwd=scratch, capture_output=True, text=True)
    ttf = os.path.join(scratch, "fonts", "ttf")
    built = sorted(os.listdir(ttf)) if os.path.isdir(ttf) else []
    results, functional = [], {}
    for r in rows:
        name = land.built_name(os.path.join(scratch, "sources", r["style"] + ".glyphs"))
        if name not in built:
            tail = [l.strip() for l in (b.stderr + b.stdout).splitlines() if l.strip()][-2:]
            results.append((r["style"], None, ["BUILD: %s not produced (%s)" % (name, "; ".join(tail))]))
            continue
        font = os.path.join(ttf, name)
        n, blocking = land.gate(r["shipped"], font, scratch)
        gained, lost = land.cmap_difference(r["shipped"], font)
        if gained or lost:
            n += len(gained) + len(lost)
            blocking.append("CMAP gained %s lost %s" % (gained, lost))
        functional[r["style"]] = functional_gate.run(r["shipped"], font, r["style"],
                                                     d3_json=land.d3_json_path(font, scratch),
                                                     workdir=scratch)
        results.append((r["style"], n, blocking))

    def fverdict(st):
        bad = functional_gate.failed_checks(functional[st]) if st in functional else ["build"]
        return "PASS" if not bad else "FAIL(%s)" % "+".join(bad)
    clean = all(n == 0 and fverdict(st) == "PASS" for st, n, _ in results)

    # 3. the commit, with the measured claim
    gf_ref = subprocess.run(["git", "-C", land.GF, "rev-parse", "--short=12", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    ev_rev, ev_clean = land.evidence()
    lines = [SUBJECT, ""]
    lines += textwrap.wrap("gftools-builder (simoncozens/gftools-rust) renamed the key that keeps "
                           "the source's glyph names: noProductionNames: true is now "
                           "productionNames: false. The CI builds with gftools-rust %s (was %s)."
                           % (PIN, old_pin.group(1)), 72)
    lines.append("")
    if clean:
        lines += textwrap.wrap("Builds with gftools-builder (%s, fontc %s) and matches the binaries "
                               "google/fonts %s ships: 0 blocking rows under tools/table_gate.py, "
                               "exactly the release's codepoints, and functionally equivalent under "
                               "tools/functional_gate.py (cmap, shaping, rendering, names, line "
                               "spacing, advances, GDEF), %d style(s)."
                               % (land.B3_WHERE, land.FONTC_ID, gf_ref, len(results)), 72)
    else:
        lines += textwrap.wrap("Builds with gftools-builder (%s, fontc %s). Against google/fonts %s:"
                               % (land.B3_WHERE, land.FONTC_ID, gf_ref), 72)
        for st, n, blocking in results:
            lines.append("  %s: %s; %s" % (st, "build failed" if n is None else "%d blocking row(s)" % n,
                                          fverdict(st)))
    lines += [""] + textwrap.wrap("Those tools: %s at %s." % (land.EVIDENCE_URL, ev_rev), 72)
    lines += ["", land.TRAILER.strip()]
    git(d, "add", "--", "sources/config.yaml", WORKFLOW)
    subprocess.run(["git", "-C", d, *land.IDENT, "commit", "-q", "-F", "-"],
                   input="\n".join(lines) + "\n", text=True, check=True)
    head = git(d, "rev-parse", "--short", "HEAD").strip()
    shutil.rmtree(scratch, ignore_errors=True)

    status = "CLEAN" if clean else "RESIDUAL"
    if not land.B3_PUBLISHED or os.environ.get("NEW_PIN"):
        status += "-UNPUBLISHED-BUILDER"
    if not ev_clean:
        status += "-UNCOMMITTED-EVIDENCE"
    summary = "; ".join("%s=%s functional=%s" % (st, n if n is not None else "BUILD", fverdict(st))
                        for st, n, _ in results)
    n_commits = int(git(d, "rev-list", "--count", "HEAD").strip())
    with open(land.LANDED, "a") as fh:
        fh.write("\t".join([repo, land.BRANCH[rows[0]["kind"]], head, str(n_commits), status, summary]) + "\n")
    print("%s: %s @ %s: %s" % (repo, status, head, summary))
    return status.startswith("CLEAN")


def main():
    args = sys.argv[1:]
    redo = "--redo" in args
    repos = [a for a in args if not a.startswith("--")]
    bad = 0
    for repo in repos:
        try:
            bad += not rekey(repo, redo)
        except land.LandError as e:
            print("%s: FATAL %s" % (repo, e))
            bad += 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
