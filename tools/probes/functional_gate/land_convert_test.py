#!/usr/bin/env python3
"""Question answered: does land.py's convert step, with the functional gate wired in, write
the right commit message and verdict -- without touching ../sfd-reland-repos or landed.tsv?

Runs land.start / template / edits / convert for one repository inside the functional-gate
scratch ($FG_SCRATCH/land-test/<repo>, builds under $SCRATCH, default
$FG_SCRATCH/land-scratch) with the converter land.py pins, then prints the convert commit
message and each style's table-gate rows and functional verdict. check_converter() is not
called, so the message names the upstream repository whatever the converter's status.

Usage: FAMILIES=families-next.tsv $PY tools/probes/functional_gate/land_convert_test.py <repo>
"""
import os
import shutil
import sys
S = os.environ.get("FG_SCRATCH", "/home/fsanches/compartilhado/sfd-reland-scratch/functional-gate")
os.environ.setdefault("SCRATCH", os.path.join(S, "land-scratch"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import land  # noqa: E402
repo = sys.argv[1]
rows = land.family_rows(repo)
plan = land.load_plan(repo)
d = os.path.join(S, "land-test", repo)
shutil.rmtree(d, ignore_errors=True)
os.makedirs(os.path.dirname(d), exist_ok=True)
land.start(repo, rows, d)
land.template(repo, rows, d)
made = land.edits(repo, rows, d, plan)
bf = land.git(land.BF_TREE, "rev-parse", "--short", "HEAD").stdout.strip()
head, results, functional = land.convert(repo, rows, d, plan, bf, len(made))
print(land.git(d, "log", "-1", "--format=%B").stdout)
for st, n, blocking in results:
    print(st, n, blocking[:3], functional[st]["verdict"], land.functional_gate.failed_checks(functional[st]))
print("scratch left behind:", os.listdir(os.environ["SCRATCH"]))
