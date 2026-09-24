#!/usr/bin/env python3
"""Question answered: does babelfont built from PR #90 plus the three FontForge PR
branches (pr-ff-reader-fixes, pr-ff-source-fidelity, pr-ff-os2-defaults, merged
together as branch integration-ff-prs) convert every FontForge source in this batch
to EXACTLY the same .glyphs as the babelfont the repositories were landed with
(gf-sfd-conversion 8b59bc3)? If yes, re-landing once those PRs are merged upstream
changes nothing but the babelfont revision the convert commit cites.

Signal: `cmp`-style byte equality of the .glyphs each binary writes. A style whose
conversion fails on one binary and not the other is a FAILURE, not a difference.

Three checks, all conversion only (no compile):

  1. original  -- every style of families.tsv (42), its UNMODIFIED .sfd from the repo
                  archive (recipe.source_text), flags from recipe.flags_for. The
                  reference binary is also run twice, as a determinism control: a
                  difference only means something if the reference agrees with itself.
  2. landed    -- every style whose repository exists in ../sfd-reland-repos/<repo>:
                  the .sfd as committed right BEFORE its "Convert to .glyphs with
                  babelfont" commit (so the documented .sfd edits of plans/*.json are
                  included), same flags, both binaries.
  3. committed -- the candidate's check-2 output after tools/workarounds.py, compared
                  with the .glyphs the convert commit actually holds
                  (<convert>:sources/<Style>.glyphs). The reference is checked the same
                  way, so drift in the landed repository itself is told apart from a
                  change the candidate introduces.

Inputs:
  reference  /home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/
             target-heights/release/babelfont  (BUILT_FROM: 8b59bc3)
  candidate  /home/fsanches/compartilhado/babelfont-rs-worktrees/target-integration/
             release/babelfont  (integration-ff-prs (see RESULT.txt for the candidate binary), built with
             `cargo build --release -p babelfont --features cli`; the bin target has
             required-features = ["cli"])
  invocation `babelfont <in.sfd> <out.glyphs> <flags...>`, as tools/land.py does.

Usage (from sfd-reland/):
  /home/fsanches/compartilhado/gftools/venv/bin/python3 \\
      tools/probes/upstream_prs_equivalence/run.py [--ref BIN] [--cand BIN] \\
      > tools/probes/upstream_prs_equivalence/RESULT.txt

Exit status 0 when every check is byte-identical and no conversion failed on only
one binary; 1 otherwise.

Negative control (the probe does detect a change): the same run with
  --cand /home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target/release/babelfont
(an earlier gf-sfd-conversion build, Sep 23 20:27, commit not stamped, without
--fontforge-height-glyph-count-mean) reports 33 one-binary failures and 7 differing
styles in check 1; its output is NEGATIVE_CONTROL.txt.
"""
import argparse
import difflib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "..")
sys.path.insert(0, TOOLS)
import recipe  # noqa: E402
import workarounds  # noqa: E402

BFW = "/home/fsanches/compartilhado/babelfont-rs-worktrees"
REF = os.path.join(BFW, "gf-sfd-conversion/target-heights/release/babelfont")
CAND = os.path.join(BFW, "target-integration/release/babelfont")
REPOS = "/home/fsanches/compartilhado/sfd-reland-repos"
DIFF_LINES = 40


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def convert(binary, src, out, flags):
    """Run one conversion. Returns (ok, message)."""
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([binary, src, out] + flags, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
        return False, "exit %d: %s" % (r.returncode, " | ".join(tail))
    return True, ""


def short_diff(a, b, label_a, label_b):
    la = open(a, encoding="utf-8", errors="replace").read().splitlines()
    lb = open(b, encoding="utf-8", errors="replace").read().splitlines()
    d = list(difflib.unified_diff(la, lb, label_a, label_b, lineterm="", n=1))
    changed = sum(1 for x in d if x[:1] in "+-" and not x.startswith(("+++", "---")))
    out = d[:DIFF_LINES]
    if len(d) > DIFF_LINES:
        out.append("... (%d more diff lines)" % (len(d) - DIFF_LINES))
    return changed, ["      " + x for x in out]


def same(a, b):
    return open(a, "rb").read() == open(b, "rb").read()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)


def convert_commit(repo_dir):
    r = git(repo_dir, "log", "--format=%H %s", "--grep=^Convert to .glyphs with babelfont")
    lines = r.stdout.decode().strip().splitlines()
    return lines[0].split(" ", 1) if lines else (None, None)


def compare_pair(tag, style, src, flags, ref, cand, tmp, counts, failures, differences,
                 control=False):
    """Convert src with both binaries, compare. Returns (ref_out, cand_out) or None."""
    ro = os.path.join(tmp, "%s.%s.ref.glyphs" % (style, tag))
    co = os.path.join(tmp, "%s.%s.cand.glyphs" % (style, tag))
    rok, rmsg = convert(ref, src, ro, flags)
    cok, cmsg = convert(cand, src, co, flags)
    if control and rok:
        ro2 = os.path.join(tmp, "%s.%s.ref2.glyphs" % (style, tag))
        ok2, _ = convert(ref, src, ro2, flags)
        if not ok2 or not same(ro, ro2):
            counts["nondeterministic"] += 1
            print("  %-28s REFERENCE NOT DETERMINISTIC" % style)
    if not rok and not cok:
        counts["both_failed"] += 1
        print("  %-28s both failed  ref: %s  cand: %s" % (style, rmsg, cmsg))
        return None
    if rok != cok:
        counts["failed"] += 1
        failures.append((tag, style, "reference" if not rok else "candidate",
                         rmsg if not rok else cmsg))
        print("  %-28s FAILURE: %s failed (%s)" % (style, "reference" if not rok else
                                                     "candidate", rmsg or cmsg))
        return None
    if same(ro, co):
        counts["identical"] += 1
        print("  %-28s identical  sha256:%s  %d bytes" % (style, sha(ro), os.path.getsize(ro)))
    else:
        counts["differ"] += 1
        n, lines = short_diff(ro, co, "reference/%s.glyphs" % style, "candidate/%s.glyphs" % style)
        differences.append((tag, style))
        print("  %-28s DIFFERS  (%d changed lines)" % (style, n))
        print("\n".join(lines))
    return ro, co


