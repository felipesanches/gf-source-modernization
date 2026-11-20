#!/usr/bin/env python3
"""Correct a binary-route repository's README after the fact: its opening paragraph and its
"Earlier sources" section, as land.py now writes them (land.binary_opening, land.earlier_section).

Question answered: what should a published README say about the sources published before?
Until 2026-11-20 land.py wrote "No source of this family was ever published" for every binary
family and an "Earlier sources" heading without its list. The opening now depends on what the
plan's earlier_sources are (fonts only / an import of the release / designer sources that do
not rebuild it), and the list is written. The converter link the README already cites is kept.

Usage: FAMILIES=<table> readme_fix.py <repo>...   commits in each landed clone (land.OUT/<repo>)
on its current branch; never pushes. Prints the diff stat, or "unchanged".
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import land  # noqa: E402

for repo in sys.argv[1:]:
    rows = land.family_rows(repo)
    if rows[0]["kind"] != "binary" or land.legacy_src(rows, []):
        sys.exit("FATAL: %s is not a binary-route repository" % repo)
    d = os.path.join(land.OUT, repo)
    path = os.path.join(d, "README.md")
    text = open(path, encoding="utf-8").read()
    plan = land.load_plan(repo)
    m = re.search(r"\[babelfont-rs\]\((https://[^)]+)\)", text)
    head = re.match(r"(# [^\n]*\n\n)(.*?)(\nHow these sources were checked)", text, re.S)
    if not head:
        sys.exit("FATAL: %s: README does not start as land.py writes it" % repo)
    new = head.group(1) + land.binary_opening(plan, m.group(1) if m else None) + text[head.start(3):]
    section = land.earlier_section(rows, plan)
    old = re.search(r"\n## Earlier sources\n.*?(?=\n## |\Z)", new, re.S)
    if old:
        new = new[:old.start()] + section.rstrip("\n") + "\n" + new[old.end():]
    elif section:
        at = re.search(r"\n## (Known differences|Original README|TrueType hinting)", new)
        new = (new[:at.start()] + section + new[at.start():]) if at else new + section
    if new == text:
        print("%s: unchanged" % repo)
        continue
    open(path, "w", encoding="utf-8").write(new)
    land.commit(d, "README: say what the earlier sources are, and list them\n\n"
                   "The README said no source of the family was ever published, and its\n"
                   "Earlier sources section had no list (tools/land.py before 2026-11-20).",
                "README.md")
    print("%s: %s" % (repo, subprocess.run(["git", "-C", d, "show", "--stat", "--format=%h", "HEAD"],
                                            capture_output=True, text=True).stdout.split("\n")[0]))
