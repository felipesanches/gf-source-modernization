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

A repository of kind `glyphs` (the designer's .glyphs is built as is, tools/land.py)
records its config commit, "Add a gftools-builder config for <source>", instead of a
conversion; each style is an instance of that one file, built as <style>.ttf. Its
upstream_info.md says no conversion ran, names the builder from that commit's message,
and lists the known differences plans/<repo>.json `disclose` puts in the README.

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
import struct
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land  # noqa: E402

GF = land.GF
# never break a file or flag name at its hyphen
wrap = functools.partial(textwrap.wrap, break_on_hyphens=False, break_long_words=False)
WT_ROOT = "/home/fsanches/compartilhado/google/fonts-worktrees"
MODEL = "Claude Opus 5.5"
# the license file google/fonts ships beside each family, by license directory
LICENSE_FILE = {"ofl": "OFL.txt", "apache": "LICENSE.txt", "ufl": "UFL.txt"}
LEGACY = {".vfb": "FontLab `.vfb`", ".vfc": "FontLab `.vfc`", ".vfj": "FontLab `.vfj`",
          ".pfa": "Type 1 `.pfa`", ".pfb": "Type 1 `.pfb`"}


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


def license_file(repo, rows, head_full):
    """The license file both sides carry: google/fonts ships OFL.txt beside an OFL family
    and LICENSE.txt beside an Apache one, and the repository must have it too."""
    name = LICENSE_FILE[rows[0]["lic"]]
    if subprocess.run(["git", "-C", os.path.join(land.OUT, repo), "cat-file", "-e",
                       "%s:%s" % (head_full, name)]).returncode:
        raise SystemExit("FATAL: %s has no %s at %s" % (repo, name, head_full[:12]))
    return name


def has_fftm(path):
    """True if the font at path has an FFTM table: FontForge wrote it."""
    with open(path, "rb") as fh:
        head = fh.read(12)
        n = struct.unpack(">H", head[4:6])[0]
        tags = [fh.read(16)[:4] for _ in range(n)]
    return b"FFTM" in tags


def provenance(repo, rows, wt):
    """What says the .sfd, not another legacy format beside it, is what was shipped."""
    d = os.path.join(land.OUT, repo)
    first = git(d, "rev-list", "--max-parents=0", "HEAD").split()[0]
    exts = {os.path.splitext(f)[1].lower() for f in git(d, "ls-tree", "-r", "--name-only", first).split()}
    others = [LEGACY[e] for e in sorted(LEGACY) if e in exts]
    shipped = [os.path.join(wt, r["lic"], r["family"], os.path.basename(r["shipped"])) for r in rows]
    fftm = sum(has_fftm(p) for p in shipped)
    text = ("%s %d shipped binaries carry FontForge's `FFTM` table, so FontForge generated "
            "them." % ("All" if fftm == len(shipped) else "%d of the" % fftm, len(shipped))
            if len(shipped) > 1 else
            "The shipped binary carries FontForge's `FFTM` table, so FontForge generated it."
            if fftm else "")
    if others:
        text += (" The directory also holds %s files; the `.sfd` is taken as the master "
                 "because FontForge generated the shipped fonts and the build from the `.sfd` "
                 "is functionally equivalent to them." % " and ".join(others))
    return text.strip()


def source_block(repo, rows, head_full, branch):
    d = os.path.join(land.OUT, repo)
    lic = license_file(repo, rows, head_full)
    lines = ["source {", '  repository_url: "https://github.com/googlefonts/%s"' % repo,
             '  commit: "%s"' % head_full,
             "  files {", '    source_file: "%s"' % lic, '    dest_file: "%s"' % lic, "  }"]
    for r in rows:
        g = os.path.join(d, "sources", r["style"] + ".glyphs")
        # a `glyphs` source holds every style as an instance, built as <style>.ttf
        built = r["style"] + ".ttf" if rows[0]["kind"] == "glyphs" else land.built_name(g)
        lines += ["  files {", '    source_file: "fonts/ttf/%s"' % built,
                  '    dest_file: "%s"' % os.path.basename(r["shipped"]), "  }"]
    lines += ['  branch: "%s"' % branch, '  config_yaml: "sources/config.yaml"', "}"]
    return "\n".join(lines) + "\n"


def replace_source(text, block):
    m = re.search(r"^source \{\n.*?^\}\n", text, re.S | re.M)
    if m:
        return text[:m.start()] + block + text[m.end():], m.group(0)
    return text.rstrip("\n") + "\n" + block, None


def plural(text):
    """'1 style(s)' -> '1 style', '4 style(s)' -> '4 styles'."""
    return re.sub(r"\b(\d+) ((?:[\w-]+ )*?)(\w+)\(s\)", lambda m: "%s %s%s%s" % (
        m.group(1), m.group(2), m.group(3), "" if m.group(1) == "1" else "s"), text)


def tools_cited(message):
    """Where the convert commit says its gate tools live: the evidence repository at the
    landing's revision, and the family's plan there if it has one."""
    m = re.search(r"^Those tools(?: and this repository's plan \((plans/[\w.-]+)\))?:\s+"
                  r"(https://\S+)\s+at\s+([0-9a-f]{7,40})", message, re.M)
    if not m:
        raise SystemExit("FATAL: the convert commit does not say where its tools live")
    plan = ", including this family's plan `%s`" % m.group(1) if m.group(1) else ""
    return "Those tools%s: %s at `%s`." % (plan, m.group(2), m.group(3))


def header(display, d, head_full):
    """Title, then the model and date lines every investigation report carries; the date
    is the equivalence commit's."""
    date = git(d, "log", "-1", "--format=%cs", head_full).strip()
    return ["# %s" % display, "", "**Model**: %s" % MODEL, "**Date**: %s" % date, ""], date


def upstream_info(repo, rows, old_block, head_full, display, previous, future, wt):
    kind, base, commit = rows[0]["kind"], rows[0]["base"], rows[0]["commit"]
    if kind == "glyphs":
        return glyphs_upstream_info(repo, rows, old_block, head_full, display, previous, future)
    d = os.path.join(land.OUT, repo)
    convert = git(d, "log", "-1", "--format=%B", head_full)
    claim = re.search(r"^(Builds with .*?)(?:\n\n|\Z)", convert, re.S | re.M)
    claim = plural(" ".join(claim.group(1).split())) + " " + tools_cited(convert) if claim else ""
    if kind == "hg":
        origin = ("the family's directory in the googlefontdirectory-hg monorepo "
                  "(https://github.com/%s, `%s/%s` at commit `%s`); it had no repository "
                  "of its own" % (base, rows[0]["lic"], rows[0]["family"], commit))
    else:
        origin = "https://github.com/%s at commit `%s`" % (base, commit)
    edits = edit_subjects(d, rows)
    out, date = header(display, d, head_full)
    out += wrap("Sources modernized %s: the FontForge `.sfd` sources were converted to "
                         "Glyphs (`.glyphs`) and build with gftools-builder and fontc. The "
                         "repository, commit and config are in the `source { }` block of "
                         "METADATA.pb." % date[:7], 88)
    out += ["", "## Initial state", ""]
    out += wrap("Google Fonts shipped %s built from FontForge `.sfd` sources in %s. There "
                         "was no source that builds with fontc. %s"
                         % (display, origin, provenance(repo, rows, wt)), 88)
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


def equivalence_commit(d, rows=None):
    """The commit METADATA.pb records: the conversion, whose build is functionally
    equivalent to the binaries google/fonts ships. Anything after it is an improvement,
    left for an onboarder's font-update PR. For a `glyphs` repository, which runs no
    converter, it is the commit adding the build config."""
    if rows and rows[0]["kind"] == "glyphs":
        want = "Add a gftools-builder config for %s" % rows[0]["source"]
        for line in git(d, "log", "--format=%H %s").splitlines():
            h, subject = line.split(" ", 1)
            if subject == want:
                return h
        raise SystemExit("FATAL: %s has no commit %r" % (d, want))
    for line in git(d, "log", "--format=%H %s").splitlines():
        h, subject = line.split(" ", 1)
        if subject.startswith("Convert to .glyphs with babelfont "):
            return h
    raise SystemExit("FATAL: %s has no conversion commit" % d)


def unwrap(paragraph):
    """Join a commit message paragraph wrapped at 72 columns back into lines: the lead
    text, then one item per line indented by exactly two spaces (land.py's per-style
    results; deeper indents continue an item). land.py wraps with break_on_hyphens, so a
    line ending in a word's hyphen joins the next without a space ("glyphslib-" + "rs")."""
    items = []
    for line in paragraph.splitlines():
        if not line.strip():
            continue
        if not items or re.match(r"  \S", line):
            items.append(line.strip())
            continue
        sep = "" if re.search(r"[A-Za-z0-9]-$", items[-1]) else " "
        items[-1] += sep + line.strip()
    return items


def glyphs_upstream_info(repo, rows, old_block, head_full, display, previous, future):
    """upstream_info.md for a repository built directly from the designer's .glyphs."""
    base, commit = rows[0]["base"], rows[0]["commit"]
    src = rows[0]["source"]
    d = os.path.join(land.OUT, repo)
    config = git(d, "log", "-1", "--format=%B", head_full)
    claim = re.search(r"^(Builds with .*?)(?:\n\n|\Z)", config, re.S | re.M)
    claim = unwrap(claim.group(1)) if claim else []
    builder = re.search(r"^Builds with gftools-builder \((.*), fontc ([^)\s]+)\)",
                        claim[0]) if claim else None
    plan = land.load_plan(repo)
    out, _ = header(display, d, head_full)
    out += wrap("Source metadata updated 2026-10: the fonts are built directly from the "
                "designer's Glyphs.app source, `%s`, with gftools-builder and fontc. No "
                "conversion is involved. The repository, commit and config are in the "
                "`source { }` block of METADATA.pb." % src, 88)
    out += ["", "## Initial state", ""]
    out += wrap("Google Fonts shipped %s exported by Glyphs.app from `%s` in "
                "https://github.com/%s at commit `%s`. There was no gftools-builder "
                "config to build it with fontc." % (display, src, base, commit), 88)
    out += ["", "## Actions taken", ""]
    out += wrap("- https://github.com/googlefonts/%s carries the history of "
                "https://github.com/%s up to `%s`, unmodified." % (repo, base, commit[:12]),
                88, subsequent_indent="  ")
    out += wrap("- The Unified Font Repository template was adopted in its own commit; the "
                "README records the provenance and the known differences below.", 88,
                subsequent_indent="  ")
    out += wrap("- `%s` was not changed: no converter ran, and there are no edit commits. "
                "It is built exactly as the designer left it." % src, 88,
                subsequent_indent="  ")
    out += wrap("- `sources/config.yaml`, the gftools-builder config, was added as the last "
                "commit.", 88, subsequent_indent="  ")
    out += ["", "## Final state", ""]
    out += wrap("The source is https://github.com/googlefonts/%s at `%s`, built directly "
                "from the designer's Glyphs.app source `%s` (%s@%s), with no conversion."
                % (repo, head_full[:12], src, base, commit[:12]), 88)
    if builder:
        # the builder, then what was measured with it, as the config commit states them
        rest = claim[0][builder.end():].strip()
        rest = ("The build " + rest[4:] if rest.startswith("and ") else
                rest[2:] if rest.startswith(". ") else rest)
        out += [""] + wrap("Builder: gftools-builder (%s) with fontc %s, as the config "
                           "commit states. %s" % (builder.group(1), builder.group(2), rest), 88)
    elif claim:
        out += [""] + wrap(claim[0], 88)
    if claim[1:]:
        out += [""]
        for t in claim[1:]:
            out += wrap("- " + t, 88, subsequent_indent="  ")
    out += ["", "Files: `%s` builds one instance per style:" % src, ""]
    for r in rows:
        out += ["- `fonts/ttf/%s.ttf` -> `%s`" % (r["style"], os.path.basename(r["shipped"]))]
    out += [""]
    out += wrap("`%s` is the equivalence commit: it builds the very source the shipped "
                "binaries were exported from. Source modernization adds no features. Any "
                "improvement is a later commit that needs its own QA, and is left as future "
                "work for an onboarder to review in a font-update PR." % head_full[:12], 88)
    disclose = plan.get("disclose", [])
    if disclose:
        out += ["", "## Known differences from the released fonts", ""]
        out += wrap("Reviewed and deliberately left as they are; the repository's README "
                    "lists them too:", 88)
        out += [""]
        for t in disclose:
            out += wrap("- " + t, 88, subsequent_indent="  ")
    earlier = plan.get("earlier_sources", [])
    if earlier:
        out += ["", "## Earlier sources", ""]
        out += wrap("Other sources of this family, kept on record; none of them is what "
                    "Google Fonts ships:", 88)
        out += [""]
        for t in earlier:
            out += wrap("- " + t, 88, subsequent_indent="  ")
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
        out += ["", "## Previous investigation", ""]
        for l in previous.rstrip("\n").splitlines():
            out.append("#" + l if l.startswith("#") else l)
    return "\n".join(out) + "\n"


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
        head_full = equivalence_commit(d, rows)   # recorded; later commits are future work
        future = land.load_plan(repo).get("future_work", [])
        # the branch the commit lives on once published: `main` for a fresh repository;
        # `master` for a fork or an extended repository, AFTER its pull request is
        # MERGED -- a squash merge would give the commit a new hash and orphan this one
        # (a `glyphs` repository is created empty on GitHub and pushed to `main`)
        rbranch = "main" if rows[0]["kind"] in ("hg", "glyphs") else "master"
        fam, lic = rows[0]["family"], rows[0]["lic"]
        mp = os.path.join(wt, lic, fam, "METADATA.pb")
        text = open(mp, encoding="utf-8").read()
        display = re.search(r'^name: "(.*)"', text, re.M).group(1)
        block = source_block(repo, rows, head_full, rbranch)
        new, old = replace_source(text, block)
        open(mp, "w", encoding="utf-8").write(new)
        ui = os.path.join(wt, lic, fam, "upstream_info.md")
        previous = open(ui, encoding="utf-8").read() if os.path.exists(ui) else ""
        body = upstream_info(repo, rows, old, head_full, display, previous, future, wt)
        if any(ord(c) > 127 for c in body) and not any(ord(c) > 127 for c in previous):
            raise SystemExit("FATAL: non-ASCII introduced into upstream_info.md for %s" % fam)
        open(ui, "w", encoding="utf-8").write(body)
        git(wt, "add", "--", os.path.relpath(mp, wt), os.path.relpath(ui, wt))
        if rows[0]["kind"] == "glyphs":
            n_disc = len(land.load_plan(repo).get("disclose", []))
            msg = ("%s: reference the googlefonts/%s Glyphs source\n\n"
                   "Repo: https://github.com/googlefonts/%s\nCommit: %s\nConfig: sources/config.yaml\n"
                   "Status: the designer's %s built as is, no conversion; builds with "
                   "gftools-builder and fontc\n"
                   "Confidence: high -- 0 blocking rows against the shipped binaries%s\n\n"
                   "Assisted by an AI agent (Claude Opus 5.5)\n"
                   % (display, repo, repo, head_full[:12], rows[0]["source"],
                      "; %d known difference(s) disclosed" % n_disc if n_disc else ""))
            git(wt, "commit", "-q", "-F", "-", input=msg)
            print("%s: %s" % (fam, git(wt, "rev-parse", "--short", "HEAD").strip()))
            continue
        msg = ("%s: reference the googlefonts/%s .glyphs source\n\n"
               "Repo: https://github.com/googlefonts/%s\nCommit: %s\nConfig: sources/config.yaml\n"
               "Status: %s; builds with gftools-builder and fontc\n"
               "Confidence: high -- 0 blocking rows against the shipped binaries\n\n"
               "Assisted by an AI agent (Claude Opus 5.5)\n"
               % (display, repo, repo, head_full[:12],
                  "converted from the unmodified .sfd" if not edits_in(d, rows) else
                  plural("converted from the .sfd after %d documented edit(s)" % edits_in(d, rows))))
        git(wt, "commit", "-q", "-F", "-", input=msg)
        print("%s: %s" % (fam, git(wt, "rev-parse", "--short", "HEAD").strip()))


if __name__ == "__main__":
    main()
