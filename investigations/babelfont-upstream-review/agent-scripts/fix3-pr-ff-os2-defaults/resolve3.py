import re,sys
p='babelfont/src/filters/fontforgeos2defaults.rs'
s=open(p).read()
blocks=re.findall(r'<<<<<<< HEAD\n.*?>>>>>>> [^\n]*\n', s, re.S)
assert len(blocks)==2, len(blocks)
doc='''/// It also fills PANOSE, as `SFDefaultOS2Info` in the same file does.
/// `SFDefaultOS2Simple` starts it at [2, 0, 5, 3, 0 ...]. `OS2WeightCheck` sets byte
/// 2 from the `Weight:` name and then from the PostScript font name, so a match in
/// the font name wins: medi 6; demi, halb, or semi with bold 7; bold, fett or gras 8;
/// heavy 9; black 10; nord 11; thin 2; extra or light 3. The font name also sets byte
/// 0 to 3 when it contains "script" but not "sans", and byte 3 from its width words:
/// ultra or extra with condensed 8; condensed or narrow 6; ultra or extra with
/// expanded 7; expanded 5. When every glyph FontForge would output has the same
/// advance (`CIDOneWidth`, up to tag 20230101), byte 3 is 9 and byte 0 stays 2. All
/// words match without regard to case, anywhere in the name. So `Weight: Medium`
/// with a font name that matches nothing gives [2, 0, 6, 3, 0 ...].
///
/// A PANOSE the source states is never overwritten.
///
/// # Not modelled: a source that does not set `pfmset`
///
/// Any of the lines `PfmFamily:`, `TTFWeight:`, `PfmWeight:`, `TTFWidth:`, `LineGap:`
/// and `VLineGap:` sets FontForge's `pfmset`. Without one, `SFDefaultOS2Info` resets
/// `pfminfo`, FontForge's record of the OS/2 values, before filling it, so the
/// exporter computes PANOSE and the ten values even when the source states them, and
/// derives the weight and width classes from the same name words as PANOSE. This
/// filter keeps the stated values and sets no weight or width class. FontForge's Font
/// Info dialog sets `pfmset` whenever it stores PANOSE or the ten, so only a source
/// edited by hand or written by another tool is affected.
'''
helptext='''                "Compute all ten OS/2 sub/superscript and strikeout metrics of a FontForge \\
                 source that states no OS2SubXSize, replacing any it states, and fill the \\
                 PANOSE it does not state, using the rules FontForge's exporter uses \\
                 (SFDefaultOS2SubSuper and SFDefaultOS2Info in tottf.c). Use only to reproduce \\
                 a binary FontForge exported; a binary built by another compiler carries \\
                 different values",
'''
s=s.replace(blocks[0],doc).replace(blocks[1],helptext)
old='''/// A filter that computes the ten OS/2 sub/superscript and strikeout metrics the way
/// FontForge's exporter does for a source that states no `OS2SubXSize`, replacing
/// any of them the source does state.
'''
new='''/// A filter that fills in OS/2 values the way FontForge's exporter does: the ten
/// sub/superscript and strikeout metrics of a source that states no `OS2SubXSize`,
/// replacing any of them it does state, and the PANOSE the source does not state.
'''
assert s.count(old)==1
s=s.replace(old,new)
open(p,'w').write(s)
