#!/usr/bin/env python3
"""Question answered: which minimal .sfd edits close which gate rows for
Nosifer-Regular and NosiferCaps-Regular?  Writes the candidate sources that
tools/baseline.sh then builds with SRC_OVERRIDE (one build at a time).

Each variant starts from the UNMODIFIED source named in families.tsv, read
straight from the repo archive, so a variant never inherits another's edits.

  droplookup  delete the `Lookup:` line of the named GSUB lookup and every glyph
              line that fills one of its subtables (Ligature2:/Substitution2:/
              AlternateSubs2:/MultipleSubs2: "<subtable>" ...).  Proposed new op.
  heights     add OS2XHeight/OS2CapHeight -- used ONLY to prove that 925/854 are
              the values the gate wants and that nothing else moves; the proposed
              fix for these rows is a converter change, not this edit.

Usage: /home/fsanches/compartilhado/gftools/venv/bin/python3 make_variants.py <outdir>
"""
import re
import subprocess
import sys

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
COMMIT = "52f780bc9d197280a9f430574e179a5f233c56b6"
SRC = {
    "Nosifer-Regular": "ofl/nosifer/src/Nosifer-Regular-TTF.sfd",
    "NosiferCaps-Regular": "ofl/nosifercaps/src/NosiferCaps-Regular-TTF.sfd",
}
LIGA = "'liga' Standard Ligatures in Latin lookup 0"


def read(style):
    return subprocess.run(["git", "-C", ARC, "show", "%s:%s" % (COMMIT, SRC[style])],
                          capture_output=True, check=True).stdout.decode("utf-8", "surrogateescape")


def droplookup(text, name):
    pat = re.compile(r'^Lookup: \d+ \d+ \d+ "%s"\s+\{(.*?)\}.*\n' % re.escape(name), re.M)
    m = pat.search(text)
    if not m:
        sys.exit("FATAL: no Lookup: line named %r" % name)
    subtables = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    text = text[:m.start()] + text[m.end():]
    n = 0
    for st in subtables:
        gl = re.compile(r'^(?:Ligature2|Substitution2|AlternateSubs2|MultipleSubs2): "%s" .*\n'
                        % re.escape(st), re.M)
        text, k = gl.subn("", text)
        n += k
    if n == 0:
        sys.exit("FATAL: lookup %r had no glyph entries" % name)
    # anything still naming the lookup or a subtable (a chaining SeqLookup, a
    # feature file, another glyph-level line kind) would dangle: refuse.
    for token in [name] + subtables:
        if '"%s"' % token in text:
            sys.exit("FATAL: %r is still referenced after the drop" % token)
    print("  droplookup %r: removed the Lookup line and %d glyph entr%s (subtables %s)"
          % (name, n, "y" if n == 1 else "ies", subtables))
    return text


def addfield(text, field, value):
    if re.search(r"^%s:" % re.escape(field), text, re.M):
        sys.exit("FATAL: %s already present" % field)
    return re.sub(r"^(FontName: .*\n)", r"\1%s: %s\n" % (field, value), text, count=1, flags=re.M)


def heights(text):
    text = addfield(text, "OS2XHeight", "925")
    text = addfield(text, "OS2CapHeight", "854")
    print("  heights: added OS2XHeight 925, OS2CapHeight 854")
    return text


VARIANTS = {
    ("Nosifer-Regular", "droplookup"): [lambda t: droplookup(t, LIGA)],
    ("Nosifer-Regular", "heights"): [heights],
    ("Nosifer-Regular", "droplookup+heights"): [lambda t: droplookup(t, LIGA), heights],
    ("NosiferCaps-Regular", "heights"): [heights],
}


def main():
    out = sys.argv[1]
    for (style, name), ops in VARIANTS.items():
        text = read(style)
        print("%s %s" % (style, name))
        for op in ops:
            text = op(text)
        path = "%s/%s.%s.sfd" % (out, style, name)
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(text)
        print("  -> %s" % path)


if __name__ == "__main__":
    main()
