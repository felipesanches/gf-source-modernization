#!/usr/bin/env python3
"""fstype_history.py -- where does each shipped OS/2.fsType (and usWeightClass) come from?

Question answered: for every Titillium Web and Wallpoet binary, what did each
revision of the file in google/fonts (and the binary committed next to the sources
in the googlefontdirectory-hg monorepo) state for OS/2.fsType, usWeightClass,
head.fontRevision, the FontForge build stamp (FFTM) and the PostScript name, and
what does the paired .sfd state (FSType, TTFWeight, Version, FontName)?

A shipped value that the .sfd and the FontForge export of it do not carry, and that
appears in google/fonts only at a later commit that touched the binary, is a
release edit -- the .sfd edit reproducing it must cite that commit.

Signals read:
  OS/2.fsType          0 = installable, 4 = preview & print, 8 = editable
  OS/2.usWeightClass   as stated
  FFTM.version / FFTM.FFTimeStamp  FontForge build stamp (tools/recipe.py fontforge_build())
  FFTM.sourceModified  the ModificationTime of the .sfd the binary was exported from
                       (printed as src_mod, Unix time); equal to the .sfd's own
                       ModificationTime: means "exported from exactly this .sfd state"
  .sfd header lines    FSType:, TTFWeight:, Version:, FontName:, ModificationTime:

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 \
    investigations/next-fstype/probes/fstype_history.py > investigations/next-fstype/runs/fstype_history.txt
"""
import datetime
import io
import re
import subprocess

from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts"
HG = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
HG_BASE = "52f780bc9d197280a9f430574e179a5f233c56b6"   # families-next.tsv base commit

FAMILIES = {
    "ofl/titilliumweb": ["Black", "Bold", "BoldItalic", "ExtraLight", "ExtraLightItalic", "Italic",
                         "Light", "LightItalic", "Regular", "SemiBold", "SemiBoldItalic"],
    "ofl/wallpoet": ["Regular"],
}
PREFIX = {"ofl/titilliumweb": "TitilliumWeb", "ofl/wallpoet": "Wallpoet"}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, check=True).stdout


def facts(blob):
    f = TTFont(io.BytesIO(blob))
    os2 = f["OS/2"]
    ff = "-"
    if "FFTM" in f:
        ts = f["FFTM"].FFTimeStamp - 2082844800
        ff = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
        ff += " src_mod=%d" % (f["FFTM"].sourceModified - 2082844800)
    ps = f["name"].getDebugName(6)
    return "fsType=%-2d weight=%-3d rev=%.3f FFTM=%s ps=%s" % (
        os2.fsType, os2.usWeightClass, f["head"].fontRevision, ff, ps)


def sfd_facts(text):
    head = text.split("\nStartChar:", 1)[0]
    out = []
    for k in ("FontName", "FSType", "TTFWeight", "Version", "ModificationTime"):
        m = re.search(r"^%s: (.*)$" % k, head, re.M)
        out.append("%s=%s" % (k, m.group(1).strip() if m else "(absent)"))
    return " ".join(out)


def main():
    for d, styles in FAMILIES.items():
        pre = PREFIX[d]
        print("=" * 100)
        print(d)
        for s in styles:
            path = "%s/%s-%s.ttf" % (d, pre, s)
            print("-- %s" % path)
            revs = git(GF, "log", "--format=%h %ad %s", "--date=short", "--", path).decode().splitlines()
            for line in reversed(revs):
                h = line.split()[0]
                try:
                    blob = git(GF, "show", "%s:%s" % (h, path))
                except subprocess.CalledProcessError:
                    print("   google/fonts %s  (deleted)" % line)
                    continue
                print("   google/fonts %-60s %s" % (line[:60], facts(blob)))
            for h in (HG_BASE,):
                try:
                    blob = git(HG, "show", "%s:%s" % (h, path))
                    print("   hg %s binary            %s" % (h[:9], facts(blob)))
                except subprocess.CalledProcessError:
                    print("   hg %s binary            (absent)" % h[:9])
            # the .sfd FontForge exported from (Thin names the ExtraLight binaries)
            sname = s.replace("ExtraLight", "Thin") if pre == "TitilliumWeb" else s
            spath = "%s/src/%s-%s-TTF.sfd" % (d, pre, sname)
            try:
                text = git(HG, "show", "%s:%s" % (HG_BASE, spath)).decode("utf-8", "replace")
                print("   hg %s %s  %s" % (HG_BASE[:9], spath.split("/")[-1], sfd_facts(text)))
            except subprocess.CalledProcessError:
                print("   hg %s %s  (absent)" % (HG_BASE[:9], spath))
            opath = "%s/src/%s-%s.otf" % (d, pre, sname)
            try:
                blob = git(HG, "show", "%s:%s" % (HG_BASE, opath))
                print("   hg %s %s  %s" % (HG_BASE[:9], opath.split("/")[-1], facts(blob)))
            except subprocess.CalledProcessError:
                pass


if __name__ == "__main__":
    main()
