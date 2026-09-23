#!/usr/bin/env python3
"""Apply candidate .sfd edits to a COPY of a Tuffy source, for testing with
tools/baseline.sh SRC_OVERRIDE=... Never touches the archive or any repo.

Question it answers: does a given list of edits close the gate rows it is
meant to close, and only those?

Usage: apply_edits.py <in.sfd> <out.sfd> <edits.tsv>
edits.tsv: one edit per line, TAB-separated: op, then args; '#' comments.
ops:
  setfield <Field> <value>            replace the one existing "Field: ..." line
                                      (same semantics as sfd-batch5/tools/
                                      source_corrections.py setfield)
  addfield <Field> <value>            insert after FontName: (source_corrections.py addfield)
  setencoding <glyph> <slot> <uni>    rewrite that glyph's "Encoding: slot uni gid"
                                      line, keeping its gid (PROPOSED new op)
  setrefer <glyph> <n> <dx> <dy>      set the translation of the glyph's n-th
                                      (1-based) "Refer:" line (PROPOSED new op)
  setwidth <glyph> <w>                set the glyph's "Width:" (PROPOSED new op)
  translateglyph <glyph> <dx> <dy>   move the glyph's outline (PROPOSED new op)
  ffnotdef                            TEST-ONLY emulation of the proposed
                                      converter change: add the .notdef that
                                      FontForge's TTF exporter synthesises when a
                                      font has none (tottf.c dumpmissingglyph)
Every op is FATAL if it cannot apply exactly once.
"""
import re
import sys


def glyph_block(text, name):
    m = re.search(r"^StartChar: %s\n.*?^EndChar\n" % re.escape(name), text, re.M | re.S)
    if not m:
        sys.exit("FATAL: no glyph %s" % name)
    return m


