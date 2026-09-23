"""Question: which blocking rows remain if table_gate's _abs_contour_area splits
contours at closePath/endPath instead of at moveTo? (The proposed gate fix; see
gate_area_split.py for why.) Runs the UNMODIFIED sfd-batch5/tools/table_gate.py
main() with only that one function replaced.
Usage: table_gate_closepath.py <d3.json> --fonts <shipped> <built>"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg


def _abs_contour_area(glyphs, name):
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    rec = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(rec)
    total, pen = 0.0, AreaPen()
    for op, args in rec.value:
        (getattr(pen, op)(*args) if args else getattr(pen, op)())
        if op in ("closePath", "endPath"):
            total += abs(pen.value)
            pen = AreaPen()
    return total


tg._abs_contour_area = _abs_contour_area
sys.argv = [tg.__file__] + sys.argv[1:]
tg.main()
