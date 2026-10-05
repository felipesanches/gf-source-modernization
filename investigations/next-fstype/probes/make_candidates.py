#!/usr/bin/env python3
"""make_candidates.py -- write each style's candidate .sfd: the unmodified source plus
the documented edits proposed for unit "fstype", in plan order.

Question answered: applied with tools/sfd_edit.py exactly as tools/land.py would apply
a plan, what does each edit find in the source beforehand, and does every one apply?
The files it writes are what tools/baseline.sh then converts (SRC_OVERRIDE=).

Edit sets (cumulative; the value's origin is named beside each):
  fstype     FSType 0            google/fonts 93550bd32 (Titillium Web, #931 "v1.002")
                                 google/fonts 8ccda7bf7 (Wallpoet, "Fix fsType for 40 font files")
  extralight (TitilliumWeb-ExtraLight, -ExtraLightItalic only; all google/fonts 93550bd32)
             TTFWeight 275       the hotfix raised usWeightClass 200 -> 275
             FontName / FullName / LangName   the hotfix renamed Thin -> ExtraLight
                                 (PostScript, full, unique-ID and typographic names)
  version    (Titillium Web only, on top of the above; google/fonts 93550bd32, "v1.002")
             Version 1.002;...   name ID 5 and head.fontRevision 1.000/1.001 -> 1.002
             sfntRevision 0x00010083   FontForge's head.revision source (tottf.c:2850);
                                 1.002 in 16.16 is 0x00010083, the release's 1.0019989
             setname 1033 3/5    the LangName unique ID and version strings
                                 (setname is a PROTOTYPE op, defined here, proposed for
                                 tools/sfd_edit.py: replace one name ID of one LangName
                                 line instead of rewriting the line)

Usage:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY investigations/next-fstype/probes/make_candidates.py <set> <outdir>
      set = fstype | extralight | version
  -> <outdir>/<Style>.sfd for every style of runs/families-fstype.tsv the set applies to,
     and a log of each edit's `before` on stdout.
"""
import os
import subprocess
import sys

W = "/home/fsanches/compartilhado/gf-source-modernization"
sys.path.insert(0, os.path.join(W, "tools"))
import sfd_edit  # noqa: E402

FAM = os.path.join(W, "investigations/next-fstype/runs/families-fstype.tsv")
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"

# LangName 1033, as the hotfix left the name table: IDs 3 (unique ID) and 17
# (typographic subfamily) said Thin; everything else on the line is kept verbatim.
EXTRALIGHT = {
    "TitilliumWeb-ExtraLight": [
        ("setfield", "TTFWeight 275"),
        ("setfield", "FontName TitilliumWeb-ExtraLight"),
        ("setfield", "FullName Titillium Web ExtraLight"),
        ("setfield", 'LangName 1033 "" "" "" "1.001;UKWN;TitilliumWeb-ExtraLight" "" '
                     '"Version 1.001;PS 57.000;hotconv 1.0.70;makeotf.lib2.5.55311" "" "" "" "" "" '
                     '"" "" "This Font Software is licensed under the SIL Open Font License, Version '
                     '1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL" '
                     '"http://scripts.sil.org/OFL" "" "" "ExtraLight" '),
    ],
    "TitilliumWeb-ExtraLightItalic": [
        ("setfield", "TTFWeight 275"),
        ("setfield", "FontName TitilliumWeb-ExtraLightItalic"),
        ("setfield", "FullName Titillium Web ExtraLight Italic"),
        ("setfield", 'LangName 1033 "" "" "ExtraLight Italic" "1.001;UKWN;TitilliumWeb-ExtraLightItalic" "" '
                     '"Version 1.001;PS 57.000;hotconv 1.0.70;makeotf.lib2.5.55311" "" "" "" "" "" '
                     '"" "" "This Font Software is licensed under the SIL Open Font License, Version '
                     '1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL" '
                     '"http://scripts.sil.org/OFL" "" "" "ExtraLight Italic" '),
    ],
}


def setname(text, args):
    """PROTOTYPE sfd_edit.py op: setname <lang> <nameid> <value>. Replace the <nameid>-th
    quoted string of the `LangName: <lang> ...` line (FontForge writes one string per
    name ID, from 0). ASCII values without '+' only: LangName strings are UTF-7."""
    import re
    lang, nid, value = args.split(" ", 2)
    nid = int(nid)
    if any(ord(c) > 126 or c in '+"' for c in value):
        raise sfd_edit.EditError("setname: %r needs UTF-7 encoding" % value)
    m = re.search(r"^LangName: %s (.*)$" % re.escape(lang), text, re.M)
    if not m:
        raise sfd_edit.EditError("no LangName: %s line" % lang)
    toks = re.findall(r'"[^"]*"', m.group(1))
    if re.sub(r'"[^"]*"', "", m.group(1)).strip():
        raise sfd_edit.EditError("LangName %s has content outside quoted strings" % lang)
    while len(toks) <= nid:
        toks.append('""')
    before = toks[nid][1:-1]
    toks[nid] = '"%s"' % value
    line = "LangName: %s %s " % (lang, " ".join(toks))
    return text[:m.start()] + line + text[m.end():], before


def apply(text, op, args):
    if op == "setname":
        return setname(text, args)
    return sfd_edit.apply(text, op, args)


def version_ops(text):
    """Version 1.001 -> 1.002 exactly as the hotfix restated it, from the source's own
    strings (Black says PS 35.000, the others PS 57.000)."""
    v = sfd_edit.field_value(text, "Version")
    fn = sfd_edit.field_value(text, "FontName")
    if not v.startswith("1.001;"):
        raise sfd_edit.EditError("Version %r does not start with 1.001;" % v)
    nv = "1.002;" + v[len("1.001;"):]
    return [("setfield", "Version " + nv),
            ("setfield", "sfntRevision 0x00010083"),
            ("setname", "1033 3 1.002;UKWN;" + fn),
            ("setname", "1033 5 Version " + nv)]


def rows():
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]


def source(row):
    path = "%s/%s/%s" % (row["lic"], row["family"], row["source"])
    return subprocess.run(["git", "-C", "%s/%s.git" % (ARC, row["base"]), "show",
                           "%s:%s" % (row["commit"], path)], capture_output=True, check=True
                          ).stdout.decode("utf-8", "surrogateescape")


def ops_for(style, which):
    ops = [("setfield", "FSType 0")]
    if which == "extralight":
        if style not in EXTRALIGHT:
            return None
        ops += EXTRALIGHT[style]
    if which == "version":
        if not style.startswith("TitilliumWeb-"):
            return None
        ops += EXTRALIGHT.get(style, [])
        ops.append(("version", None))      # expanded against the text as edited so far
    return ops


def main():
    which, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for row in rows():
        ops = ops_for(row["style"], which)
        if ops is None:
            continue
        text = source(row)
        i = 0
        while i < len(ops):
            op, args = ops[i]
            if op == "version":
                ops[i:i + 1] = version_ops(text)
                op, args = ops[i]
            i += 1
            new, before = apply(text, op, args)
            if new == text:
                sys.exit("FATAL: %s %s %s changed nothing" % (row["style"], op, args))
            print("%s\t%s %s\tbefore=%r" % (row["style"], op, args[:60], before))
            text = new
        with open(os.path.join(outdir, row["style"] + ".sfd"), "w", encoding="utf-8",
                  errors="surrogateescape") as fh:
            fh.write(text)


if __name__ == "__main__":
    main()
