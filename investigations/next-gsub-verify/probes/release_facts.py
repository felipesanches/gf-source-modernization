#!/usr/bin/env python3
"""Question: for each style of the gsub unit, what does the SHIPPED binary say about
how it was exported, and does it tie to the paired .sfd?

Prints, per style (pairing read from families-next.tsv, never guessed):
  - the release's table set, OS/2.usMaxContext, whether GSUB/GPOS/GDEF/kern/DSIG exist
  - FFTM: FontForge build stamp, font-created and font-modified (the .sfd's
    CreationTime / ModificationTime as FontForge stored them), head.created/modified
  - the paired .sfd's CreationTime / ModificationTime, and whether they equal FFTM's
  - md5 of the release in google/fonts and of the hg blob beside the .sfd (same bytes?)
  - the .sfd's Lookup: lines count, kerning (KernPairs/kern lookups), anchors,
    and TtTable (cvt/fpgm/prep) presence -- to explain the release's hinting tables.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY release_facts.py Megrim Poly-Italic RibeyeMarrow-Regular Varela-Regular
"""
import datetime
import hashlib
import subprocess
import sys

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/sfd-reland"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
MAC_EPOCH = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)


def row_for(style):
    for line in open(W + "/families-next.tsv"):
        f = line.rstrip("\n").split("\t")
        if f[6] == style:
            return f
    raise SystemExit("no row for " + style)


def fftm(font):
    if "FFTM" not in font:
        return None
    t = font["FFTM"]
    data = t.compile(font) if not hasattr(t, "data") else t.data
    import struct
    ver, stamp, created, modified = struct.unpack(">Lqqq", data[:28])
    conv = lambda v: (MAC_EPOCH + datetime.timedelta(seconds=v)).strftime("%Y-%m-%d %H:%M:%S")
    return ver, conv(stamp), conv(created), conv(modified), created, modified


def main():
    for style in sys.argv[1:]:
        repo, fam, lic, kind, base, commit, _, src, shipped = row_for(style)
        sfd = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show",
                              "%s:%s/%s/%s" % (commit, lic, fam, src)],
                             capture_output=True, check=True).stdout.decode("utf-8", "replace")
        f = TTFont(shipped)
        print("=== %s  source %s:%s/%s/%s  release %s" % (style, commit[:8], lic, fam, src, shipped))
        rel_md5 = hashlib.md5(open(shipped, "rb").read()).hexdigest()
        hgname = shipped.rsplit("/", 1)[1]
        try:
            hg = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show",
                                 "%s:%s/%s/%s" % (commit, lic, fam, hgname)],
                                capture_output=True, check=True).stdout
            hg_md5 = hashlib.md5(hg).hexdigest()
        except subprocess.CalledProcessError:
            hg_md5 = "(absent in hg)"
        print("  release md5 %s ; hg %s/%s md5 %s ; identical=%s"
              % (rel_md5, fam, hgname, hg_md5, rel_md5 == hg_md5))
        print("  tables:", " ".join(sorted(f.keys())))
        print("  OS/2.usMaxContext:", getattr(f["OS/2"], "usMaxContext", None),
              " OS/2.version:", f["OS/2"].version)
        h = f["head"]
        conv = lambda v: (MAC_EPOCH + datetime.timedelta(seconds=v)).strftime("%Y-%m-%d %H:%M:%S")
        print("  head.created %s  head.modified %s" % (conv(h.created), conv(h.modified)))
        ff = fftm(f)
        sfd_ct = sfd_mt = None
        for line in sfd.splitlines():
            if line.startswith("CreationTime:"):
                sfd_ct = int(line.split()[1])
            elif line.startswith("ModificationTime:"):
                sfd_mt = int(line.split()[1])
        unix = lambda v: datetime.datetime.fromtimestamp(v, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if ff:
            ver, stamp, created, modified, c_raw, m_raw = ff
            print("  FFTM v%d build-stamp %s  font-created %s  font-modified %s" % (ver, stamp, created, modified))
            # FFTM stores the .sfd's creation/modification times in Mac epoch
            c_unix = c_raw - 2082844800
            m_unix = m_raw - 2082844800
            print("  .sfd CreationTime %s (%s) ModificationTime %s (%s)" % (
                sfd_ct, unix(sfd_ct) if sfd_ct else "-", sfd_mt, unix(sfd_mt) if sfd_mt else "-"))
            print("  FFTM created == .sfd CreationTime: %s ; FFTM modified == .sfd ModificationTime: %s"
                  % (c_unix == sfd_ct, m_unix == sfd_mt))
        else:
            print("  no FFTM")
        lookups = [l for l in sfd.splitlines() if l.startswith("Lookup:")]
        gsub = [l for l in lookups if int(l.split()[1]) < 256]
        gpos = [l for l in lookups if int(l.split()[1]) >= 256]
        print("  .sfd lookups: %d GSUB, %d GPOS" % (len(gsub), len(gpos)))
        print("  .sfd KernPairs lines: %d ; Kerns2 lines: %d ; KernClass2: %d ; AnchorClass2: %s ; AnchorPoint lines: %d"
              % (sum(l.startswith("KernsSLIF") or l.startswith("Kerns2:") for l in sfd.splitlines()),
                 sum(l.startswith("Kerns2:") for l in sfd.splitlines()),
                 sum(l.startswith("KernClass2:") for l in sfd.splitlines()),
                 any(l.startswith("AnchorClass2:") for l in sfd.splitlines()),
                 sum(l.startswith("AnchorPoint:") for l in sfd.splitlines())))
        print("  .sfd TtTable:", [l.split()[1] for l in sfd.splitlines() if l.startswith("TtTable:")],
              " glyphs with TtInstrs:", sum(l.startswith("TtInstrs:") for l in sfd.splitlines()))
        for tag in ("GSUB", "GPOS"):
            if tag in f:
                t = f[tag].table
                print("  %s: %d scripts, %d features, %d lookups" % (
                    tag, len(t.ScriptList.ScriptRecord) if t.ScriptList else 0,
                    len(t.FeatureList.FeatureRecord) if t.FeatureList else 0,
                    len(t.LookupList.Lookup) if t.LookupList else 0))


if __name__ == "__main__":
    main()
