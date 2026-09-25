#!/usr/bin/env python3
"""Build one repository's layered history, ready for Felipe to push.

The history, in the shape the repositories this programme already published use
(verified on the googlefonts/* repos in the repo archive, and as
sfd-batch5/tools/drift/build_series.py builds it):

  1. the unmodified original -- for a fresh repository, "Import <family> from
     googlefontdirectory-hg at <commit>", the family's files exactly as the
     monorepo holds them at the revision METADATA.pb records; for a fork, the
     upstream history itself; for a family added to an existing repository,
     "Restore <file> as committed at <commit>", byte-identical
  2. "Adopt the Unified Font Repository template" -- scaffolding, a README
     recording provenance, and the legacy build cruft dropped
  3. one commit per documented .sfd edit in plans/<repo>.json (criterion B:
     every change to the font is its own commit, with the edit visible)
  4. "Convert to .glyphs with babelfont <rev>" -- LAST: the conversion of the
     committed .sfd, with fidelity flags only, plus the named tool workarounds
     of tools/workarounds.py (values from the .sfd); src/ retired. Built and
     gated BEFORE it is committed, so its message states what was measured:
     the table gate (sfd-batch5/tools/table_gate.py), the exact codepoint set,
     and tools/functional_gate.py (shaping, rendering, names, line spacing,
     advances, GDEF). A landing is CLEAN only if all three pass.

Nothing is pushed. The remote is set so that Felipe's push is one command.

Usage: land.py <repo> [--rebuild]      (repo = googlefonts/<repo> name, families.tsv col 1)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import functional_gate  # noqa: E402
import recipe        # noqa: E402
import sfd_edit      # noqa: E402
import workarounds   # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
OUT = "/home/fsanches/compartilhado/sfd-reland-repos"
TEMPLATE = "/home/fsanches/compartilhado/sfd-func-audit/ufr-template"
# the converter checkout; after the upstream merge, a worktree of simoncozens/babelfont-rs
# main (BF_TREE=... in the environment), built with tools/build_babelfont.sh
BF_TREE = os.environ.get("BF_TREE", "/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion")
BF = os.path.join(BF_TREE, "target-heights/release/babelfont")
# A font repository may cite only a converter revision merged into babelfont's upstream:
# never a personal fork (Felipe, 2026-09-23). --unpublished-converter lands anyway, for
# measurement only; push.sh refuses such a landing.
BF_UPSTREAM = "simoncozens/babelfont-rs"
BF_WHERE = BF_UPSTREAM            # set by check_converter()
B3 = "/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder"
B3_ID, FONTC_ID = "e851b8b", "1.0.0"
D3 = "/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3"
PY = "/home/fsanches/compartilhado/gftools/venv/bin/python3"
TG = "/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py"
GF = "/home/fsanches/compartilhado/google/fonts"
IDENT = ["-c", "user.name=Felipe Correa da Silva Sanches",
         "-c", "user.email=juca@members.fsf.org", "-c", "commit.gpgsign=false"]
TRAILER = "\n\nAssisted by an AI agent (Claude Opus 5.5)\n"
# where a landing builds before it commits (SCRATCH=<dir> to put it elsewhere, e.g. /home)
SCRATCH = os.environ.get("SCRATCH", "/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/"
                                    "f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad")

TEMPLATE_FILES = [".github/workflows/build.yaml", "Makefile", "requirements.in",
                  "requirements.txt", "scripts/customize.py", "scripts/read-config.py",
                  "scripts/update-custom-filter.py", "scripts/index.html"]
# The template's OFL.txt is Bentham's. It is never copied: a family's licence is
# the one thing in an imported tree a template must not replace.

SUBSET = re.compile(r"\.(latin|latin-ext|cyrillic|cyrillic-ext|greek|greek-ext|"
                    r"vietnamese|menu|khmer|devanagari|hebrew|arabic|thai|tamil|"
                    r"bengali|oriya|gujarati|gurmukhi|telugu|kannada|malayalam)$")

BRANCH = {"hg": "main", "fork": "modernize-sfd-to-glyphs",
          "allerta": "add-allerta-stencil", "upstream": "modernize-sfd-to-glyphs"}


# Why a per-release flag differs between the styles of one family.
REASON = {
    "--fontforge-height-glyph-count-mean": "its release was exported by a FontForge built before 2012-05-14",
    "--reverse-path-direction": "its release mixes contour directions",
    "--correct-path-direction": "its release has uniform contour directions",
    "--add-legacy-duplicate-cmap": "its release carries makeotf's duplicate cmap entries",
    "--correct-conjunct-category": "Indic mark positioning",
}


def describe_sources(paths):
    """src/Lekton-Bold-TTF.sfd, src/Lekton-Italic-TTF.sfd -> "src/Lekton-{Bold,Italic}-TTF.sfd"."""
    if len(paths) == 1:
        return paths[0]
    names = sorted(paths)
    pre = os.path.commonprefix(names)
    suf = os.path.commonprefix([n[::-1] for n in names])[::-1]
    pre = pre[:pre.rfind("-") + 1] if "-" in pre else pre
    suf = suf[suf.find("-"):] if "-" in suf else suf
    mids = [n[len(pre):len(n) - len(suf)] for n in names]
    if all(mids) and "," not in "".join(mids):
        return "%s{%s}%s" % (pre, ",".join(mids), suf)
    return ", ".join(names)


class LandError(Exception):
    pass


def sh(*cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise LandError("%s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r


def git(repo, *args, check=True):
    return sh("git", "-C", repo, *IDENT, *args, check=check)


def commit(repo, message, *paths):
    if paths:
        git(repo, "add", "--", *paths)
    if git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        raise LandError("nothing staged for: %s" % message.splitlines()[0])
    msg = message.rstrip("\n") + TRAILER
    for ch in msg:
        if ord(ch) > 127:
            raise LandError("non-ASCII in commit message: %r" % message.splitlines()[0])
    r = subprocess.run(["git", "-C", repo, *IDENT, "commit", "-q", "-F", "-"],
                       input=msg, capture_output=True, text=True)
    if r.returncode != 0:
        raise LandError("commit failed: %s" % r.stderr)
    return git(repo, "rev-parse", "--short", "HEAD").stdout.strip()


def family_rows(repo):
    rows = [r for r in recipe.rows() if r["repo"] == repo]
    if not rows:
        raise LandError("no rows for repo %s in %s" % (repo, recipe.families_file()))
    return rows


def display_name(family):
    text = open(os.path.join(GF, "ofl" if os.path.isdir(os.path.join(GF, "ofl", family)) else "apache",
                             family, "METADATA.pb"), encoding="utf-8").read()
    return re.search(r'^name: "(.*)"', text, re.M).group(1)


def load_plan(repo):
    p = os.path.join(W, "plans", repo + ".json")
    if not os.path.exists(p):
        return {"repo": repo, "commits": [], "flags": {}}
    plan = json.load(open(p))
    plan.setdefault("commits", [])
    plan.setdefault("flags", {})
    return plan


def check_converter():
    if git(BF_TREE, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise LandError("babelfont worktree has uncommitted changes; the pin would lie")
    head = git(BF_TREE, "rev-parse", "HEAD").stdout.strip()
    stamp = os.path.join(BF_TREE, "target-heights", "BUILT_FROM")
    built = open(stamp).read().strip() if os.path.exists(stamp) else None
    if built != head:
        raise LandError("babelfont binary was built from %s, HEAD is %s; run tools/build_babelfont.sh"
                        % (built, head))
    git(BF_TREE, "fetch", "-q", "upstream", "main")
    upstream = git(BF_TREE, "merge-base", "--is-ancestor", head, "upstream/main",
                   check=False).returncode == 0
    if not upstream and "--unpublished-converter" not in sys.argv:
        raise LandError("babelfont %s is not on %s main; a font repository may cite only an "
                        "upstream revision (--unpublished-converter lands for measurement only)"
                        % (head[:7], BF_UPSTREAM))
    global BF_WHERE
    BF_WHERE = BF_UPSTREAM if upstream else "UNPUBLISHED, not on %s main" % BF_UPSTREAM
    return head[:7], upstream


# --- step 1: the unmodified original ------------------------------------------
def start(repo, rows, d):
    kind, fam, lic, base, commit_id = (rows[0][k] for k in ("kind", "family", "lic", "base", "commit"))
    mirror = os.path.join(ARC, base + ".git")
    if kind == "hg":
        sh("git", "init", "-q", "-b", "main", d)
        tar = subprocess.run(["git", "-C", mirror, "archive", commit_id, "%s/%s" % (lic, fam)],
                             capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", d, "--strip-components=2"], input=tar, check=True)
        git(d, "add", "-A")
        return commit(d, textwrap.dedent("""\
            Import %s from googlefontdirectory-hg at %s

            The contents of %s/%s at commit %s
            of https://github.com/%s: the revision
            google/fonts records in METADATA.pb for this family, and so the
            revision the shipped binaries came from.

            Nothing here is modified: these are the family's files exactly as the
            monorepo holds them. Every change from here on is its own commit.

            The repository starts here rather than carrying the monorepo's
            history: the family has no repository of its own, and splitting its
            subtree out of a repository that serves the whole library is not
            practical. The commit named above is the provenance.""") % (
            fam, commit_id[:12], lic, fam, commit_id, base))
    if kind == "allerta":
        # the repository being extended is googlefonts/<repo>; `base` names where the
        # restored file comes from, not the repository to clone
        sh("git", "clone", "-q", os.path.join(ARC, "googlefonts", repo + ".git"), d)
    else:
        sh("git", "clone", "-q", mirror, d)
    if kind == "allerta":
        git(d, "checkout", "-q", "-b", BRANCH[kind], "master")
        src = rows[0]["source"]
        blob = subprocess.run(["git", "-C", os.path.join(ARC, "librefonts/allerta.git"), "show",
                               "%s:%s" % (commit_id, src)], capture_output=True, check=True).stdout
        os.makedirs(os.path.join(d, os.path.dirname(src)), exist_ok=True)
        open(os.path.join(d, src), "wb").write(blob)
        return commit(d, textwrap.dedent("""\
            Restore %s as committed at %s

            Byte-identical to librefonts/allerta at %s, the revision
            google/fonts records for Allerta Stencil.

            This repository serves two families. When it was modernised only
            Allerta was converted, but the commit retiring the legacy sources
            (2efd249) removed Allerta Stencil's too, leaving a family Google Fonts
            ships with no source here at all.""") % (src, commit_id[:12], commit_id), src)
    git(d, "checkout", "-q", "-b", BRANCH[kind], commit_id)
    return None


# --- step 2: the template -----------------------------------------------------
def template(repo, rows, d):
    if rows[0]["kind"] == "allerta":
        return None          # already adopted in that repository
    for f in TEMPLATE_FILES:
        os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True)
        shutil.copyfile(os.path.join(TEMPLATE, f), os.path.join(d, f))
    tracked = git(d, "ls-files").stdout.splitlines()
    old_readme = open(os.path.join(d, "README.md")).read() if "README.md" in tracked else ""
    disp = display_name(rows[0]["family"])
    readme = textwrap.dedent("""\
        # %s

        The sources in `sources/` were converted from this repository's FontForge
        `.sfd` sources using [babelfont-rs](https://github.com/simoncozens/babelfont-rs),
        and build with [gftools-builder](https://github.com/simoncozens/gftools-builder3)
        and fontc. Every change made to the `.sfd` before converting it is its own
        commit in this repository's history.

        The original FontForge sources remain in the git history.
        """) % disp
    if old_readme:
        readme += "\n## Original README\n\n" + old_readme
    open(os.path.join(d, "README.md"), "w").write(readme)
    dead_ttx = [f for f in tracked if "/" not in f and f.endswith(".ttx")]
    dead_ci = [f for f in tracked if f in (".travis.yml", "METADATA.json")]
    dead_bin = [f for f in tracked if "/" not in f and
                (f.lower().endswith((".ttf", ".otf", ".woff", ".woff2")) or SUBSET.search(f))]
    dead = dead_ttx + dead_ci + dead_bin
    if dead:
        git(d, "rm", "-q", "--", *dead)
    moved = []
    if "src/FONTLOG.txt" in tracked and "FONTLOG.txt" not in tracked:
        git(d, "mv", "src/FONTLOG.txt", "FONTLOG.txt")
        moved = ["FONTLOG.txt"]
    body = ["Add the googlefonts project-template scaffolding: a CI build and QA",
            "workflow, a Makefile, the template requirements files and the helper",
            "scripts, and a README recording where the sources come from."]
    drops = []
    if dead_ttx:
        drops.append("the checked-in TTX dumps")
    if dead_ci:
        drops.append(" and ".join("the Travis config" if f == ".travis.yml" else "the stale METADATA.json"
                                  for f in dead_ci))
    if dead_bin:
        drops.append("the checked-in binaries and subset files (google/fonts ships the "
                     "binaries; this repository now builds them from sources/)")
    if drops:
        body += [""] + textwrap.wrap("Drop " + (", ".join(drops[:-1]) + " and " + drops[-1]
                                                if len(drops) > 1 else drops[0]) + ".", 72)
    if moved:
        body += [""] + textwrap.wrap("FONTLOG.txt moves from src/ to the repository root: it "
                                     "is documentation, and src/ is retired by the conversion.", 72)
    return commit(d, "Adopt the Unified Font Repository template\n\n" + "\n".join(body),
                  *(TEMPLATE_FILES + ["README.md"] + moved))


# --- step 3: documented .sfd edits --------------------------------------------
def edits(repo, rows, d, plan):
    made = []
    by_style = {r["style"]: r for r in rows}
    for c in plan["commits"]:
        styles = list(by_style) if c.get("styles", "*") in ("*", ["*"]) else c["styles"]
        touched = []
        # a commit is one op, or several that only make sense together (a value and
        # the flag saying it is absolute) so that no commit leaves a nonsense state
        ops = c["ops"] if "ops" in c else [[c["op"], c.get("args", "")]]
        for st in styles:
            path = by_style[st]["source"]
            for op, args in ops:
                before, changed = sfd_edit.apply_file(os.path.join(d, path), op, args)
                if changed and path not in touched:
                    touched.append(path)
        if not touched:
            raise LandError("plan commit changed nothing: %s" % c["subject"])
        made.append(commit(d, c["subject"] + "\n\n" + c["body"].strip(), *touched))
    return made


# --- step 4: convert, build, gate, commit -------------------------------------
def built_name(glyphs_path):
    t = open(glyphs_path, encoding="utf-8").read()
    fam = re.search(r'^familyName = "?(.*?)"?;$', t, re.M).group(1)
    inst = re.search(r"^instances = \(\n\{.*?^name = \"?(.*?)\"?;$", t, re.S | re.M).group(1)
    return "%s-%s.ttf" % (fam.replace(" ", ""), inst.replace(" ", ""))


def cmap_difference(shipped, built):
    """Codepoints the build gains and loses against the release. Checked here because
    the table gate accepts a GAINED codepoint (cmap_blocking's duplicate-cmap class),
    so a gate-clean build can still map what the release does not."""
    from fontTools.ttLib import TTFont
    rel = set(TTFont(shipped).getBestCmap() or {})
    ours = set(TTFont(built).getBestCmap() or {})
    return sorted(ours - rel), sorted(rel - ours)


def d3_json_path(built, scratch):
    """Where gate() leaves diffenator3's JSON for a built font; the functional gate
    reads its rendering sections instead of running diffenator3 again."""
    return os.path.join(scratch, os.path.basename(built) + ".d3.json")


def gate(shipped, built, scratch):
    j = d3_json_path(built, scratch)
    with open(j, "w") as fh:
        subprocess.run([D3, "-J", "1", "--no-languages", "--no-match", "--json", "--succinct",
                        shipped, built], stdout=fh, stderr=subprocess.DEVNULL)
    out = subprocess.run([PY, TG, j, "--fonts", shipped, built], capture_output=True, text=True).stdout
    m = re.findall(r"^(\d+) blocking table difference\(s\)", out, re.M)
    if not m:
        raise LandError("the gate did not finish for %s" % built)
    rows = [l.strip() for l in out.splitlines() if l.strip().startswith("BLOCKING ")]
    return int(m[-1]), rows


def convert(repo, rows, d, plan, bf_rev, n_edits):
    os.makedirs(os.path.join(d, "sources"), exist_ok=True)
    per_style = []
    for r in rows:
        src = os.path.join(d, r["source"])
        text = open(src, encoding="utf-8", errors="replace").read()
        f = plan["flags"].get(r["style"], {})
        flags = recipe.flags_for(text, r["shipped"], f.get("add", []), f.get("drop", []))
        g = os.path.join(d, "sources", r["style"] + ".glyphs")
        sh(BF, src, g, *flags)
        notes = workarounds.apply_all(g, src)
        per_style.append({"row": r, "flags": flags, "notes": notes, "glyphs": g})
    cfg = os.path.join(d, "sources", "config.yaml")
    if rows[0]["kind"] == "allerta":
        text = open(cfg).read().rstrip("\n") + "\n"
        for p in per_style:
            text += "  - %s.glyphs\n" % p["row"]["style"]
        open(cfg, "w").write(text)
    else:
        with open(cfg, "w") as fh:
            fh.write("buildVariable: false\nremoveOutlineOverlaps: false\nsources:\n")
            for p in per_style:
                fh.write("  - %s.glyphs\n" % p["row"]["style"])

    # build exactly what will be committed, from its own config, in a scratch copy
    os.makedirs(SCRATCH, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="land-%s-" % repo, dir=SCRATCH)
    shutil.copytree(os.path.join(d, "sources"), os.path.join(scratch, "sources"))
    r = subprocess.run([B3, "sources/config.yaml"], cwd=scratch, capture_output=True, text=True)
    ttf_dir = os.path.join(scratch, "fonts", "ttf")
    built = sorted(os.listdir(ttf_dir)) if os.path.isdir(ttf_dir) else []
    results = []
    functional = {}            # style -> tools/functional_gate.py verdict
    for p in per_style:
        name = built_name(p["glyphs"])
        if name not in built:
            results.append((p["row"]["style"], None, ["BUILD: %s not produced (%s)" % (name, ", ".join(built) or "nothing")]))
            continue
        font = os.path.join(ttf_dir, name)
        n, blocking = gate(p["row"]["shipped"], font, scratch)
        gained, lost = cmap_difference(p["row"]["shipped"], font)
        if gained or lost:
            n += len(gained) + len(lost)
            blocking = blocking + ["CMAP gained %s lost %s" % (["U+%04X" % c for c in gained],
                                                               ["U+%04X" % c for c in lost])]
        # after the table gate: does the build BEHAVE like the release?
        fg = functional_gate.run(p["row"]["shipped"], font, p["row"]["style"],
                                 d3_json=d3_json_path(font, scratch), workdir=scratch)
        functional[p["row"]["style"]] = fg
        results.append((p["row"]["style"], n, blocking))
        p["built"] = name

    # retire the converted source(s)
    kind = rows[0]["kind"]
    if kind in ("hg", "fork"):
        retired = git(d, "ls-files", "src").stdout.split()
        if retired:
            git(d, "rm", "-r", "-q", "src")
        what = "src/ is retired (%d files); it remains in the git history." % len(retired)
    else:
        retired = [p["row"]["source"] for p in per_style]
        git(d, "rm", "-q", "--", *retired)
        what = "The converted .sfd is retired; it remains in the git history."

    def equivalent(st):
        return st in functional and functional[st]["verdict"] == "PASS"
    clean = all(n == 0 and equivalent(st) for st, n, _ in results)
    srcs = describe_sources([p["row"]["source"] for p in per_style])
    corrected = (", as corrected by the %d preceding commit%s," % (n_edits, "" if n_edits == 1 else "s")
                 if n_edits else "")

    def wrap(text, indent="  ", sub="    "):
        return textwrap.wrap(text, 72, initial_indent=indent, subsequent_indent=sub,
                             break_on_hyphens=False, break_long_words=False)

    # A flag most styles share is stated once; a style that differs says how.
    every = []
    for p in per_style:
        every += [f for f in p["flags"] if f not in every]
    common = [f for f in every if 2 * sum(f in p["flags"] for p in per_style) > len(per_style)]
    lines = ["Convert to .glyphs with babelfont %s" % bf_rev, ""]
    lines += wrap("Converted from %s%s with babelfont %s (%s), FontForge-fidelity filters "
                  "only:" % (srcs, corrected, bf_rev, BF_WHERE), "", "")
    lines += wrap(" ".join(common), "  ", "  ")
    for p in per_style:
        extra = [f for f in p["flags"] if f not in common]
        missing = [f for f in common if f not in p["flags"]]
        if not extra and not missing:
            continue
        said = []
        if extra and missing and len(extra) == len(missing) == 1:
            said.append("%s instead of %s" % (extra[0], missing[0]))
        else:
            if extra:
                said.append("also " + " ".join(extra))
            if missing:
                said.append("not " + " ".join(missing))
        why = "; ".join(REASON[f] for f in extra if f in REASON)
        lines += wrap("%s: %s%s" % (p["row"]["style"], ", ".join(said), " (%s)" % why if why else ""))
    notes = [(p["row"]["style"], n) for p in per_style for n in p["notes"]]
    if notes:
        lines += ["", "Values from the .sfd that the toolchain loses, carried across:"]
        for st, n in notes:
            lines += wrap("%s: %s" % (st, n))
    gf_ref = sh("git", "-C", GF, "rev-parse", "--short=12", "HEAD").stdout.strip()
    lines.append("")
    if clean:
        lines += textwrap.wrap("Builds with gftools-builder3 %s (fontc %s) and matches the binaries "
                               "google/fonts %s ships: 0 blocking rows under the table gate, "
                               "exactly the release's codepoints, and functionally equivalent under "
                               "tools/functional_gate.py (cmap, shaping, rendering, names, line "
                               "spacing, advances, GDEF), %d style(s)."
                               % (B3_ID, FONTC_ID, gf_ref, len(results)), 72)
    else:
        lines += textwrap.wrap("Builds with gftools-builder3 %s (fontc %s). Against google/fonts %s, "
                               "under the table gate and tools/functional_gate.py:"
                               % (B3_ID, FONTC_ID, gf_ref), 72)
        for st, n, blocking in results:
            if n is None:
                lines.append("  %s: %s" % (st, blocking[0]))
                continue
            table = "0 blocking rows" if n == 0 else "%s blocking row(s)" % n
            bad = functional_gate.failed_checks(functional[st])
            lines += wrap("%s: %s; %s" % (st, table, "functionally equivalent" if not bad else
                                          "functionally different in " + ", ".join(bad)))
    lines += [""] + textwrap.wrap(what, 72)
    head = commit(d, "\n".join(lines), "sources")
    shutil.rmtree(scratch, ignore_errors=True)
    return head, results, functional


def main():
    repo = sys.argv[1]
    rebuild = "--rebuild" in sys.argv
    rows = family_rows(repo)
    plan = load_plan(repo)
    bf_rev, bf_upstream = check_converter()
    d = os.path.join(OUT, repo)
    if os.path.exists(d):
        if not rebuild:
            raise LandError("%s exists; pass --rebuild to regenerate it" % d)
        prev = d + ".prev"
        if os.path.exists(prev):
            shutil.rmtree(prev)
        os.rename(d, prev)            # keep the previous generation, never just delete
    os.makedirs(OUT, exist_ok=True)
    start(repo, rows, d)
    template(repo, rows, d)
    made = edits(repo, rows, d, plan)
    head, results, functional = convert(repo, rows, d, plan, bf_rev, len(made))
    kind = rows[0]["kind"]
    if kind == "upstream":
        git(d, "remote", "set-url", "origin", "https://github.com/%s.git" % rows[0]["base"])
    else:
        git(d, "remote", "remove", "origin", check=False)
        git(d, "remote", "add", "origin", "https://github.com/googlefonts/%s.git" % repo)
    n = int(git(d, "rev-list", "--count", "HEAD").stdout)
    def fverdict(st):
        if st not in functional:
            return "-"
        bad = functional_gate.failed_checks(functional[st])
        return "PASS" if not bad else "FAIL(%s)" % "+".join(bad)
    # CLEAN = 0 table-gate rows, the release's exact codepoints, AND functional PASS
    status = "CLEAN" if all(x == 0 and fverdict(st) == "PASS" for st, x, _ in results) else "RESIDUAL"
    if not bf_upstream:
        status += "-UNPUBLISHED-CONVERTER"      # push.sh pushes only CLEAN
    summary = "; ".join("%s=%s functional=%s" % (st, x if x is not None else "BUILD", fverdict(st))
                        for st, x, _ in results)
    with open(os.path.join(W, "landed.tsv"), "a") as fh:
        fh.write("\t".join([repo, BRANCH[kind], head, str(n), status, summary]) + "\n")
    print("%s: %s @ %s, %d commits, %d edit(s): %s" % (repo, status, head, n, len(made), summary))
    for st, x, blocking in results:
        for b in blocking[:6]:
            print("   %s %s" % (st, b))
        if st in functional and functional[st]["verdict"] != "PASS":
            for line in functional_gate.summary_lines(functional[st])[1:]:
                print("   " + line)
    return 0 if status == "CLEAN" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LandError as e:
        sys.exit("FATAL: %s" % e)
