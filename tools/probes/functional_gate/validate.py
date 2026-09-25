#!/usr/bin/env python3
"""Question answered: what does tools/functional_gate.py say about every landed style, and
about the known non-equivalent cases the table gate passed?

For every repository of families.tsv and families-next.tsv with a landed.tsv row: clone
../sfd-reland-repos/<repo> fresh and build it with the pinned builder3 (as verify_landed.py
step 4 does), run diffenator3 with land.gate()'s flags, then the functional gate. Pairs that
are not landed repositories (Lohit-Bengali's provenance-repaired build) come from EXTRA.tsv
(label, shipped, built, d3 json; `$S` stands for the scratch root).

Writes one TSV row per style to stdout: repo, style, verdict, the seven check statuses, and
the first failure of each failing check. Per-style verdict JSON: $S/runs/<style>.json.

Usage:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY tools/probes/functional_gate/validate.py [--rebuild] [repo ...] > tools/probes/functional_gate/RESULT.tsv
Scratch root $S: FG_SCRATCH, default /home/fsanches/compartilhado/sfd-reland-scratch/functional-gate
(builds/<repo>/clone, d3/<style>.json, runs/<style>.json -- all regenerable).
"""
import csv
import json
import multiprocessing
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(W, "tools"))
import functional_gate  # noqa: E402
import land             # noqa: E402

S = functional_gate.SCRATCH
R = land.OUT
CHECKS = ["cmap", "shaping", "rendering", "names", "line_spacing", "advances", "gdef"]


def landed_rows():
    landed = {l.split("\t")[0] for l in open(os.path.join(W, "landed.tsv"))}
    out = []
    for tsv in ("families.tsv", "families-next.tsv"):
        for r in csv.DictReader(open(os.path.join(W, tsv)), delimiter="\t"):
            if r["repo"] in landed and os.path.isdir(os.path.join(R, r["repo"])):
                out.append(r)
    return out


def build(repo, rebuild):
    d = os.path.join(S, "builds", repo)
    clone = os.path.join(d, "clone")
    if rebuild or not os.path.isdir(os.path.join(clone, "fonts", "ttf")):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        subprocess.run(["git", "clone", "-q", os.path.join(R, repo), clone], check=True)
        with open(os.path.join(d, "build.log"), "w") as log:
            subprocess.run([land.B3, "sources/config.yaml"], cwd=clone, stdout=log, stderr=log)
    head = subprocess.run(["git", "-C", clone, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    return clone, head


def d3(shipped, built, style):
    j = os.path.join(S, "d3", style + ".json")
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        os.makedirs(os.path.dirname(j), exist_ok=True)
        with open(j, "w") as fh:
            subprocess.run([land.D3, "-J", "1", "--no-languages", "--no-match", "--json", "--succinct",
                            shipped, built], stdout=fh, stderr=subprocess.DEVNULL)
    return j


def one(job):
    repo, style, shipped, built, j = job
    if not os.path.exists(built):
        return [repo, style, "NOT-BUILT"] + ["-"] * len(CHECKS) + [built]
    j = j or d3(shipped, built, style)
    try:
        res = functional_gate.run(shipped, built, style, d3_json=j)
    except Exception as e:
        return [repo, style, "CRASH"] + ["-"] * len(CHECKS) + [repr(e)]
    os.makedirs(os.path.join(S, "runs"), exist_ok=True)
    with open(os.path.join(S, "runs", style + ".json"), "w") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False, default=list)
    first = []
    for c in CHECKS:
        ch = res["checks"][c]
        if ch["status"] != "PASS":
            first.append("%s: %s" % (c, (ch["failures"] or [ch["summary"]])[0][:160]))
    return [repo, style, res["verdict"]] + [res["checks"][c]["status"] for c in CHECKS] + \
        [" | ".join(first).replace("\t", " ").replace("\n", " ")]


def jobs(repos=(), rebuild=False):
    """(repo@HEAD, style, shipped, built, d3 json or None) for every landed style (built
    here if its build is missing) and, when no repository is named, every EXTRA.tsv pair."""
    out = []
    for r in landed_rows():
        if repos and r["repo"] not in repos:
            continue
        clone, head = build(r["repo"], rebuild)
        g = os.path.join(clone, "sources", r["style"] + ".glyphs")
        built = os.path.join(clone, "fonts", "ttf", land.built_name(g)) if os.path.exists(g) else g
        out.append((r["repo"] + "@" + head, r["style"], r["shipped"], built, None))
    extra = os.path.join(HERE, "EXTRA.tsv")
    if os.path.exists(extra) and not repos:
        for line in open(extra):
            if line.startswith("#") or not line.strip():
                continue
            label, shipped, built, j = line.rstrip("\n").split("\t")
            built, j = built.replace("$S", S), j.replace("$S", S)
            out.append(("extra", label, shipped, built, j if j != "-" else None))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    all_jobs = jobs(args, "--rebuild" in sys.argv)
    print("\t".join(["repo", "style", "verdict"] + CHECKS + ["first failure per failing check"]))
    with multiprocessing.Pool(3) as pool:
        for row in pool.imap(one, all_jobs):
            print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
