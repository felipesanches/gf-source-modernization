#!/usr/bin/env python3
"""Which rule did FontLab Studio 5 use to write each table value of a shipped font?

Question answered: for every paired style of families-vfb.tsv, read the font-level
entries of the .vfb (vfbLib) and the tables of the shipped font (fontTools), and count,
per candidate rule, the styles whose release value the rule reproduces from the .vfb's
values. A rule that holds for (nearly) every style is what the VFB reader has to do; the
counter-examples are listed so they can be looked at one by one.

Rules tested (release value == f(.vfb)):
  underline    post.underlinePosition == underline_position + underline_thickness // 2
               (FontLab stores the centre line, post wants the top); also == position as is
  x_height     OS/2.sxHeight == PostScript Info x_height; cap_height likewise
  panose       OS/2.panose == entry 1118 (font-level); also == the TrueType block's
  hhea         hhea asc/desc/gap == OS/2 typo asc/desc/gap; also == win asc/-desc + 0;
               also == typo asc/desc + the hhea_line_gap entry
  typo, win    OS/2 typo and win values == the TrueType block's
  weight       OS/2.usWeightClass == block os2_us_weight_class; also == weight_code
  fs_type      OS/2.fsType == block os2_fs_type
  name1        name ID 1 == family_name; also == menu_name
  name2        name ID 2 == style_name; also == weight
  name4        name ID 4 == full_name; also == family_name + " " + style_name
               (without " Regular"); also == family_name + " " + style_name always
  name6        name ID 6 == font_name
  name16/17    name ID 16 == pref_family_name (absent == family); ID 17 == pref_style_name
  revision     head.fontRevision == version_major.version_minor
  os2_version  the release's OS/2 table version (no rule; distribution printed)

Output: a TSV of the raw values per style on stdout (so a counter-example can be read
without re-running), the rule tallies on stderr.

Usage (vfbLib lives in the vfblib-py-venv interpreter; ~5 min for 194 styles):
  /home/fsanches/compartilhado/vfblib-py-venv/bin/python3 -I tools/probes/vfb_rules/vfb_vs_release.py \
      > tools/probes/vfb_rules/vfb-vs-release-2026-10-29.tsv 2> tools/probes/vfb_rules/rules-2026-10-29.txt
"""
import collections
import csv
import os
import re
import sys
import tempfile

from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(W, "tools"))
from pair_vfb import ARC, HG, family_prefix, git  # noqa: E402

SCRATCH = os.environ.get("TMPDIR", "/home/fsanches/compartilhado/tmp")

KEYS = ("full_name", "family_name", "pref_family_name", "menu_name", "weight", "weight_code",
        "underline_position", "underline_thickness", "panose", "tt_version", "style_name",
        "pref_style_name", "version_major", "version_minor", "font_name", "font_style",
        "hhea_line_gap", "hhea_ascender", "hhea_descender", "ttinfo", "PostScript Info",
        "version", "upm", "ascender", "descender", "x_height", "cap_height")


def vfb_values(mirror, commit, path, tmpdir):
    from vfbLib.vfb.vfb import Vfb
    blob = git(mirror, "show", "%s:%s" % (commit, path))
    p = os.path.join(tmpdir, re.sub(r"[^A-Za-z0-9._-]", "_", path))
    with open(p, "wb") as fh:
        fh.write(blob)
    vfb = Vfb(p, timing=False)
    vals, keys = {}, set()
    for e in vfb.entries:
        k = str(e.key)
        if k == "Glyph" or k.startswith("Glyph ") or k in ("mask", "Links", "Background"):
            continue
        keys.add(k)
        if k not in KEYS or k in vals:
            continue
        try:
            e.decompile()
        except Exception:
            continue
        vals[k] = e.data
    return vals, keys


def name(font, nid):
    r = font["name"].getName(nid, 3, 1, 0x409)
    return str(r) if r else None


def release_values(path):
    f = TTFont(path)
    o, p, h, hd = f["OS/2"], f["post"], f["hhea"], f["head"]
    pan = o.panose
    return {
        "name1": name(f, 1), "name2": name(f, 2), "name4": name(f, 4), "name6": name(f, 6),
        "name16": name(f, 16), "name17": name(f, 17),
        "os2_version": o.version, "fsType": o.fsType, "fsSelection": o.fsSelection,
        "usWeightClass": o.usWeightClass, "usWidthClass": o.usWidthClass,
        "sxHeight": getattr(o, "sxHeight", None), "sCapHeight": getattr(o, "sCapHeight", None),
        "panose": [getattr(pan, a) for a in ("bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast",
                                              "bStrokeVariation", "bArmStyle", "bLetterForm", "bMidline", "bXHeight")],
        "typo": (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap),
        "win": (o.usWinAscent, o.usWinDescent),
        "hhea": (h.ascent, h.descent, h.lineGap),
        "underlinePosition": p.underlinePosition, "underlineThickness": p.underlineThickness,
        "fontRevision": round(hd.fontRevision, 3), "upm": hd.unitsPerEm,
    }


