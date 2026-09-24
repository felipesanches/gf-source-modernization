#!/usr/bin/env python3
"""Split one commit's diff of babelfont/src/convertors/fontforge.rs into
code hunks (before the old `mod tests {`) and test hunks (inside it).

Usage: split_hunks.py <repo> <commit> <outdir>
Writes <outdir>/<commit>.code.patch (a git-apply-able patch of the code hunks)
and <outdir>/<commit>.tests.rs (the added lines of every test hunk, dedented by
four spaces, in order, separated by a marker comment giving the old context).
"""
import os, re, subprocess, sys

repo, commit, outdir = sys.argv[1:4]
path = "babelfont/src/convertors/fontforge.rs"
parent = subprocess.check_output(["git", "-C", repo, "show", f"{commit}^:{path}"], text=True)
tests_start = None
for i, line in enumerate(parent.splitlines(), 1):
    if line.startswith("mod tests {"):
        tests_start = i
diff = subprocess.check_output(["git", "-C", repo, "diff", f"{commit}^", commit, "--", path], text=True)
lines = diff.splitlines(keepends=True)
header, hunks, cur = [], [], None
for l in lines:
    if l.startswith("@@"):
        cur = [l]; hunks.append(cur)
    elif cur is None:
        header.append(l)
    else:
        cur.append(l)
code, tests = [], []
for h in hunks:
    m = re.match(r"@@ -(\d+)", h[0])
    old = int(m.group(1))
    (tests if tests_start and old >= tests_start else code).append(h)
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, f"{commit}.code.patch"), "w") as f:
    if code:
        f.writelines(header)
        for h in code:
            f.writelines(h)
with open(os.path.join(outdir, f"{commit}.tests.rs"), "w") as f:
    for h in tests:
        f.write(f"// ==== hunk {h[0].strip()}\n")
        ctx = [l[1:] for l in h[1:] if l.startswith(" ")][:3]
        for c in ctx:
            f.write("// ctx: " + c.rstrip("\n")[4:] + "\n")
        for l in h[1:]:
            if l.startswith("-"):
                f.write("// REMOVED: " + l[1:])
            elif l.startswith("+"):
                body = l[1:]
                f.write(body[4:] if body.startswith("    ") else body)
print(f"tests_start={tests_start} code_hunks={len(code)} test_hunks={len(tests)}")
