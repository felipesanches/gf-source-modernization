import sys, math, re
from fontTools.ttLib import TTFont
def sfd_widths(p):
    out={}; name=None
    for line in open(p, encoding='latin-1'):
        if line.startswith('StartChar:'): name=line.split(':',1)[1].strip()
        elif line.startswith('Width:') and name: out[name]=int(line.split()[1])
        elif line.startswith('EndChar'): name=None
    return out
for s in ["Regular","Italic","Bold","BoldItalic"]:
    w=sfd_widths(f"mono/src/Puritan-{s}.sfd")
    f=TTFont(f"rel/Puritan-{s}.ttf"); hm=f['hmtx'].metrics
    o=TTFont(f"mono/src/Puritan-{s}.otf"); om=o['hmtx'].metrics
    sc=1024/1000
    res={'rint':0,'trunc':0,'floor':0,'ceil':0}; n=0; bad=[]
    for g,wd in w.items():
        if g not in hm: continue
        n+=1; r=hm[g][0]; x=wd*sc
        if r==round(x) if x-math.floor(x)!=0.5 else None: pass
        if r==int(math.floor(x+0.5)): res['rint']+=1
        if r==int(x): res['trunc']+=1
        if r==math.floor(x): res['floor']+=1
        if r==math.ceil(x): res['ceil']+=1
        if r!=int(math.floor(x+0.5)) and r!=int(x): bad.append((g,wd,x,r))
    otfok=sum(1 for g,wd in w.items() if g in om and om[g][0]==wd)
    print(s, 'glyphs', len(w), 'in release', n, res, 'otf==sfd', otfok, 'bad', bad[:5])
    # ambiguous count
    amb=sum(1 for g,wd in w.items() if g in hm and int(wd*sc)!=int(math.floor(wd*sc+0.5)))
    print('  distinguishing glyphs (trunc!=rint):', amb)
