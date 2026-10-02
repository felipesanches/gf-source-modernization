#!/usr/bin/env python3
"""Question answered: do tools/sfd_edit.py's `truncateanchors` and `sfdlibinterpolated`
do exactly what their docstrings say on a tiny .sfd, and refuse what they do not model?

Each test states its fixture and the expected text. Prints one line per test and exits 1
on the first failure:
  python3 tools/probes/exporter_source_edits/test_ops.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import sfd_edit  # noqa: E402

HEAD = """SplineFontDB: 3.2
FontName: Test
Ascent: 800
Descent: 200
LayerCount: 2
Layer: 0 1 "Back" 1
Layer: 1 1 "Fore" 0
BeginChars: 2 2
"""


def glyph(name, enc, body):
    return "\nStartChar: %s\nEncoding: %d %d %d\nWidth: 500\nLayerCount: 2\n%sEndChar\n" % (
        name, enc, enc, enc - 97, body)


def check(name, got, want):
    if got != want:
        print("FAIL %s\n--- got\n%s\n--- want\n%s" % (name, got, want))
        sys.exit(1)
    print("ok   %s" % name)


def refuses(name, text, op, args=""):
    try:
        sfd_edit.apply(text, op, args)
    except sfd_edit.EditError as e:
        print("ok   %s (EditError: %s)" % (name, e))
        return
    print("FAIL %s: no EditError" % name)
    sys.exit(1)


def test_truncateanchors():
    src = HEAD + glyph("a", 97, 'AnchorPoint: "top" 129.5 -46.7 basechar 0\n'
                                'AnchorPoint: "bot" 250 0 basechar 0\n'
                                'AnchorPoint: "lig" -0.5 600.9 baselig 1\n'
                                'AnchorPoint: "pt" 10.99 20 basechar 0 3\n'
                                'Fore\nSplineSet\n0 0 m 1,0,-1\n 100 0 l 1,1,-1\n 0 0 l 1,0,-1\nEndSplineSet\n')
    new, before = sfd_edit.apply(src, "truncateanchors", "")
    want = (src.replace("129.5 -46.7", "129 -46").replace("-0.5 600.9", "0 600")
            .replace("10.99 20 basechar 0 3", "10 20 basechar 0 3"))
    check("truncateanchors: toward zero, integers and the rest of the line kept", new, want)
    check("truncateanchors: reports the count", before.split(",")[0], "3 anchor(s) with fractional coordinates")
    refuses("truncateanchors: nothing fractional", want, "truncateanchors")


# A quadratic square-ish contour: the closing segment ends unflagged on the start point;
# (200,100) is flagged 0x80 between controls (200,0) and (200,200).
QUAD = ("Fore\nSplineSet\n"
        "0 0 m 1,0,-1\n"
        " 100 0 l 1,1,2\n"
        " 200 0 200 0 200 100 c 128,-1,3\n"
        " 200 200 200 200 100 200 c 0,4,5\n"
        " 0 200 0 200 0 0 c 1,0,-1\n"
        "EndSplineSet\n")


def test_sfdlibinterpolated_middle_point():
    src = HEAD + glyph("a", 97, QUAD)
    new, before = sfd_edit.apply(src, "sfdlibinterpolated", "")
    # (200,100) becomes a control point; the implied on-curve points at the midpoints of
    # (200,0)-(200,100) and (200,100)-(200,200) are written out, flagged 128, number -1;
    # the new control gets 6, the first unused number.
    want = src.replace(" 200 0 200 0 200 100 c 128,-1,3\n",
                       " 200 0 200 0 200 50 c 128,-1,6\n 200 100 200 100 200 150 c 128,-1,3\n")
    check("sfdlibinterpolated: flagged point becomes a control between two implied points", new, want)
    check("sfdlibinterpolated: report", before, "1 on-curve point(s) flagged 0x80 in 1 glyph(s): a")


def test_sfdlibinterpolated_start_point():
    # the closing segment is flagged: sfdLib makes the contour's first point (100,100) an
    # off-curve point; the contour then starts at its first stated on-curve point (0,0),
    # where the release's starts (ufo2ft draws through a segment pen, which moves there)
    quad = ("Fore\nSplineSet\n"
            "100 100 m 128,-1,1\n"
            " 100 0 100 0 0 0 c 0,2,3\n"
            " -100 0 -100 0 -100 100 c 0,4,5\n"
            " -100 200 -100 200 0 200 c 0,6,7\n"
            " 100 200 100 200 100 100 c 128,-1,1\n"
            "EndSplineSet\n")
    src = HEAD + glyph("o", 111, quad)
    new, _ = sfd_edit.apply(src, "sfdlibinterpolated", "")
    want = src.replace(quad, "Fore\nSplineSet\n"
                       "0 0 m 0,2,3\n"
                       " -100 0 -100 0 -100 100 c 0,4,5\n"
                       " -100 200 -100 200 0 200 c 0,6,7\n"
                       " 100 200 100 200 100 150 c 128,-1,8\n"
                       " 100 100 100 100 100 50 c 128,-1,1\n"
                       " 100 0 100 0 0 0 c 0,2,3\n"
                       "EndSplineSet\n")
    check("sfdlibinterpolated: flagged closing segment, contour restarts at its first stated on-curve point",
          new, want)


def test_sfdlibinterpolated_exact_midpoint():
    quad = QUAD.replace(" 200 0 200 0 200 100 c 128,-1,3", " 200 0.1 200 0.1 200 100 c 128,-1,3")
    new, _ = sfd_edit.apply(HEAD + glyph("a", 97, quad), "sfdlibinterpolated", "")
    # (0.1 + 100) / 2 written so that it reads back as exactly that double
    check("sfdlibinterpolated: midpoint written exactly", " 200 0.1 200 0.1 200 50.05 c 128,-1,6" in new, True)


def test_sfdlibinterpolated_keeps_position():
    # a flagged point off the unit grid becomes a control point at exactly the same place
    # (sfdLib does not round; the compiler does)
    quad = QUAD.replace(" 200 0 200 0 200 100 c 128,-1,3", " 201 -1 201 -1 200.5 -0.5 c 128,-1,3")
    new, _ = sfd_edit.apply(HEAD + glyph("a", 97, quad), "sfdlibinterpolated", "")
    check("sfdlibinterpolated: point kept where it is, midpoints exact",
          " 201 -1 201 -1 200.75 -0.75 c 128,-1,6\n 200.5 -0.5 200.5 -0.5 200.25 99.75 c 128,-1,3" in new, True)


def test_sfdlibinterpolated_refusals():
    refuses("sfdlibinterpolated: nothing flagged", HEAD + glyph("a", 97, QUAD.replace("c 128,-1,3", "c 0,2,3")),
            "sfdlibinterpolated")
    refuses("sfdlibinterpolated: cubic Fore layer", (HEAD + glyph("a", 97, QUAD)).replace('Layer: 1 1 "Fore"', 'Layer: 1 0 "Fore"'),
            "sfdlibinterpolated")
    refuses("sfdlibinterpolated: TrueType instructions",
            HEAD + glyph("a", 97, QUAD + "TtInstrs:\nNPUSHB\nEndTTInstrs\n"), "sfdlibinterpolated")
    refuses("sfdlibinterpolated: open contour",
            HEAD + glyph("a", 97, QUAD.replace(" 0 200 0 200 0 0 c 1,0,-1\n", "")), "sfdlibinterpolated")


if __name__ == "__main__":
    test_truncateanchors()
    test_sfdlibinterpolated_middle_point()
    test_sfdlibinterpolated_start_point()
    test_sfdlibinterpolated_exact_midpoint()
    test_sfdlibinterpolated_keeps_position()
    test_sfdlibinterpolated_refusals()