def ffnotdef(text):
    """FontForge 2011/2012 tottf.c dumpmissingglyph(): stem = strtod(StdVW) or
    strtod(StdHW); a PostScript array "[70]" parses as 0, so stem falls back to
    (ascent+descent)/30 (integer division). ymax = 2*(a+d)/3 capped at ascent;
    xmax = 5*stem + (a+d)/10 + stem; advance = xmax + 2*stem; lsb = stem."""
    if re.search(r"^StartChar: \.notdef$", text, re.M):
        sys.exit("FATAL: font already has a .notdef")
    asc = int(re.search(r"^Ascent: (\d+)", text, re.M).group(1))
    dsc = int(re.search(r"^Descent: (\d+)", text, re.M).group(1))
    em = asc + dsc

    def ps(key):
        m = re.search(r"^%s \d+ (.*)$" % key, text, re.M)
        if not m:
            return None
        try:
            return float(m.group(1).strip())      # C strtod: "[70]" -> 0
        except ValueError:
            return 0.0
    v = ps("StdVW")
    stem = int(v if v is not None else (ps("StdHW") or 0))
    if stem <= 0:
        stem = em // 30
    ymax = min(2 * em // 3, asc)
    xmax = 5 * stem + em // 10 + stem
    width = xmax + 2 * stem
    outer = [(stem, 0), (stem, ymax), (xmax, ymax), (xmax, 0)]
    inner = [(2 * stem, stem), (xmax - stem, stem), (xmax - stem, ymax - stem), (2 * stem, ymax - stem)]
    lines = []
    for c in (outer, inner):
        lines.append("%d %d m 1" % c[0])
        for p in c[1:] + [c[0]]:
            lines.append(" %d %d l 1" % p)
    slots = [int(x) for x in re.findall(r"^Encoding: (\d+) ", text, re.M)]
    gids = [int(x) for x in re.findall(r"^Encoding: \d+ -?\d+ (\d+)", text, re.M)]
    block = ("StartChar: .notdef\nEncoding: %d -1 %d\nWidth: %d\nFlags: HMW\nLayerCount: 2\n"
             "Fore\nSplineSet\n%s\nEndSplineSet\nEndChar\n\n"
             % (max(slots) + 1, max(gids) + 1, width, "\n".join(lines)))
    # Appended LAST: babelfont resolves "Refer: <index> ..." by the glyph's
    # position in the file, so inserting anywhere else re-targets every
    # reference behind it (an earlier try that inserted it first made
    # fontc overflow its stack on the resulting reference cycles).
    m = re.search(r"^BeginChars: (\d+) (\d+)$", text, re.M)
    text = (text[:m.start()] + "BeginChars: %d %d" % (int(m.group(1)) + 1, int(m.group(2)) + 1)
            + text[m.end():])
    e = list(re.finditer(r"^EndChars$", text, re.M))
    if len(e) != 1:
        sys.exit("FATAL: %d EndChars lines" % len(e))
    text = text[:e[0].start()] + block + text[e[0].start():]
    print("ffnotdef: stem %d, advance %d, outer %s" % (stem, width, outer))
    return text


def main():
    src, dst, tsv = sys.argv[1:4]
    text = open(src, encoding="utf-8", errors="surrogateescape").read()
    for line in open(tsv):
        if not line.strip() or line.startswith("#"):
            continue
        op, *args = line.rstrip("\n").split("\t")
        if op == "setfield":
            field, value = args
            pat = re.compile(r"^%s: .*$" % re.escape(field), re.M)
            if len(pat.findall(text)) != 1:
                sys.exit("FATAL setfield %s: %d lines" % (field, len(pat.findall(text))))
            old = pat.search(text).group(0)
            text = pat.sub("%s: %s" % (field, value), text, count=1)
            print("setfield: %s -> %s: %s" % (old, field, value))
        elif op == "addfield":
            # same semantics as source_corrections.py addfield
            field, value = args
            if re.search(r"^%s: " % re.escape(field), text, re.M):
                sys.exit("FATAL addfield %s: already present" % field)
            text = re.sub(r"^(FontName: .*)$", lambda mm: "%s\n%s: %s" % (mm.group(1), field, value),
                          text, count=1, flags=re.M)
            print("addfield: %s: %s" % (field, value))
        elif op in ("setencoding", "setrefer", "setwidth"):
            m = glyph_block(text, args[0])
            block = m.group(0)
            if op == "setencoding":
                slot, uni = args[1:]
                new, n = re.subn(r"^Encoding: \S+ \S+ (\d+)$",
                                 lambda e: "Encoding: %s %s %s" % (slot, uni, e.group(1)), block, count=1, flags=re.M)
            elif op == "setwidth":
                new, n = re.subn(r"^Width: -?\d+$", "Width: %s" % args[1], block, count=1, flags=re.M)
            else:
                idx, dx, dy = int(args[1]), args[2], args[3]
                refs = list(re.finditer(r"^Refer: (\S+ \S+ \S+ \S+ \S+ \S+ \S+) (\S+) (\S+) (.*)$", block, re.M))
                if idx > len(refs):
                    sys.exit("FATAL setrefer %s: only %d refs" % (args[0], len(refs)))
                r = refs[idx - 1]
                new = block[:r.start()] + "Refer: %s %s %s %s" % (r.group(1), dx, dy, r.group(4)) + block[r.end():]
                n = 1
            if n != 1:
                sys.exit("FATAL %s %s" % (op, args))
            text = text[:m.start()] + new + text[m.end():]
            print("%s: %s" % (op, " ".join(args)))
        elif op == "translateglyph":
            # translateglyph <glyph> <dx> <dy>: move every SplineSet point of the
            # glyph (PROPOSED new op; FATAL on references, anchors or hints,
            # which would need moving too)
            name, dx, dy = args[0], float(args[1]), float(args[2])
            m = glyph_block(text, name)
            block = m.group(0)
            if re.search(r"^(Refer|AnchorPoint|HStem|VStem|DStem2|TtInstrs):", block, re.M):
                sys.exit("FATAL translateglyph %s: glyph has refs/anchors/hints" % name)
            ss = re.search(r"^SplineSet\n(.*?)^EndSplineSet$", block, re.M | re.S)

            def mv(line):
                t = line.split()
                k = next(i for i, x in enumerate(t) if x in ("m", "l", "c"))
                nums = [float(x) for x in t[:k]]
                nums = [v + (dx if i % 2 == 0 else dy) for i, v in enumerate(nums)]
                lead = line[:len(line) - len(line.lstrip())]
                return lead + " ".join("%g" % v for v in nums) + " " + " ".join(t[k:])
            body = "\n".join(mv(l) for l in ss.group(1).rstrip("\n").split("\n")) + "\n"
            block = block[:ss.start(1)] + body + block[ss.end(1):]
            text = text[:m.start()] + block + text[m.end():]
            print("translateglyph: %s by (%g, %g)" % (name, dx, dy))
        elif op == "ffnotdef":
            text = ffnotdef(text)
        else:
            sys.exit("FATAL unknown op %s" % op)
    open(dst, "w", encoding="utf-8", errors="surrogateescape").write(text)


if __name__ == "__main__":
    main()
