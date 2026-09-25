#!/usr/bin/env python3
"""Question answered (independent re-derivation for the adversarial check of unit
"heights"): for each style of the unit and its CLEAN siblings, what do the release,
the paired -TTF.sfd and the sibling src/<X>.otf in the SAME base tree actually say?

  release  : FFTM stamps (FontForge build, source created/modified), OS/2 version,
             sxHeight, sCapHeight, usWeightClass, head.fontRevision, U+00A0 advance
  .sfd     : CreationTime/ModificationTime, BeginPrivate present?, OS2 x/cap lines,
             TTFWeight, Ascent/Descent, the mu glyph's Encoding/AltUni2 lines
  .otf     : which .otf files exist in src/, the CFF FontName, the CFF Private
             BlueValues/OtherBlues exactly as fontTools reads them, OS/2 x/cap
  history  : the last base-tree commit that touched the .otf, the release .ttf and
             the .sfd (googlefontdirectory-hg mirror), so the .otf's BlueValues can be
             shown to predate (or not) the release they are claimed to have shaped.

Pairing: families-next.tsv (the pipeline's own table). Nothing is read from the
investigator's run outputs.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 facts.py > ../runs/facts.txt
"""
import io
import subprocess
import time

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/sfd-reland/families-next.tsv"
E1904 = 2082844800
STYLES = """KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular""".split()


def git(*a):
    return subprocess.run(["git", "-C", ARC, *a], capture_output=True, check=True).stdout


def rows():
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return {r["style"]: r for r in (dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh)}


def utc(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))


def last_commit(commit, path):
    out = git("log", "-1", "--format=%h %ad %s", "--date=short", commit, "--", path).decode().strip()
    n = len(git("log", "--format=%h", commit, "--", path).decode().split())
    return f"{out}  ({n} commit(s) touch it)"


def main():
    rs = rows()
    for s in STYLES:
        r = rs[s]
        d = f"{r['lic']}/{r['family']}"
        print("=" * 78)
        print(f"{s}  source {d}/{r['source']}  release {r['shipped']}")
        rel = TTFont(r["shipped"])
        if "FFTM" in rel:
            f = rel["FFTM"]
            print(f"  release FFTM build {utc(f.FFTimeStamp - E1904)}  src created "
                  f"{utc(f.sourceCreated - E1904)}  src modified {utc(f.sourceModified - E1904)}")
        else:
            print("  release has NO FFTM")
        o = rel["OS/2"]
        print(f"  release OS/2 v{o.version} sxHeight={getattr(o, 'sxHeight', None)} "
              f"sCapHeight={getattr(o, 'sCapHeight', None)} usWeightClass={o.usWeightClass} "
              f"fontRevision={rel['head'].fontRevision:.4f} "
              f"nbsp_adv={rel['hmtx'][rel.getBestCmap()[0xA0]][0] if 0xA0 in rel.getBestCmap() else None}")
        sfd = git("show", f"{r['commit']}:{d}/{r['source']}").decode("utf-8", "replace").split("\n")
        hdr = {}
        for line in sfd:
            if line.startswith("StartChar:") or line.startswith("BeginChars:"):
                break
            k = line.split(":", 1)[0]
            if k in ("CreationTime", "ModificationTime", "Ascent", "Descent", "TTFWeight",
                     "OS2Version", "OS2XHeight", "OS2CapHeight", "BeginPrivate", "FontName"):
                hdr[k] = line.split(":", 1)[1].strip()
        for k in ("CreationTime", "ModificationTime"):
            if k in hdr:
                hdr[k] += f" ({utc(int(hdr[k]))})"
        print(f"  sfd header {hdr}")
        # the mu glyph(s): primary and alternate encodings
        cur = None
        for line in sfd:
            if line.startswith("StartChar:"):
                cur = [line.strip()]
            elif cur is not None and (line.startswith("Encoding:") or line.startswith("AltUni2:")):
                cur.append(line.strip())
            elif line.startswith("EndChar") and cur is not None:
                if any("0003bc" in c or c.startswith("Encoding: 956 ") or c.startswith("Encoding: 181 ")
                       for c in cur):
                    print(f"  sfd glyph {' | '.join(cur)}")
                cur = None
        # sibling .otf files
        files = git("ls-tree", "--name-only", f"{r['commit']}:{d}/src/").decode().split()
        otfs = [x for x in files if x.lower().endswith(".otf")]
        want = r["source"].split("/")[-1].replace("-TTF.sfd", ".otf")
        print(f"  src/*.otf in base tree: {otfs}  (paired by name: {want})")
        for x in otfs:
            data = git("show", f"{r['commit']}:{d}/src/{x}")
            t = TTFont(io.BytesIO(data))
            if "CFF " not in t:
                print(f"    {x}: no CFF table")
                continue
            cff = t["CFF "].cff
            td = cff.topDictIndex[0]
            pr = td.Private
            bv = getattr(pr, "BlueValues", None)
            ob = getattr(pr, "OtherBlues", None)
            oo = t["OS/2"]
            ff = t["FFTM"].FFTimeStamp - E1904 if "FFTM" in t else None
            print(f"    {x}: CFF FontName={cff.fontNames[0]} BlueValues={bv} OtherBlues={ob} "
                  f"OS/2 v{oo.version} x={getattr(oo, 'sxHeight', None)} cap={getattr(oo, 'sCapHeight', None)} "
                  f"FFTM={utc(ff) if ff else None} UPM={t['head'].unitsPerEm}")
        rel_ttf = r["shipped"].split("/")[-1]
        for label, p in (("otf", f"{d}/src/{want}"), ("ttf", f"{d}/{rel_ttf}"),
                         ("sfd", f"{d}/{r['source']}")):
            print(f"  last commit touching {label}: {last_commit(r['commit'], p)}")


if __name__ == "__main__":
    main()
