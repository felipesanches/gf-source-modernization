"""Question: which glyphs make up the gate's 'hmtx.N bearings differ though both
fonts agree with their own outlines' row? Same computation as
table_gate.expand_overflow (glyphs keyed by NAME, both bearings self-consistent,
lsb differs), listing each with its composite structure on both sides.
Usage: hmtx_outline_led.py <shipped.ttf> <built.ttf>"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
from fontTools.ttLib import TTFont
S, B = sys.argv[1:3]
ship, ours = tg._self_consistent_lsbs(S), tg._self_consistent_lsbs(B)
fs, fb = TTFont(S), TTFont(B)
def comp(f, n):
    g = f["glyf"][n]
    return [(c.glyphName, c.x, c.y) for c in g.components] if g.isComposite() else "simple"
n = 0
for name, (s_lsb, s_xmin) in ship.items():
    if name not in ours or s_xmin is None: continue
    o_lsb, o_xmin = ours[name]
    if o_xmin is None or s_lsb == o_lsb: continue
    if o_lsb == o_xmin and s_lsb == s_xmin:
        n += 1
        print("%-14s release lsb %5d  ours %5d  adv %d/%d  release %s  ours %s" % (
            name, s_lsb, o_lsb, fs["hmtx"][name][0], fb["hmtx"][name][0], comp(fs, name), comp(fb, name)))
print("outline-led bearing differences:", n)
