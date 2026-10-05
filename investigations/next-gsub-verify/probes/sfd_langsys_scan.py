#!/usr/bin/env python3
"""Question: which styles of BOTH batches (families.tsv, families-next.tsv) does the
proposed babelfont language-system change touch, judged from the .sfd alone?

Two triggers, read from each style's paired, unmodified .sfd (pairing from the
tables, sources from the repo archive):

  (a) exclude_dflt: a feature F has, in script S, a lookup registered for (S, dflt)
      but NOT for some language L of S that F is also registered for. babelfont 17ea899
      writes `language L;` (include_dflt), which lets fea-rs 1.0.0 copy the (S, dflt)
      lookups registered so far into L (features.rs set_system); FontForge did not.
      Lists the (feature, script, language, lookups L would inherit).
  (b) aalt narrower: aalt's (script, language) pairs are a strict subset of all the
      pairs any lookup uses. Reports whether the style has kerning (KernClass2/Kerns2)
      or anchors (AnchorPoint), i.e. whether the prototype applies its fix or only warns.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY sfd_langsys_scan.py [families.tsv ...]      (default: both tables)
"""
import re
import subprocess
import sys

W = "/home/fsanches/compartilhado/gf-source-modernization"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"


def sfd_text(row):
    repo, fam, lic, kind, base, commit, style, src, shipped = row
    path = "%s/%s/%s" % (lic, fam, src) if kind == "hg" else src
    r = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show", "%s:%s" % (commit, path)],
                       capture_output=True)
    if r.returncode:
        return None
    return r.stdout.decode("utf-8", "replace")


LOOKUP = re.compile(r'^Lookup: (\d+) \d+ \d+ "((?:[^"\\]|\\.)*)"\s+\{.*?\}\s*\[(.*)\]\s*$')
FEAT = re.compile(r"'(....)' \((.*?)\)")
SCR = re.compile(r"'(....)' <((?:'....' ?)*)>")


def parse(text):
    """[(type, name, [(feature, script, lang)])] in declaration order."""
    out = []
    for line in text.splitlines():
        m = LOOKUP.match(line)
        if not m:
            continue
        typ, name, feats = int(m.group(1)), m.group(2), m.group(3)
        regs = []
        for fm in FEAT.finditer(feats):
            feat = fm.group(1)
            for sm in SCR.finditer(fm.group(2)):
                script = sm.group(1).strip() or "DFLT"
                for lang in re.findall(r"'(....)'", sm.group(2)):
                    regs.append((feat, script, lang.strip()))
        out.append((typ, name, regs))
    return out


def main():
    tables = sys.argv[1:] or [W + "/families.tsv", W + "/families-next.tsv"]
    for t in tables:
        print("### %s" % t)
        for line in open(t).readlines()[1:]:
            row = line.rstrip("\n").split("\t")
            style = row[6]
            text = sfd_text(row)
            if text is None:
                print("%-28s NO-SOURCE" % style)
                continue
            lookups = parse(text)
            pairs = {(s, l) for _, _, regs in lookups for _, s, l in regs}
            aalt = {(s, l) for _, _, regs in lookups for f, s, l in regs if f == "aalt"}
            kern = bool(re.search(r"^(KernClass2|Kerns2|VKernClass2):", text, re.M))
            anchors = bool(re.search(r"^AnchorPoint:", text, re.M))
            # (a) per feature/script: dflt-registered lookups a language lacks
            inherit = []
            feats = {f for _, _, regs in lookups for f, _, _ in regs}
            for f in sorted(feats):
                by = {}
                for _, name, regs in lookups:
                    for ff, s, l in regs:
                        if ff == f:
                            by.setdefault((s, l), []).append(name)
                for (s, l), names in sorted(by.items()):
                    if l == "dflt":
                        continue
                    missing = [n for n in by.get((s, "dflt"), []) if n not in names]
                    if missing:
                        inherit.append("%s %s/%s would inherit %d: %s" % (f, s, l, len(missing),
                                        "; ".join(missing)[:160]))
            b = ""
            if aalt and aalt != pairs:
                extra = sorted("%s/%s" % p for p in pairs - aalt)
                b = "aalt-narrower (aalt lacks %s) -> %s" % (",".join(extra),
                     "WARN-ONLY (kerning/anchors)" if (kern or anchors) else "fix applies")
            if inherit or b:
                print("%-28s %s" % (style, b or "-"))
                for x in inherit:
                    print("      (a) " + x)
            else:
                print("%-28s unaffected" % style)


if __name__ == "__main__":
    main()
