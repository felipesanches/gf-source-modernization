#!/usr/bin/env python3
"""Review harness (disposable): print the glyph names in a TTF's post table (format 2.0),
to check whether a compile kept the source's names (mu) or used production ones (uni03BC)."""
import struct, sys
d = open(sys.argv[1], 'rb').read()
n = struct.unpack('>H', d[4:6])[0]
tables = {d[12+16*i:16+16*i].decode('latin1'): struct.unpack('>II', d[20+16*i:28+16*i]) for i in range(n)}
off, ln = tables['post']
p = d[off:off+ln]
fmt = struct.unpack('>I', p[:4])[0]
if fmt != 0x20000:
    print('post format', hex(fmt)); sys.exit()
ng = struct.unpack('>H', p[32:34])[0]
idx = struct.unpack('>%dH' % ng, p[34:34+2*ng])
pos = 34 + 2*ng; extra = []
while pos < len(p):
    l = p[pos]; extra.append(p[pos+1:pos+1+l].decode('latin1')); pos += 1+l
for i in idx:
    print(extra[i-258] if i >= 258 else '#std%d' % i)
