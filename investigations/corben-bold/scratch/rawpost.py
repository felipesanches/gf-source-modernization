# Print the RAW post-table format-2 name of chosen glyph ids (no fontTools de-duplication).
import sys, struct
from fontTools.ttLib import TTFont
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder
f = TTFont(sys.argv[1]); raw = f.reader['post']
fmt, = struct.unpack('>L', raw[:4])
assert fmt == 0x00020000, hex(fmt)
n, = struct.unpack('>H', raw[32:34])
idx = struct.unpack('>%dH' % n, raw[34:34+2*n])
p = 34+2*n; extra = []
while p < len(raw):
    l = raw[p]; extra.append(raw[p+1:p+1+l].decode('latin1')); p += 1+l
names = [standardGlyphOrder[i] if i < 258 else extra[i-258] for i in idx]
from collections import Counter
c = Counter(names)
print('numGlyphs', n, 'duplicates', {k: v for k, v in c.items() if v > 1})
for g in map(int, sys.argv[2:]): print(g, names[g])
