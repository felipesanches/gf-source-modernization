#!/usr/bin/env python3
"""Point google/fonts at a landed repository: one commit per family.

Question answered: what exactly must change in google/fonts so a family's
recorded upstream is the repository just landed? The METADATA.pb `source {}` block
(repository, the convert commit, the build config, and the file mapping from what
the repository builds to what google/fonts ships), plus an upstream_info.md that
records what was done -- the older repository preserved in full, per the
preserve-old-repos policy.

The mapping is measured, not assumed: each style's built file name comes from the
converted .glyphs, and its destination is the file google/fonts already ships
(NovaCut builds NovaCut-Regular.ttf, google/fonts ships NovaCut.ttf).

Writes into a google/fonts worktree on its own branch; never pushes. The commits
are only meaningful once the repositories are pushed: every hash they cite must
exist on GitHub first.

Usage: metadata.py <branch> <repo>...
"""
import os
import re
import subprocess
import sys
import functools
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land  # noqa: E402

GF = land.GF
# never break a file or flag name at its hyphen
wrap = functools.partial(textwrap.wrap, break_on_hyphens=False, break_long_words=False)
WT_ROOT = "/home/fsanches/compartilhado/google/fonts-worktrees"


def git(d, *a, check=True, input=None):
    r = subprocess.run(["git", "-C", d, *land.IDENT, *a], capture_output=True, text=True, input=input)
    if check and r.returncode:
        raise SystemExit("FATAL git %s: %s" % (" ".join(a), r.stderr))
    return r.stdout


def worktree(branch):
    wt = os.path.join(WT_ROOT, branch)
    if not os.path.isdir(wt):
        git(GF, "fetch", "-q", "upstream", "main")
        git(GF, "worktree", "add", "-q", "-b", branch, wt, "upstream/main")
    return wt


def source_block(repo, rows, head_full, branch):
    d = os.path.join(land.OUT, repo)
    lines = ["source {", '  repository_url: "https://github.com/googlefonts/%s"' % repo,
             '  commit: "%s"' % head_full,
             "  files {", '    source_file: "OFL.txt"', '    dest_file: "OFL.txt"', "  }"]
    for r in rows:
        g = os.path.join(d, "sources", r["style"] + ".glyphs")
        built = land.built_name(g)
        lines += ["  files {", '    source_file: "fonts/ttf/%s"' % built,
                  '    dest_file: "%s"' % os.path.basename(r["shipped"]), "  }"]
    lines += ['  branch: "%s"' % branch, '  config_yaml: "sources/config.yaml"', "}"]
    return "\n".join(lines) + "\n"


def replace_source(text, block):
    m = re.search(r"^source \{\n.*?^\}\n", text, re.S | re.M)
    if m:
        return text[:m.start()] + block + text[m.end():], m.group(0)
    return text.rstrip("\n") + "\n" + block, None


def upstream_info(repo, rows, old_block, head_full, display, previous, future):
    kind, base, commit = rows[0]["kind"], rows[0]["base"], rows[0]["commit"]
    d = os.path.join(land.OUT, repo)
    convert = git(d, "log", "-1", "--format=%B", head_full)
    claim = re.search(r"^(Builds with .*?)(?:\n\n|\Z)", convert, re.S | re.M)
    claim = " ".join(claim.group(1).split()) if claim else ""
    if kind == "hg":
        origin = ("the family's directory in the googlefontdirectory-hg monorepo "
                  "(https://github.com/%s, `%s/%s` at commit `%s`); it had no repository "
                  "of its own" % (base, rows[0]["lic"], rows[0]["family"], commit))
    else:
        origin = "https://github.com/%s at commit `%s`" % (base, commit)
    edits = edit_subjects(d, rows)
    out = ["# %s" % display, ""]
    out += wrap("Sources modernized 2026-09: the FontForge `.sfd` sources were converted to "
                         "Glyphs (`.glyphs`) and build with gftools-builder and fontc. The "
                         "repository, commit and config are in the `source { }` block of "
                         "METADATA.pb.", 88)
    out += ["", "## Initial state", ""]
    out += wrap("Google Fonts shipped %s built from FontForge `.sfd` sources in %s. There "
                         "was no source that builds with fontc." % (display, origin), 88)
    out += ["", "## Actions taken", ""]
    first = ("The family's files were imported unmodified as the first commit of "
             "https://github.com/googlefonts/%s." % repo if kind == "hg" else
             "The work was done on top of the upstream history, in https://github.com/googlefonts/%s." % repo)
    out += wrap("- " + first, 88, subsequent_indent="  ")
    if edits:
        out += wrap("- Each change to the `.sfd` before conversion is its own commit: "
                             + "; ".join(edits) + ".", 88, subsequent_indent="  ")
    else:
        out += ["- The `.sfd` needed no change: it was converted exactly as the designer left it."]
    out += wrap("- The `.sfd` was converted with babelfont-rs, using only filters that "
                         "reproduce FontForge's own export, as the last commit.", 88,
                         subsequent_indent="  ")
    out += ["", "## Final state", ""]
    out += wrap("The source is https://github.com/googlefonts/%s at `%s`. %s"
                         % (repo, head_full[:12], claim), 88)
    out += [""]
    out += wrap("`%s` is the equivalence commit: its build is functionally equivalent "
                         "to the binaries Google Fonts ships. Source modernization adds no "
                         "features. Where the shipped binaries differ from the source, the "
                         "difference is reproduced by a documented commit before the "
                         "conversion, never silently corrected. Any improvement is a later "
                         "commit that needs its own QA, and is left as future work for an "
                         "onboarder to review in a font-update PR." % head_full[:12], 88)
    later = later_subjects(d, head_full)
    if later or future:
        out += ["", "## Future work", ""]
        out += wrap("Not part of what Google Fonts ships; for review in a font-update "
                             "PR:", 88)
        for l in later:
            out += wrap("- commit `%s` (after the equivalence commit): %s"
                                 % (l.split(" ", 1)[0], l.split(" ", 1)[1]), 88,
                                 subsequent_indent="  ")
        for f in future:
            out += wrap("- " + f, 88, subsequent_indent="  ")
    if old_block:
        out += ["", "## Original repository (dormant)", ""]
        out += wrap("The source block this replaces, preserved for provenance:", 88)
        out += [""] + ["    " + l for l in old_block.rstrip("\n").splitlines()]
    if previous.strip():
        # never discard an earlier investigation: carried forward, one heading level down
        out += ["", "## Previous investigation", ""]
        for l in previous.rstrip("\n").splitlines():
            out.append("#" + l if l.startswith("#") else l)
    return "\n".join(out) + "\n"


