#!/usr/bin/env python3
"""Which genuine FontForge original does each babelfont branch improve?

Reads the per-branch land.py logs written by run.sh (<scratch>/logs-<branch>/<repo>.log) and
prints, per branch and repo, every functional-gate line (check status + detail lines) and the
per-style BLOCKING count that differs from u0 (Simon's main alone). A branch with no output is
not needed by any of the six originals.

    python3 compare_need.py /home/fsanches/compartilhado/tmp/bf-pr-need-2026-11-08
"""
import re
import sys
from pathlib import Path

S = Path(sys.argv[1])
REPOS = "comicrelief thabit lohitbengali lohittamil kristi novamono".split()


def parse(path):
    """Return {(style, check): [lines]} and {style: blocking} from one log."""
    out, blocking = {}, {}
    text = path.read_text(errors="replace").splitlines()
    head = text[0] if text else ""
    styles = re.findall(r"([A-Za-z0-9-]+)=(\d+) functional=", head)
    for st, n in styles:
        blocking[st] = int(n)
    style_idx, cur, seen = 0, None, set()
    for line in text[1:]:
        m = re.match(r"^     (\w+)\s+(PASS|FAIL|SKIP|WARN)\s*(.*)$", line)
        if m:
            check = m.group(1)
            if check in seen:  # a new style block starts when a check repeats
                style_idx += 1
                seen = set()
            seen.add(check)
            st = styles[style_idx][0] if style_idx < len(styles) else f"#{style_idx}"
            cur = (st, check)
            out[cur] = [f"{m.group(2)} {m.group(3)}"]
        elif line.startswith("         - ") and cur:
            out[cur].append(line.strip())
    return out, blocking


def main():
    branches = sorted(p.name[5:] for p in S.glob("logs-*") if p.is_dir())
    base = {r: parse(S / "logs-u0" / f"{r}.log") for r in REPOS}
    for b in branches:
        if b == "u0":
            continue
        print(f"== {b}")
        if not any((S / f"logs-{b}").glob("*.log")):
            print("  NOT MEASURED (no landing logs: the merge or the build failed, see progress.txt)")
            continue
        any_diff = False
        for r in REPOS:
            if not (S / f"logs-{b}" / f"{r}.log").exists():  # a combined run on a subset
                continue
            lines, blk = parse(S / f"logs-{b}" / f"{r}.log")
            blines, bblk = base[r]
            for st in sorted(set(blk) | set(bblk)):
                if blk.get(st) != bblk.get(st):
                    print(f"  {r} {st} BLOCKING {bblk.get(st)} -> {blk.get(st)}")
                    any_diff = True
            for k in sorted(set(lines) | set(blines)):
                if lines.get(k) != blines.get(k):
                    any_diff = True
                    print(f"  {r} {k[0]} {k[1]}:")
                    print(f"    u0:  {' | '.join(blines.get(k, ['-']))}")
                    print(f"    {b}: {' | '.join(lines.get(k, ['-']))}")
        if not any_diff:
            print("  no difference from u0 on any of the six originals")


main()
