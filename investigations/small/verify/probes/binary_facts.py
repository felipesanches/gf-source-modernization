#!/usr/bin/env python3
"""Questions answered:
 A. RussoOne: is the hg-era binary identical to google/fonts 90abd17b4, and did
    8ccda7bf7 change anything but OS/2.fsType (cmap mapping, head)?
 B. Tuffy Regular/Italic: FSType stated by both .sfd variants vs the hg-era binary and
    the release; and whether the release's OS/2 script/strikeout metrics look like a
    compiler's em-fraction defaults (0.65/0.6/0.075/0.35 em, truncated), i.e. not a
    FontForge export of this source (which carried the .sfd's garbage values verbatim).
Usage: gftools/venv/bin/python3 verify/probes/binary_facts.py
"""
import hashlib, io, subprocess
from fontTools.ttLib import TTFont
GF = "/home/fsanches/compartilhado/google/fonts"
HG = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
HGC = "52f780bc9d197280a9f430574e179a5f233c56b6"
def show(repo, rev, path):
    return subprocess.check_output(["git", "-C", repo, "show", "%s:%s" % (rev, path)])
def field(blob, name):
    for l in blob.decode("utf-8", "replace").split("\nStartChar:", 1)[0].splitlines():
        if l.startswith(name + ": "):
            return l.split(": ", 1)[1]
print("== A. RussoOne-Regular.ttf")
bl = {"hg@52f780bc": show(HG, HGC, "ofl/russoone/RussoOne-Regular.ttf")}
for r in ("90abd17b4", "8ccda7bf7", "HEAD"):
    bl["gf@" + r] = show(GF, r, "ofl/russoone/RussoOne-Regular.ttf")
for k, b in bl.items():
    f = TTFont(io.BytesIO(b))
    print("  %-14s sha1 %s fsType %d FFTM %s" % (k, hashlib.sha1(b).hexdigest()[:12], f["OS/2"].fsType, "FFTM" in f))
a, b = TTFont(io.BytesIO(bl["gf@90abd17b4"])), TTFont(io.BytesIO(bl["gf@8ccda7bf7"]))
raw = [t for t in a.reader.keys() if t not in b.reader or a.reader[t] != b.reader[t]]
os2 = [k for k in a["OS/2"].__dict__ if k != "panose" and a["OS/2"].__dict__[k] != b["OS/2"].__dict__.get(k)]
pan = vars(a["OS/2"].panose) == vars(b["OS/2"].panose)
print("  8ccda7bf7 vs parent: raw tables differ %s; OS/2 fields differ %s (panose equal %s); cmap mapping equal %s" % (
    raw, os2, pan, a.getBestCmap() == b.getBestCmap()))
print("  .sfd FSType: %s" % field(show(HG, HGC, "ofl/russoone/src/RussoOne-Regular-TTF.sfd"), "FSType"))
print("== B. Tuffy")
for s in ("Regular", "Italic"):
    print("  %s: -TTF.sfd FSType %s, plain .sfd FSType %s" % (s,
        field(show(HG, HGC, "ofl/tuffy/src/Tuffy-%s-TTF.sfd" % s), "FSType"),
        field(show(HG, HGC, "ofl/tuffy/src/Tuffy-%s.sfd" % s), "FSType")))
    for k, b in (("hg@52f780bc", show(HG, HGC, "ofl/tuffy/Tuffy-%s.ttf" % s)),
                 ("gf@ebcdfd2bb", show(GF, "ebcdfd2bb", "ofl/tuffy/Tuffy-%s.ttf" % s)),
                 ("gf@HEAD", show(GF, "HEAD", "ofl/tuffy/Tuffy-%s.ttf" % s))):
        f = TTFont(io.BytesIO(b)); o = f["OS/2"]; e = f["head"].unitsPerEm
        print("    %-12s fsType %d FFTM %-5s vendor %s name5 %r sub %d/%d/%d sup-yoff %d strike %d/%d (em fractions trunc: %d/%d/%d/%d)" % (
            k, o.fsType, "FFTM" in f, o.achVendID, f["name"].getDebugName(5), o.ySubscriptXSize, o.ySubscriptYSize,
            o.ySubscriptYOffset, o.ySuperscriptYOffset, o.yStrikeoutSize, o.yStrikeoutPosition,
            int(.65 * e), int(.6 * e), int(.075 * e), int(.35 * e)))