def equivalence_commit(d):
    """The commit METADATA.pb records: the conversion, whose build is functionally
    equivalent to the binaries google/fonts ships. Anything after it is an improvement,
    left for an onboarder's font-update PR."""
    for line in git(d, "log", "--format=%H %s").splitlines():
        h, subject = line.split(" ", 1)
        if subject.startswith("Convert to .glyphs with babelfont "):
            return h
    raise SystemExit("FATAL: %s has no conversion commit" % d)


def later_subjects(d, equiv):
    return [l for l in git(d, "log", "--reverse", "--format=%h %s", "%s..HEAD" % equiv).splitlines() if l]


def own_subjects(d, rows):
    """Subjects of the commits this work added -- never the upstream's own history."""
    kind = rows[0]["kind"]
    rng = ("HEAD" if kind == "hg" else "master..HEAD" if kind == "allerta"
           else "%s..HEAD" % rows[0]["commit"])
    return git(d, "log", "--reverse", "--format=%s", rng).splitlines()


def edit_subjects(d, rows):
    return [s for s in own_subjects(d, rows) if s != "Adopt the Unified Font Repository template"
            and not s.startswith(("Import ", "Convert to .glyphs", "Restore "))]


def edits_in(d, rows):
    return len(edit_subjects(d, rows))


def main():
    branch, repos = sys.argv[1], sys.argv[2:]
    wt = worktree(branch)
    landed = {}
    for line in open(os.path.join(land.W, "landed.tsv")):
        cols = line.rstrip("\n").split("\t")
        landed[cols[0]] = cols
    for repo in repos:
        if landed.get(repo, [None] * 5)[4] != "CLEAN":
            raise SystemExit("FATAL: %s is not landed CLEAN; its metadata would overclaim" % repo)
        rows = land.family_rows(repo)
        if git(os.path.join(land.OUT, repo), "rev-parse", "--short", "HEAD").strip() != landed[repo][2]:
            raise SystemExit("FATAL: %s HEAD is not the landed commit %s" % (repo, landed[repo][2]))
        d = os.path.join(land.OUT, repo)
        head_full = equivalence_commit(d)      # recorded; later commits are future work
        future = land.load_plan(repo).get("future_work", [])
        # the branch the commit lives on once published: `main` for a fresh repository;
        # `master` for a fork or an extended repository, AFTER its pull request is
        # MERGED -- a squash merge would give the commit a new hash and orphan this one
        rbranch = "main" if rows[0]["kind"] == "hg" else "master"
        fam, lic = rows[0]["family"], rows[0]["lic"]
        mp = os.path.join(wt, lic, fam, "METADATA.pb")
        text = open(mp, encoding="utf-8").read()
        display = re.search(r'^name: "(.*)"', text, re.M).group(1)
        block = source_block(repo, rows, head_full, rbranch)
        new, old = replace_source(text, block)
        open(mp, "w", encoding="utf-8").write(new)
        ui = os.path.join(wt, lic, fam, "upstream_info.md")
        previous = open(ui, encoding="utf-8").read() if os.path.exists(ui) else ""
        body = upstream_info(repo, rows, old, head_full, display, previous, future)
        if any(ord(c) > 127 for c in body) and not any(ord(c) > 127 for c in previous):
            raise SystemExit("FATAL: non-ASCII introduced into upstream_info.md for %s" % fam)
        open(ui, "w", encoding="utf-8").write(body)
        git(wt, "add", "--", os.path.relpath(mp, wt), os.path.relpath(ui, wt))
        msg = ("%s: reference the googlefonts/%s .glyphs source\n\n"
               "Repo: https://github.com/googlefonts/%s\nCommit: %s\nConfig: sources/config.yaml\n"
               "Status: %s; builds with gftools-builder and fontc\n"
               "Confidence: high -- 0 blocking rows against the shipped binaries\n\n"
               "Assisted by an AI agent (Claude Opus 5.5)\n"
               % (display, repo, repo, head_full[:12],
                  "converted from the unmodified .sfd" if not edits_in(d, rows) else
                  "converted from the .sfd after %d documented edit(s)" % edits_in(d, rows)))
        git(wt, "commit", "-q", "-F", "-", input=msg)
        print("%s: %s" % (fam, git(wt, "rev-parse", "--short", "HEAD").strip()))


if __name__ == "__main__":
    main()
