#!/usr/bin/env python3
"""Each style's .sfd exactly as tools/land.py converts it, without building a repository.

land.py imports a family (step 1), adopts the template (step 2, which touches no .sfd) and
applies plans/<repo>.json commit by commit (step 3). This does steps 1 and 3 in a scratch
tree: the family's files from the repo archive at the pinned commit, then every plan op in
order, with tools/sfd_edit.py. `stop_before` names ops to leave out (so a census can look at
a source as it was before an edit this probe is measuring).

Used by census.py and convert_check.py in this directory; not a tool of its own.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(W, "tools"))
import sfd_edit  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
SCRATCH = os.path.join(os.environ.get("TMPDIR", "/home/fsanches/compartilhado/tmp"),
                       "exporter-source-edits")


def rows():
    out = []
    for t in ("families.tsv", "families-next.tsv"):
        with open(os.path.join(W, t), encoding="utf-8") as fh:
            head = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                r = dict(zip(head, line.rstrip("\n").split("\t")))
                if r.get("repo"):
                    out.append(r)
    return out


def plan(repo):
    p = os.path.join(W, "plans", repo + ".json")
    return json.load(open(p)) if os.path.exists(p) else {"commits": []}


def _extract(rows_, d):
    r0 = rows_[0]
    kind, base, commit = r0["kind"], r0["base"], r0["commit"]
    mirror = os.path.join(ARC, base + ".git")
    os.makedirs(d)
    if kind == "allerta":
        for r in rows_:
            blob = subprocess.run(["git", "-C", mirror, "show", "%s:%s" % (commit, r["source"])],
                                  capture_output=True, check=True).stdout
            os.makedirs(os.path.join(d, os.path.dirname(r["source"])), exist_ok=True)
            open(os.path.join(d, r["source"]), "wb").write(blob)
        return
    if kind == "hg":
        path = "%s/%s" % (r0["lic"], r0["family"])
        if not subprocess.run(["git", "-C", mirror, "ls-tree", "--name-only", commit, path],
                              capture_output=True, text=True).stdout.strip():
            path = r0["family"]
        strip = path.count("/") + 1
        tar = subprocess.run(["git", "-C", mirror, "archive", commit, path],
                             capture_output=True, check=True).stdout
    else:
        strip = 0
        tar = subprocess.run(["git", "-C", mirror, "archive", commit],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", d, "--strip-components=%d" % strip], input=tar, check=True)


def edited(repo, stop_before=(), tag="final", plan_override=None):
    """{style: path of its .sfd after the plan} in SCRATCH/<tag>/<repo>/. Ops named in
    stop_before (and every later op of the same style) are skipped. plan_override: a plan
    to apply instead of plans/<repo>.json (another revision's)."""
    rows_ = [r for r in rows() if r["repo"] == repo]
    if not rows_ or rows_[0]["kind"] == "glyphs":
        return {}
    d = os.path.join(SCRATCH, tag, repo)
    assert os.path.realpath(d).startswith(os.path.realpath(SCRATCH) + os.sep)
    if os.path.exists(d):
        shutil.rmtree(d)
    _extract(rows_, d)
    by_style = {r["style"]: r for r in rows_}
    stopped = set()
    for c in (plan_override if plan_override is not None else plan(repo)).get("commits", []):
        styles = list(by_style) if c.get("styles", "*") in ("*", ["*"]) else c["styles"]
        ops = c["ops"] if "ops" in c else [[c["op"], c.get("args", "")]]
        for st in styles:
            for op, args in ops:
                if op in stop_before:
                    stopped.add(st)
                if st in stopped:
                    continue
                sfd_edit.apply_file(os.path.join(d, by_style[st]["source"]), op, args)
    return {st: os.path.join(d, r["source"]) for st, r in by_style.items()}
