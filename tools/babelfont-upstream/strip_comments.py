import sys,re
src=open(sys.argv[1]).read()
out=[]
for line in src.splitlines():
    s=line.strip()
    if s.startswith('//'): continue
    # strip trailing // comment not inside string (crude: only if no quote after)
    m=re.search(r'\s//\s', line)
    if m and line[:m.start()].count('"')%2==0:
        line=line[:m.start()]
    if line.strip()=='' : continue
    out.append(line.rstrip())
print('\n'.join(out))
