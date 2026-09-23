#!/usr/bin/env python3
"""Questions answered -- every release/source fact FINDINGS.md cites:

 A. ComicRelief: what toolchain built the release? (tables present, FFTM, name ID 5,
    OS/2 version vs the .sfd's OS2Version, head.created vs the .sfd's CreationTime,
    head.modified as a date, post underline values vs the .sfd's fields)
 B. RussoOne: what does the .sfd state for FSType, and what did each binary in its
    history carry? (hg-era binary at the source's own commit, google/fonts
    90abd17b4 initial, 8ccda7bf7 "Fix fsType for 40 font files", the release);
    and the fsType of every .ttf that 8ccda7bf7 touched, before and after.
 C. Tuffy Regular/Italic: FSType stated by both .sfd variants vs every binary.

Reads only the READ-ONLY archive and the google/fonts checkout (git show).
Usage: gftools/venv/bin/python3 probes/release_facts.py
"""
import collections
import datetime
import io
import subprocess

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
GF = "/home/fsanches/compartilhado/google/fonts"
HG, HGC = ARC + "/googlefonts/googlefontdirectory-hg.git", "52f780bc9d197280a9f430574e179a5f233c56b6"
CR, CRC = ARC + "/loudifier/Comic-Relief.git", "856315f5a45dfdad75090e4454f1ebfd019296b9"
EPOCH = datetime.datetime(1904, 1, 1)


def show(repo, rev, path):
    return subprocess.check_output(["git", "-C", repo, "show", "%s:%s" % (rev, path)])


def sfd_field(blob, name):
    for line in blob.decode("utf-8", "replace").split("\nStartChar:", 1)[0].splitlines():
        if line.startswith(name + ": "):
            return line.split(": ", 1)[1]
    return None


def main():
    print("== A. ComicRelief release toolchain (google/fonts %s)" %
          subprocess.check_output(["git", "-C", GF, "rev-parse", "--short=12", "HEAD"], text=True).strip())
    for s in ("Regular", "Bold"):
        sfd = show(CR, CRC, "sources/ComicRelief-%s.sfd" % s)
        f = TTFont("%s/ofl/comicrelief/ComicRelief-%s.ttf" % (GF, s))
        created = int(sfd_field(sfd, "CreationTime"))
        print("%s: tables %s" % (s, " ".join(sorted(t for t in f.keys() if t != "GlyphOrder"))))
        print("  FFTM %s | DSIG %s | name5 %r" % ("FFTM" in f, "DSIG" in f, f["name"].getDebugName(5)))
        print("  OS/2.version %d (sfd OS2Version %s) | usWeightClass %d (sfd TTFWeight %s)" % (
            f["OS/2"].version, sfd_field(sfd, "OS2Version"), f["OS/2"].usWeightClass, sfd_field(sfd, "TTFWeight")))
        print("  head.created %s == sfd CreationTime? %s | head.modified %s UTC" % (
            f["head"].created, f["head"].created - 2082844800 == created,
            (EPOCH + datetime.timedelta(seconds=f["head"].modified)).isoformat()))
        print("  post.underlinePosition %d thickness %d | sfd UnderlinePosition %s UnderlineWidth %s" % (
            f["post"].underlinePosition, f["post"].underlineThickness,
            sfd_field(sfd, "UnderlinePosition"), sfd_field(sfd, "UnderlineWidth")))

    print("\n== B. RussoOne fsType")
    sfd = show(HG, HGC, "ofl/russoone/src/RussoOne-Regular-TTF.sfd")
    print("sfd (hg %s src/RussoOne-Regular-TTF.sfd) FSType: %s" % (HGC[:12], sfd_field(sfd, "FSType")))
    for label, blob in (
        ("hg-era binary ofl/russoone/RussoOne-Regular.ttf @52f780bc9d19", show(HG, HGC, "ofl/russoone/RussoOne-Regular.ttf")),
        ("google/fonts 90abd17b4 (2015-03-07 initial)", show(GF, "90abd17b4", "ofl/russoone/RussoOne-Regular.ttf")),
        ("google/fonts 8ccda7bf7 (2015-08-05 fsType sweep)", show(GF, "8ccda7bf7", "ofl/russoone/RussoOne-Regular.ttf")),
        ("release (HEAD)", open(GF + "/ofl/russoone/RussoOne-Regular.ttf", "rb").read()),
    ):
        f = TTFont(io.BytesIO(blob))
        print("  %-50s fsType %d  FFTM %s  vendor %r" % (label, f["OS/2"].fsType, "FFTM" in f, f["OS/2"].achVendID))
    files = [p for p in subprocess.check_output(
        ["git", "-C", GF, "show", "--name-only", "--format=", "8ccda7bf7"], text=True).split() if p.endswith(".ttf")]
    before, after = collections.Counter(), collections.Counter()
    for p in files:
        before[TTFont(io.BytesIO(show(GF, "8ccda7bf7^", p)))["OS/2"].fsType] += 1
        after[TTFont(io.BytesIO(show(GF, "8ccda7bf7", p)))["OS/2"].fsType] += 1
    print("  8ccda7bf7 touched %d .ttf: fsType before %s, after %s" % (len(files), dict(before), dict(after)))

    print("\n== C. Tuffy Regular/Italic fsType")
    for s in ("Regular", "Italic"):
        a = sfd_field(show(HG, HGC, "ofl/tuffy/src/Tuffy-%s-TTF.sfd" % s), "FSType")
        b = sfd_field(show(HG, HGC, "ofl/tuffy/src/Tuffy-%s.sfd" % s), "FSType")
        print("%s: sfd -TTF.sfd FSType %s (families.tsv source); plain .sfd FSType %s" % (s, a, b))
        for label, blob in (
            ("hg-era binary @52f780bc9d19", show(HG, HGC, "ofl/tuffy/Tuffy-%s.ttf" % s)),
            ("google/fonts 90abd17b4 (initial)", show(GF, "90abd17b4", "ofl/tuffy/Tuffy-%s.ttf" % s)),
            ("google/fonts ebcdfd2bb (v1.272, 2017-10-24)", show(GF, "ebcdfd2bb", "ofl/tuffy/Tuffy-%s.ttf" % s)),
            ("release (HEAD)", open("%s/ofl/tuffy/Tuffy-%s.ttf" % (GF, s), "rb").read()),
        ):
            f = TTFont(io.BytesIO(blob))
            print("  %-45s fsType %d  FFTM %s  name5 %r" % (label, f["OS/2"].fsType, "FFTM" in f, f["name"].getDebugName(5)))


if __name__ == "__main__":
    main()
