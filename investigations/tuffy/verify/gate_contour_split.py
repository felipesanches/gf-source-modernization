#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".
Question it answers: does the table gate's verdict change if _abs_contour_area
delimits contours by closePath/endPath (every contour counted once, including a
TrueType contour with no on-curve point, which fontTools draws as
qCurveTo(..., None) + closePath WITHOUT a moveTo) instead of by moveTo?
Runs the unmodified sfd-batch5/tools/table_gate.py main() with only that function
swapped (independent re-implementation of the tuffy investigation's proposal).
Usage: gate_contour_split.py <d3.json> --fonts <shipped.ttf> <built.ttf>"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import DecomposingRecordingPen


def split_area(glyphs, name):
    rec = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(rec)
    contours, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            contours.append(cur)
            cur = []
    total = 0.0
    for c in contours:
        pen = AreaPen()
        for op, args in c:
            getattr(pen, op)(*args)
        total += abs(pen.value)
    return total


table_gate._abs_contour_area = split_area
sys.argv = [table_gate.__file__] + sys.argv[1:]
table_gate.main()
