#!/usr/bin/env python3
"""The table gate with the three changes the cardo unit proposes, as a wrapper.

Question answered: with sfd-batch5/tools/table_gate.py (2f43693) left untouched, what
does the gate report for a pair once
  1. an advance-width difference can no longer be hidden: expand_overflow() (a
     diffenator3 hmtx section replaced by "There are N changes, check manually!")
     also recomputes ADVANCES, and arbitrate_lsb() keeps a row BLOCKING when it also
     carries a "width" difference (probes/advance_audit.py: Cardo-Italic uni2E11 and
     uniF15B, Cardo-Regular uni0304 and uni05B105BD, Lohit-Tamil 7 glyphs were hidden);
  2. head.font_direction_hint is arbitrated: the release's value is RELEASE-STALE when
     it is not 2, ours is 2, the release carries an FFTM table stamped before FontForge
     722e7ea8873e (2017-12-23, "Skip Apple 'head' table fields in OpenType mode"), and
     the value is the one that code computed from the release's own cmap
     (probes/dirhint_oracle.py: 0 when the font maps both left-to-right and
     right-to-left characters, -2 when only right-to-left) with head.flags bit 9 set
     exactly when it saw a right-to-left glyph. The OpenType spec deprecates the field
     ("Deprecated (Set to 2)"); fontc, ufo2ft and FontForge >= 20190317 write 2, and
     neither harfrust 0.6.2 nor skrifa 0.47.0 reads it.
It is otherwise the same gate: same argv, same output format.

Usage:
  table_gate_proposed.py <d3.json> --fonts <shipped.ttf> <built.ttf>
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import datetime
import json
import os
import sys
import unicodedata

sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg  # noqa: E402

FF_722E7EA = datetime.datetime(2017, 12, 23, tzinfo=datetime.UTC)
UNIX_FROM_1904 = 2082844800


def _advances(path):
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    return {n: f["hmtx"][n][0] for n in f.getGlyphOrder()}


_orig_expand = tg.expand_overflow


def expand_overflow(rows, shipped, built):
    had_overflow = any(r.startswith("hmtx.error") and "changes" in r for r in rows)
    out = _orig_expand(rows, shipped, built)
    if had_overflow:
        s, b = _advances(shipped), _advances(built)
        for n in s:
            if n in b and s[n] != b[n]:
                out.append('hmtx.%s {"width": [%d, %d]}' % (n, s[n], b[n]))
    return out


_orig_lsb = tg.arbitrate_lsb


def arbitrate_lsb(rows, shipped, built):
    width_rows = [r for r in rows if r.startswith("hmtx.") and '"width"' in r]
    block, stale = _orig_lsb(rows, shipped, built)
    for r in width_rows:
        if r in block:
            continue
        # the lsb part may be the release's stale bearing; the advance is not
        head = r.split(" ", 1)[0]
        try:
            vals = json.loads(r.split(" ", 1)[1])
            block.append('%s {"width": %s}' % (head, json.dumps(vals["width"])))
        except Exception:
            block.append(r)
    return block, stale


def _dirhint_oracle(font):
    lr = rl = False
    for cp in (font.getBestCmap() or {}):
        bidi = unicodedata.bidirectional(chr(cp))
        if bidi in ("R", "AL") or 0x10800 <= cp <= 0x10FFF:
            rl = True
        elif (cp < 0x10000 and bidi == "L") or 0x10300 <= cp < 0x107FF:
            lr = True
    return (0 if (lr and rl) else -2 if rl else 2), rl


def arbitrate_direction_hint(rows, shipped, built):
    from fontTools.ttLib import TTFont
    block, stale = [], []
    for r in rows:
        if not r.startswith("head.font_direction_hint"):
            block.append(r)
            continue
        try:
            S, B = TTFont(shipped), TTFont(built)
            ship, ours = S["head"].fontDirectionHint, B["head"].fontDirectionHint
            stamp = None
            if "FFTM" in S:
                stamp = datetime.datetime.fromtimestamp(
                    S["FFTM"].FFTimeStamp - UNIX_FROM_1904, datetime.UTC)
            want, rl = _dirhint_oracle(S)
            bit9 = bool((S["head"].flags >> 9) & 1)
            ok = (ours == 2 and ship != 2 and stamp is not None and stamp < FF_722E7EA
                  and ship == want and bit9 == rl)
        except Exception:
            ok = False
        if ok:
            stale.append("head.font_direction_hint -- the release's %d is what FontForge "
                         "before 722e7ea8873e computed from its cmap (FFTM %s); the "
                         "field is deprecated (spec: set to 2) and no shaper reads it"
                         % (ship, stamp.date().isoformat()))
        else:
            block.append(r)
    return block, stale


_orig_post = tg.arbitrate_post_version


def arbitrate_post_version(rows, shipped, built):
    rows, stale = _orig_post(rows, shipped, built)
    rows, more = arbitrate_direction_hint(rows, shipped, built)
    return rows, stale + more


tg.expand_overflow = expand_overflow
tg.arbitrate_lsb = arbitrate_lsb
tg.arbitrate_post_version = arbitrate_post_version

if __name__ == "__main__":
    tg.main()
