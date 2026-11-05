#!/usr/bin/env python3
"""Question answered: is a google/fonts branch written by tools/metadata.py right to submit?

Checks every commit between the base (upstream/main by default) and the branch HEAD:
  1. it touches exactly <lic>/<family>/METADATA.pb and upstream_info.md, one family;
  2. METADATA.pb parses (gftools' fonts_public_pb2) and its source block names
     https://github.com/googlefonts/<repo>, its DEFAULT branch on GitHub, and a commit on
     that branch as GitHub publishes it (fetched; never a pull request's branch);
  3. every files {} dest_file is a file google/fonts ships in that family's directory,
     and the license source_file is in the repository at that commit;
  4. with --build: the repository at that commit, built by the same gftools-builder as
     tools/land.py, produces exactly the fonts/ttf/ files the source block maps, and each
     passes tools/functional_gate.py (all eight checks, hinting included) against the font
     this google/fonts commit ships as its dest_file (ALLOW_DISCLOSED=1: a difference the
     plan's "accepted" list states word for word is reported, not failed);
  5. the upstream_info.md text this branch adds (everything above "## Previous
     investigation") is ASCII, names no workstation path, and every commit id and
     github.com URL in it is public (tools/public_refs.py's mirrors; run --fetch once).

Usage: verify_metadata.py [--build] [--fetch] <google/fonts worktree> [<base ref>]
Exit 1 if anything fails.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land  # noqa: E402
import public_refs  # noqa: E402
import functional_gate  # noqa: E402
import check_publishable  # noqa: E402
from google.protobuf import text_format  # noqa: E402
from gftools import fonts_public_pb2  # noqa: E402


def git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True).stdout


def added_text(info):
    return info.split("## Previous investigation")[0]


def check_commit(wt, sha, build):
    problems = []
    files = git(wt, "show", "--format=", "--name-only", sha).split()
    dirs = {os.path.dirname(f) for f in files}
    names = sorted(os.path.basename(f) for f in files)
    if len(dirs) != 1 or names != ["METADATA.pb", "upstream_info.md"]:
        return "?", ["touches %s" % ", ".join(files)]
    fam_dir = dirs.pop()
    md = fonts_public_pb2.FamilyProto()
    try:
        text_format.Parse(git(wt, "show", "%s:%s/METADATA.pb" % (sha, fam_dir)), md)
    except text_format.ParseError as e:
        return fam_dir, ["METADATA.pb does not parse: %s" % e]
    src = md.source
    m = re.match(r"https://github\.com/googlefonts/([\w.-]+)$", src.repository_url)
    if not m:
        return fam_dir, ["repository_url %r is not a googlefonts repository" % src.repository_url]
    repo = m.group(1)
    local = os.path.join(land.OUT, repo)
    # standing rule (Felipe, 2026-11-04): the commit is on the repository's DEFAULT branch
    # as GitHub publishes it, never on a pull request's branch
    head = subprocess.run(["git", "ls-remote", "--symref", src.repository_url, "HEAD"],
                          capture_output=True, text=True).stdout
    default = re.search(r"^ref: refs/heads/(\S+)\tHEAD$", head, re.M)
    if not default:
        problems.append("cannot read the default branch of %s" % src.repository_url)
    elif src.branch != default.group(1):
        problems.append("branch %r is not %s's default branch %r" % (src.branch, repo, default.group(1)))
    ref = "refs/published/" + src.branch
    fetched = subprocess.run(["git", "-C", local, "fetch", "-q", src.repository_url + ".git",
                              "+refs/heads/%s:%s" % (src.branch, ref)], capture_output=True, text=True)
    if fetched.returncode:
        problems.append("branch %r is not on %s" % (src.branch, src.repository_url))
    elif subprocess.run(["git", "-C", local, "merge-base", "--is-ancestor", src.commit, ref]).returncode:
        problems.append("commit %s is not on %s %s (%s)" % (src.commit[:12], repo, src.branch,
                                                            git(local, "rev-parse", "--short", ref).strip()))
    shipped = set(git(wt, "ls-tree", "--name-only", sha, fam_dir + "/").split())
    mapped = []
    for f in src.files:
        if fam_dir + "/" + f.dest_file not in shipped:
            problems.append("dest_file %s is not in %s" % (f.dest_file, fam_dir))
        if f.source_file.startswith("fonts/ttf/"):
            mapped.append(os.path.basename(f.source_file))
        elif subprocess.run(["git", "-C", local, "cat-file", "-e", "%s:%s" % (src.commit, f.source_file)],
                            capture_output=True).returncode:
            problems.append("source_file %s is not in %s at %s" % (f.source_file, repo, src.commit[:12]))
    if src.config_yaml and subprocess.run(["git", "-C", local, "cat-file", "-e", "%s:%s" % (
            src.commit, src.config_yaml)], capture_output=True).returncode:
        problems.append("config_yaml %s is not in %s at %s" % (src.config_yaml, repo, src.commit[:12]))
    if build:
        scratch = tempfile.mkdtemp(prefix="verify-metadata-%s-" % repo, dir=land.SCRATCH)
        try:
            subprocess.run("git -C %s archive %s sources | tar -x -C %s" % (local, src.commit, scratch),
                           shell=True, check=True)
            subprocess.run([land.B3, src.config_yaml], cwd=scratch, capture_output=True)
            ttf = os.path.join(scratch, "fonts", "ttf")
            built = sorted(os.listdir(ttf)) if os.path.isdir(ttf) else []
            if sorted(mapped) != built:
                problems.append("build produces %s, the source block maps %s" % (built, sorted(mapped)))
            accepted = land.load_plan(repo).get("accepted", []) if os.environ.get("ALLOW_DISCLOSED") else []
            for f in src.files:
                name = os.path.basename(f.source_file)
                if not f.source_file.startswith("fonts/ttf/") or name not in built:
                    continue
                shipped_font = os.path.join(scratch, "shipped-" + f.dest_file)
                with open(shipped_font, "wb") as fh:
                    fh.write(subprocess.run(["git", "-C", wt, "show", "%s:%s/%s" % (sha, fam_dir, f.dest_file)],
                                            capture_output=True, check=True).stdout)
                style = os.path.splitext(f.dest_file)[0]
                res = functional_gate.run(shipped_font, os.path.join(ttf, name), style, workdir=scratch)
                for check in functional_gate.failed_checks(res):
                    c = res["checks"][check]
                    if {"style": style, "check": check, "summary": c["summary"]} in accepted:
                        continue
                    problems.append("%s: functional_gate %s FAIL: %s" % (
                        f.dest_file, check, (c["failures"] or [c["summary"]])[0][:200]))
        finally:
            if os.path.dirname(scratch) == land.SCRATCH and os.path.basename(scratch).startswith("verify-metadata-"):
                shutil.rmtree(scratch)
    text = added_text(git(wt, "show", "%s:%s/upstream_info.md" % (sha, fam_dir)))
    if any(ord(c) > 127 for c in text):
        problems.append("upstream_info.md: non-ASCII in the added text")
    if public_refs.LOCAL.search(text):
        problems.append("upstream_info.md: workstation path %s" % public_refs.LOCAL.search(text).group(0))
    def is_ancestor(repo_dir, h, ref):
        return subprocess.run(["git", "-C", repo_dir, "merge-base", "--is-ancestor", h, ref],
                              capture_output=True).returncode == 0

    for h in set(public_refs.HEX.findall(text)):
        if not (re.search("[a-f]", h) and re.search("[0-9]", h)):
            continue
        # the family's own repository on GitHub, the evidence repository as published,
        # then the tool and google/fonts mirrors public_refs.py knows
        if not fetched.returncode and is_ancestor(local, h, ref):
            continue
        if is_ancestor(public_refs.W, h, "refs/published/main"):
            continue
        if any(public_refs.published(r, rem, b, h) for r, rem, b in public_refs.MIRRORS):
            continue
        # a repository the text names beside the id (an earlier copy, the replaced source
        # block): its repo-archive mirror's default branch, else GitHub serving the commit,
        # as check_publishable.py resolves it
        if check_publishable.in_archive(h, text) or check_publishable.served_by_github(h, text)[0]:
            continue
        problems.append("upstream_info.md: %s is not a commit on any published branch we know" % h)
    for u in set(public_refs.URL.findall(text)):
        u = u.rstrip(".,;:`")
        code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-w", "%{http_code}", "-I", u],
                              capture_output=True, text=True).stdout
        if code != "200":
            problems.append("upstream_info.md: %s answers %s" % (u, code or "nothing"))
    return fam_dir, problems


def main():
    args = sys.argv[1:]
    build = "--build" in args
    if "--fetch" in args:
        public_refs.refresh()
    args = [a for a in args if not a.startswith("--")]
    wt, base = args[0], args[1] if len(args) > 1 else "upstream/main"
    bad = 0
    shas = git(wt, "rev-list", "--reverse", "%s..HEAD" % base).split()
    for sha in shas:
        fam_dir, problems = check_commit(wt, sha, build)
        print("%-10s %-28s %s" % (sha[:9], fam_dir, "OK" if not problems else "FAIL"))
        for p in problems:
            print("    " + p)
        bad += bool(problems)
    print("%d commits, %d failing" % (len(shas), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
