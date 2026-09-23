# Compare the release cmap with the codepoints src/Corben-Bold.sfd assigns (Encoding + AltUni2).
import re,sys
from fontTools.ttLib import TTFont
t=open(sys.argv[1],encoding="latin1").read()
m={}
for b in re.finditer(r"^StartChar: (\S+)\n(.*?)^EndChar",t,re.S|re.M):
    n=b.group(1); body=b.group(2)
    e=re.search(r"^Encoding: (-?\d+) (-?\d+) (\d+)",body,re.M)
    u=int(e.group(2))
    if u>=0: m.setdefault(u,[]).append(n)
    for a in re.finditer(r"^AltUni2: (.*)$",body,re.M):
        for x in re.findall(r"([0-9a-f]+)\.([0-9a-f]+)\.([0-9a-f]+)",a.group(1)):
            m.setdefault(int(x[0],16),[]).append(n)
rel=TTFont(sys.argv[2]).getBestCmap()
print("sfd codepoints",len(m),"release",len(rel))
print("dup cp in sfd",{hex(k):v for k,v in m.items() if len(v)>1})
print("only sfd",sorted(hex(k) for k in m if k not in rel)[:20])
print("only rel",sorted(hex(k) for k in rel if k not in m)[:20])
diff={hex(k):(m[k][0],rel[k]) for k in m if k in rel and m[k][0]!=rel[k]}
print("name differs",len(diff),list(diff.items())[:10])