def new_counts():
    return {"identical": 0, "differ": 0, "failed": 0, "both_failed": 0, "nondeterministic": 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--cand", default=CAND)
    a = ap.parse_args()

    rows = recipe.rows()
    print("reference  %s  (%d bytes, sha256:%s)" % (a.ref, os.path.getsize(a.ref), sha(a.ref)))
    built = os.path.join(os.path.dirname(os.path.dirname(a.ref)), "BUILT_FROM")
    if os.path.exists(built):
        print("           BUILT_FROM %s" % open(built).read().strip())
    print("candidate  %s  (%d bytes, sha256:%s)" % (a.cand, os.path.getsize(a.cand), sha(a.cand)))
    print("styles     %d (families.tsv)" % len(rows))
    print()

    failures, differences = [], []
    summary = {}
    tmp = tempfile.mkdtemp(prefix="upstream_prs_equivalence.")
    try:
        # 1. original -------------------------------------------------------------
        print("== 1. original: unmodified .sfd from the repo archive, recipe flags")
        c = new_counts()
        for row in rows:
            src = os.path.join(tmp, row["style"] + ".orig.sfd")
            with open(src, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(recipe.source_text(row))
            flags = recipe.flags_for(open(src, encoding="utf-8", errors="replace").read(),
                                     row["shipped"])
            compare_pair("original", row["style"], src, flags, a.ref, a.cand, tmp, c,
                         failures, differences, control=True)
        summary["1. original"] = (len(rows), c)
        print()

        # 2. landed + 3. committed ----------------------------------------------
        print("== 2. landed: the .sfd committed just before each convert commit")
        c2, c3 = new_counts(), new_counts()
        committed_lines = []
        n2 = 0
        for row in rows:
            repo_dir = os.path.join(REPOS, row["repo"])
            if not os.path.isdir(os.path.join(repo_dir, ".git")):
                continue
            sha_c, subject = convert_commit(repo_dir)
            if sha_c is None:
                print("  %-28s no convert commit in %s" % (row["style"], repo_dir))
                continue
            n2 += 1
            src = os.path.join(tmp, row["style"] + ".landed.sfd")
            with open(src, "wb") as fh:
                fh.write(git(repo_dir, "show", "%s^:%s" % (sha_c, row["source"])).stdout)
            text = open(src, encoding="utf-8", errors="replace").read()
            flags = recipe.flags_for(text, row["shipped"])
            pair = compare_pair("landed", row["style"], src, flags, a.ref, a.cand, tmp, c2,
                                failures, differences)
            if pair is None:
                continue
            committed = os.path.join(tmp, row["style"] + ".committed.glyphs")
            with open(committed, "wb") as fh:
                fh.write(git(repo_dir, "show", "%s:sources/%s.glyphs"
                             % (sha_c, row["style"])).stdout)
            verdict = []
            for who, out in (("ref", pair[0]), ("cand", pair[1])):
                w = os.path.join(tmp, "%s.%s.worked.glyphs" % (row["style"], who))
                shutil.copy(out, w)
                with open(os.devnull, "w") as devnull:
                    stdout, sys.stdout = sys.stdout, devnull
                    try:
                        workarounds.apply_all(w, src)
                    finally:
                        sys.stdout = stdout
                verdict.append((who, same(w, committed), w))
            ref_ok, cand_ok = verdict[0][1], verdict[1][1]
            if cand_ok:
                c3["identical"] += 1
            else:
                c3["differ"] += 1
                differences.append(("committed", row["style"]))
            committed_lines.append("  %-28s %s %s  ref%s  cand%s" % (
                row["style"], row["repo"], sha_c[:7], "=" if ref_ok else "!=",
                "=" if cand_ok else "!="))
            if not cand_ok:
                n, lines = short_diff(committed, verdict[1][2],
                                      "%s@%s:sources/%s.glyphs" % (row["repo"], sha_c[:7],
                                                                   row["style"]),
                                      "candidate+workarounds")
                committed_lines.append("      (%d changed lines)" % n)
                committed_lines += lines
        summary["2. landed"] = (n2, c2)
        summary["3. committed"] = (n2 - c2["failed"] - c2["both_failed"], c3)
        print()
        print("== 3. committed: candidate (+ workarounds.py) vs the .glyphs in the convert "
              "commit; ref shown as control")
        print("\n".join(committed_lines))
        print()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("== summary")
    for name, (n, c) in summary.items():
        print("  %-13s %2d styles: %d identical, %d differ, %d FAILED on one binary, "
              "%d failed on both%s" % (name, n, c["identical"], c["differ"], c["failed"],
                                       c["both_failed"],
                                       ", %d reference non-deterministic" % c["nondeterministic"]
                                       if name.startswith("1") else ""))
    print("  failures (one binary only): %s" % (
        "; ".join("%s %s: %s failed (%s)" % f for f in failures) or "none"))
    print("  differences: %s" % (", ".join("%s/%s" % d for d in differences) or "none"))
    ok = not failures and not differences
    print("  VERDICT: %s" % ("EQUIVALENT -- re-landing changes only the cited babelfont revision"
                            if ok else "NOT EQUIVALENT -- see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