def main():
    rows = list(csv.DictReader(open(os.path.join(W, "families-vfb.tsv")), delimiter="\t"))
    if sys.argv[1:]:
        rows = [r for r in rows if r["repo"] in sys.argv[1:]]
    tmpdir = tempfile.mkdtemp(prefix="vfb_rules-", dir=SCRATCH)
    out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    cols = ["repo", "style", "vfb", "rel_name1", "rel_name2", "rel_name4", "rel_name6", "rel_name16", "rel_name17",
            "vfb_family_name", "vfb_style_name", "vfb_full_name", "vfb_font_name", "vfb_pref_family_name",
            "vfb_pref_style_name", "vfb_menu_name", "vfb_weight", "vfb_weight_code", "rel_usWeightClass",
            "tt_weight_class", "rel_fsType", "tt_fs_type", "rel_fsSelection", "tt_fs_selection", "rel_os2_version",
            "rel_underline", "vfb_underline", "rel_sxHeight", "rel_sCapHeight", "ps_x_height", "ps_cap_height",
            "rel_panose", "vfb_panose", "tt_panose", "rel_typo", "tt_typo", "rel_win", "tt_win", "rel_hhea",
            "vfb_hhea_line_gap", "rel_fontRevision", "vfb_version", "rel_upm", "tt_upm", "vfb_tt_version",
            "vfb_hhea_entries", "rel_usWidthClass", "tt_width_class", "vfb_width"]
    out.writerow(cols)
    tally = collections.Counter()
    counter = collections.defaultdict(list)
    seen_keys = set()
    n = 0

    def rule(key, ok, label):
        if ok:
            tally[key] += 1
        else:
            counter[key].append(label)

    for r in rows:
        mirror = os.path.join(ARC, r["base"] + ".git")
        prefix = family_prefix(mirror, r["commit"], r["lic"], r["family"]) if r["base"] == HG else ""
        try:
            v, keys = vfb_values(mirror, r["commit"], prefix + r["source"], tmpdir)
        except Exception as ex:
            print("%s/%s: vfbLib: %s: %s" % (r["repo"], r["style"], type(ex).__name__, ex), file=sys.stderr)
            continue
        seen_keys |= keys
        rel = release_values(r["shipped"])
        tt = v.get("ttinfo") or {}
        ps = v.get("PostScript Info") or {}
        n += 1
        label = "%s/%s" % (r["repo"], r["style"])
        up, ut = v.get("underline_position"), v.get("underline_thickness")
        if up is not None and ut is not None:
            rule("underline: position + thickness // 2", rel["underlinePosition"] == up + ut // 2, label)
            rule("underline: position as is", rel["underlinePosition"] == up, label)
            rule("underline: thickness as is", rel["underlineThickness"] == ut, label)
        if rel["os2_version"] >= 2 and "x_height" in ps:
            rule("x_height: PostScript Info", rel["sxHeight"] == ps["x_height"], label)
            rule("cap_height: PostScript Info", rel["sCapHeight"] == ps["cap_height"], label)
        if "panose" in v:
            rule("panose: entry 1118", rel["panose"] == list(v["panose"]), label)
        if "OpenTypeOS2Panose" in tt:
            rule("panose: TrueType block", rel["panose"] == list(tt["OpenTypeOS2Panose"]), label)
        typo = (tt.get("os2_s_typo_ascender"), tt.get("os2_s_typo_descender"), tt.get("os2_s_typo_line_gap"))
        win = (tt.get("os2_us_win_ascent"), tt.get("os2_us_win_descent"))
        if None not in typo:
            rule("typo: TrueType block", rel["typo"] == typo, label)
            rule("hhea: == release typo", rel["hhea"] == rel["typo"], label)
            rule("hhea: typo asc/desc + hhea_line_gap entry",
                 rel["hhea"] == (typo[0], typo[1], v.get("hhea_line_gap")), label)
        if None not in win:
            rule("win: TrueType block", rel["win"] == win, label)
            rule("hhea: == release win, gap 0", rel["hhea"] == (rel["win"][0], -rel["win"][1], 0), label)
        if "os2_us_weight_class" in tt:
            rule("weight: TrueType block", rel["usWeightClass"] == tt["os2_us_weight_class"], label)
        if "weight_code" in v:
            rule("weight: weight_code", rel["usWeightClass"] == v["weight_code"], label)
        if "os2_fs_type" in tt:
            rule("fs_type: TrueType block", rel["fsType"] == tt["os2_fs_type"], label)
        if "os2_fs_selection" in tt:
            rule("fs_selection: TrueType block", rel["fsSelection"] == tt["os2_fs_selection"], label)
            rule("fs_selection: TrueType block | REGULAR(64) when bits 0/5 clear",
                 rel["fsSelection"] == (tt["os2_fs_selection"] | (64 if not tt["os2_fs_selection"] & 0x21 else 0)),
                 label)
        fam, sty = v.get("family_name"), v.get("style_name")
        if fam is not None:
            rule("name1: family_name", rel["name1"] == fam, label)
        if "menu_name" in v:
            rule("name1: menu_name", rel["name1"] == v["menu_name"], label)
        if sty is not None:
            rule("name2: style_name", rel["name2"] == sty, label)
        if "weight" in v:
            rule("name2: weight", rel["name2"] == v["weight"], label)
        if "full_name" in v:
            rule("name4: full_name", rel["name4"] == v["full_name"], label)
        if fam is not None and sty is not None:
            rule("name4: family_name + ' ' + style_name", rel["name4"] == "%s %s" % (fam, sty), label)
            rule("name4: family_name + ' ' + style_name, Regular dropped",
                 rel["name4"] == (fam if sty == "Regular" else "%s %s" % (fam, sty)), label)
        if "font_name" in v:
            rule("name6: font_name", rel["name6"] == v["font_name"], label)
        if "pref_family_name" in v:
            rule("name16: pref_family_name (absent == name1)", (rel["name16"] or rel["name1"]) == v["pref_family_name"], label)
        if "pref_style_name" in v:
            rule("name17: pref_style_name (absent == name2)", (rel["name17"] or rel["name2"]) == v["pref_style_name"], label)
        if "version_major" in v and "version_minor" in v:
            rule("revision: version_major.version_minor",
                 rel["fontRevision"] == round(v["version_major"] + v["version_minor"] / 1000.0, 3), label)
        m = re.search(r"(\d+\.\d+)", str(v.get("tt_version", "")))
        if m:
            rule("revision: the number in tt_version", rel["fontRevision"] == round(float(m.group(1)), 3), label)
        hh = (v.get("hhea_ascender"), v.get("hhea_descender"), v.get("hhea_line_gap"))
        if None not in hh:
            rule("hhea: the hhea_ascender/descender/line_gap entries", rel["hhea"] == hh, label)
            rule("hhea: the hhea entries, descender negated", rel["hhea"] == (hh[0], -hh[1], hh[2]), label)
        if "os2_us_width_class" in tt:
            rule("width: TrueType block", rel["usWidthClass"] == tt["os2_us_width_class"], label)
        if "width" in v:
            rule("width: width entry", str(rel["usWidthClass"]) == str(v["width"]), label)
        tally["os2 version %d" % rel["os2_version"]] += 1
        out.writerow([r["repo"], r["style"], r["source"], rel["name1"], rel["name2"], rel["name4"], rel["name6"],
                      rel["name16"], rel["name17"], fam, sty, v.get("full_name"), v.get("font_name"),
                      v.get("pref_family_name"), v.get("pref_style_name"), v.get("menu_name"), v.get("weight"),
                      v.get("weight_code"), rel["usWeightClass"], tt.get("os2_us_weight_class"), rel["fsType"],
                      tt.get("os2_fs_type"), rel["fsSelection"], tt.get("os2_fs_selection"), rel["os2_version"],
                      "%s/%s" % (rel["underlinePosition"], rel["underlineThickness"]), "%s/%s" % (up, ut),
                      rel["sxHeight"], rel["sCapHeight"], ps.get("x_height"), ps.get("cap_height"),
                      ",".join(map(str, rel["panose"])), ",".join(map(str, v.get("panose", []))),
                      ",".join(map(str, tt.get("OpenTypeOS2Panose", []))), "/".join(map(str, rel["typo"])),
                      "/".join(map(str, typo)), "/".join(map(str, rel["win"])), "/".join(map(str, win)),
                      "/".join(map(str, rel["hhea"])), v.get("hhea_line_gap"), rel["fontRevision"],
                      "%s.%s" % (v.get("version_major"), v.get("version_minor")), rel["upm"],
                      tt.get("head_units_per_em"), v.get("tt_version"),
                      "/".join(str(v.get(k)) for k in ("hhea_ascender", "hhea_descender", "hhea_line_gap")),
                      rel["usWidthClass"], tt.get("os2_us_width_class"), v.get("width")])
        sys.stdout.flush()
    print("%d styles read" % n, file=sys.stderr)
    print("\nrule: styles it reproduces / styles it was tested on; then the counter-examples", file=sys.stderr)
    for k in sorted(set(tally) | set(counter)):
        if k.startswith("os2 version"):
            continue
        ok, bad = tally[k], counter.get(k, [])
        print("  %-62s %3d / %3d   %s" % (k, ok, ok + len(bad), " ".join(bad[:8]) + (" ..." if len(bad) > 8 else "")),
              file=sys.stderr)
    print("\nrelease OS/2 table versions: " + ", ".join("%s: %d" % (k, c) for k, c in sorted(tally.items())
                                                        if k.startswith("os2 version")), file=sys.stderr)
    print("\nfont-level entry keys seen: " + ", ".join(sorted(seen_keys)), file=sys.stderr)


if __name__ == "__main__":
    main()
