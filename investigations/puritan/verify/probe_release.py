import sys, time, struct
from fontTools.ttLib import TTFont
def ts(t): return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
for p in sys.argv[1:]:
    f = TTFont(p)
    h = f['head']; o = f['OS/2']; hh = f['hhea']; post = f['post']
    ff = f.reader['FFTM'] if 'FFTM' in f else None
    fft = ''
    if ff:
        ver, = struct.unpack('>L', ff[:4])
        a,b,c = struct.unpack('>qqq', ff[4:28])
        epoch = -2082844800
        fft = 'FFTM v%d FFTimeStamp %s created %s modified %s' % (ver, ts(a+epoch), ts(b+epoch), ts(c+epoch))
    print(p.split('/')[-2] + '/' + p.split('/')[-1], 'upm', h.unitsPerEm, 'bbox', h.xMin, h.yMin, h.xMax, h.yMax,
          'fsType', o.fsType, 'os2v', o.version, 'wc', o.usWeightClass, 'xh/cap', getattr(o,'sxHeight',None), getattr(o,'sCapHeight',None),
          'typo', o.sTypoAscender, o.sTypoDescender, 'win', o.usWinAscent, o.usWinDescent, 'hhea', hh.ascent, hh.descent,
          'upos/uth', post.underlinePosition, post.underlineThickness, 'head.mod', ts(h.modified-2082844800))
    print('   ', fft, sorted(f.keys()))
