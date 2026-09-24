import os, subprocess, sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-reland/tools")
import recipe
OUT = sys.argv[1]
REPOS = "/home/fsanches/compartilhado/sfd-reland-repos"
os.makedirs(OUT, exist_ok=True)
for row in recipe.rows():
    p = os.path.join(OUT, row["style"] + ".orig.sfd")
    open(p, "w", encoding="utf-8", errors="replace").write(recipe.source_text(row))
    flags = recipe.flags_for(open(p, encoding="utf-8", errors="replace").read(), row["shipped"])
    open(p + ".flags", "w").write(" ".join(flags) + "\n")
    rd = os.path.join(REPOS, row["repo"])
    if not os.path.isdir(os.path.join(rd, ".git")):
        continue
    r = subprocess.run(["git", "-C", rd, "log", "--format=%H", "--grep=^Convert to .glyphs with babelfont"], capture_output=True, text=True)
    c = r.stdout.split()[0]
    q = os.path.join(OUT, row["style"] + ".landed.sfd")
    open(q, "wb").write(subprocess.run(["git", "-C", rd, "show", "%s^:%s" % (c, row["source"])], capture_output=True, check=True).stdout)
    flags = recipe.flags_for(open(q, encoding="utf-8", errors="replace").read(), row["shipped"])
    open(q + ".flags", "w").write(" ".join(flags) + "\n")
