import re
p='babelfont/src/filters/fontforgeos2defaults.rs'
s=open(p).read()
blocks=re.findall(r'<<<<<<< HEAD\n.*?>>>>>>> [^\n]*\n', s, re.S)
assert len(blocks)==1, len(blocks)
s=s.replace(blocks[0],'''                "Compute all ten OS/2 sub/superscript and strikeout metrics of a FontForge \\
                 source that states no OS2SubXSize, replacing any it states, and fill the \\
                 x-height, cap height and PANOSE it does not state, using the rules FontForge's \\
                 exporter uses (SFDefaultOS2SubSuper and SFDefaultOS2Info in tottf.c, \\
                 SFStandardHeight in splinefont.c). Use only to reproduce a binary FontForge \\
                 exported; a binary built by another compiler carries different values",
''')
def rep(old,new):
    global s
    assert s.count(old)==1, old
    s=s.replace(old,new)
rep('''/// A filter that fills in OS/2 values the way FontForge's exporter does: the ten
/// sub/superscript and strikeout metrics of a source that states no `OS2SubXSize`,
/// replacing any of them it does state, and the PANOSE the source does not state.
''','''/// A filter that fills in OS/2 values the way FontForge's exporter does: the ten
/// sub/superscript and strikeout metrics of a source that states no `OS2SubXSize`,
/// replacing any of them it does state, and the x-height, cap height and PANOSE the
/// source does not state.
''')
rep('''/// It also fills each of the x-height and cap height the source does not state,
/// measured from the outlines, as `setos2` in the same file does with `SFXHeight`
/// and `SFCapHeight` (see `fontforge_standard_height`).
''','''/// It also fills each of the x-height and cap height the source does not state,
/// measured from the outlines, as `setos2` in the same file does with `SFXHeight`
/// and `SFCapHeight` (see `fontforge_standard_height`). `setos2` writes the two only
/// into an OS/2 table of version 2 or later. A CFF export gets version 3, but a
/// TrueType export gets version 1 unless the source's `OS2Version:`,
/// `OS2_UseTypoMetrics` or `OS2_WeightWidthSlopeOnly` selects a later one, and then
/// the binary has neither field: the values filled here are FontForge's estimate, not
/// values found in that binary. FontForge before tag 20150430 measured the two even
/// when the source stated them.
''')
rep('''/// `pfminfo`, FontForge's record of the OS/2 values, before filling it, so the
/// exporter computes PANOSE and the ten values even when the source states them, and
/// derives the weight and width classes from the same name words as PANOSE. This
/// filter keeps the stated values and sets no weight or width class. FontForge's Font
/// Info dialog sets `pfmset` whenever it stores PANOSE or the ten, so only a source
/// edited by hand or written by another tool is affected.
''','''/// `pfminfo`, FontForge's record of the OS/2 values, before filling it, so the
/// exporter computes PANOSE, the ten values, the x-height and the cap height even
/// when the source states them, and derives the weight and width classes from the
/// same name words as PANOSE. This filter keeps the stated values and sets no weight
/// or width class. FontForge's Font Info dialog sets `pfmset` whenever it stores any
/// of those values, so only a source edited by hand or written by another tool is
/// affected.
''')
open(p,'w').write(s)
