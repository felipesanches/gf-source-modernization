#!/usr/bin/env python3
"""Question answered: is each paired src/<X>-TTF.sfd a re-import of the released TTF
(googlefontdirectory-hg tools/nonhinting/ttf2sfd.py, the last FontForge step in
tools/generate/HOWTOGEN.txt), rather than the font the release was exported from?

If it is, whatever a TTF cannot carry -- a PostScript private dictionary with its
BlueValues -- was in the FontForge session that exported the release (it had opened
src/<X>.otf) but is absent from the -TTF.sfd.

Three independent checks per style (pairing: families-next.tsv):
  times  the .sfd CreationTime/ModificationTime equal the release FFTM
         sourceCreated/sourceModified. FontForge's TTF import reads those two dates
         from FFTM when it is present (parsettf.c readttfhead at b69c9652: fseek to
         fftm_start+12, readdate x2), so a re-import inherits them.
  prep   the .sfd's TtTable prep is the release's prep (setnonhinting-fonttools.py
         added PUSHW 511 SCANCTRL PUSHB 4 SCANTYPE to the TTF after FontForge made it)
         and its GaspTable is the release's gasp.
  glyf   for every glyph in both, the advance and the bounding box of all the .sfd's
         points (on- and off-curve, own contours only) equal the release's hmtx
         advance and the bounding box of the release glyf's points (not the glyf
         header, which FontForge writes from the curves); glyphs with references
         are counted separately, not compared.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 provenance.py > ../runs/provenance.txt
"""
import re
import subprocess

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/gf-source-modernization/families-next.tsv"
E1904 = 2082844800
UNIT = """KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular""".split()


def rows():
    out = {}
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            out[r["style"]] = r
    return out


def sfd_glyphs(text):
    """name -> (width, bbox of own points or None, has_refs)"""
    out = {}
    for m in re.finditer(r"^StartChar: (.*?)\n(.*?)^EndChar", text, re.S | re.M):
        name, body = m.group(1).strip(), m.group(2)
        w = re.search(r"^Width: (-?\d+)", body, re.M)
        pts = []
        fore = True
        inspl = False
        for line in body.split("\n"):
            s = line.strip()
            if s == "Fore" or s.startswith("Layer: 1"):
                fore = True
            elif s == "Back" or (s.startswith("Layer:") and not s.startswith("Layer: 1")):
                fore = False
            elif s == "SplineSet":
                inspl = True
            elif s == "EndSplineSet":
                inspl = False
            elif inspl and fore:
                tok = s.split()
                k = next((i for i, t in enumerate(tok) if t in ("m", "l", "c")), None)
                if k is None:
                    continue
                v = [float(t) for t in tok[:k]]
                pts += list(zip(v[0::2], v[1::2]))
        refs = bool(re.search(r"^Refer:", body, re.M))
        bbox = None
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        out[name] = (int(w.group(1)) if w else None, bbox, refs)
    return out


def sfd_prep(text):
    m = re.search(r"^TtTable: prep\n(.*?)^EndTTInstrs", text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else None


def main():
    rs = rows()
    for s in UNIT:
        r = rs[s]
        text = subprocess.run(["git", "-C", ARC, "show", "%s:%s/%s/%s" % (r["commit"], r["lic"], r["family"], r["source"])],
                              capture_output=True, check=True).stdout.decode("utf-8", "replace")
        rel = TTFont(r["shipped"])
        ff = rel["FFTM"]
        ct = int(re.search(r"^CreationTime: (\d+)", text, re.M).group(1))
        mt = int(re.search(r"^ModificationTime: (\d+)", text, re.M).group(1))
        times = (ct, mt) == (ff.sourceCreated - E1904, ff.sourceModified - E1904)
        rprep = " ".join(rel["prep"].program.getAssembly()).replace("[]", "") if "prep" in rel else None
        sprep = sfd_prep(text)
        def norm(x):   # opcode names and pushed values only
            if x is None:
                return None
            x = re.sub(r"/\*.*?\*/", " ", x).replace("[ ]", " ").replace("[]", " ")
            x = re.sub(r"_1\b", "", x)
            return " ".join(x.split())
        prep = norm(sprep) is not None and norm(sprep) == norm(rprep)
        gasp_s = re.search(r"^GaspTable: (.*)$", text, re.M)
        gasp_r = rel["gasp"].gaspRange if "gasp" in rel else None
        gl = sfd_glyphs(text)
        glyf, hm = rel["glyf"], rel["hmtx"]
        same = diff = refd = missing = 0
        firstdiff = []
        for name in rel.getGlyphOrder():
            if name not in gl:
                missing += 1
                continue
            w, bbox, refs = gl[name]
            g = glyf[name]
            if refs or g.isComposite():
                refd += 1
                continue
            if g.numberOfContours == 0:
                rb = None
            else:   # the points themselves: FontForge writes the glyf header bbox from
                    # the curves, not the points, so the header is not comparable
                co = g.getCoordinates(glyf)[0]
                rb = (min(x for x, _ in co), min(y for _, y in co),
                      max(x for x, _ in co), max(y for _, y in co))
            if w == hm[name][0] and rb == bbox:
                same += 1
            else:
                diff += 1
                if len(firstdiff) < 3:
                    firstdiff.append((name, w, hm[name][0], bbox, rb))
        print("%-28s times=%s prep=%s (%r) gasp sfd=%r rel=%r" % (
            s, times, prep, norm(rprep), gasp_s and gasp_s.group(1), gasp_r))
        print("%-28s glyf: %d glyphs same advance+bbox, %d differ, %d with references (not compared), "
              "%d release glyphs absent from the .sfd; sfd has %d glyphs, release %d%s" % (
                  "", same, diff, refd, missing, len(gl), len(rel.getGlyphOrder()),
                  ("  first differences: %s" % firstdiff) if firstdiff else ""))


if __name__ == "__main__":
    main()
