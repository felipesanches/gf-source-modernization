#!/usr/bin/env python3
"""Independent re-implementation (adversarial verification of unit "tuffy") of the
.sfd edits the tuffy investigation proposed. Written from the op descriptions,
NOT from their probes/apply_edits.py, so a shared bug cannot hide.

Question it answers: applied from the UNMODIFIED source to a fresh copy, do the
proposed edits produce the gate rows the investigation reported?

Usage: verify_apply.py <in.sfd> <out.sfd> OP ARGS... [-- OP ARGS...]...
Ops (every op must match exactly once, else exit 1):
  setfield F V            replace the single header line "F: ..." (before BeginChars)
  addfield F V            insert "F: V" after "FontName:" (F must be absent)
  setunicode G U          set the 2nd field of G's "Encoding:" (keep slot and gid)
  setencoding G SLOT U    set 1st and 2nd field of G's "Encoding:" (keep gid)
  setrefer G N DX DY      set translation (tokens 8,9 after "Refer:") of G's N-th Refer
  setwidth G W            set G's "Width:"
  translateglyph G DX DY  add DX,DY to every coordinate of G's SplineSet
  ffnotdef                append the .notdef FontForge's tottf.c dumpmissingglyph
                          writes when a font has none (TEST-ONLY emulation)
"""
import sys


def die(msg):
    sys.stderr.write("FATAL: %s\n" % msg)
    sys.exit(1)


def glyph_range(lines, name):
    hits = [i for i, l in enumerate(lines) if l == "StartChar: %s" % name]
    if len(hits) != 1:
        die("glyph %s found %d times" % (name, len(hits)))
    s = hits[0]
    e = next(i for i in range(s, len(lines)) if lines[i] == "EndChar")
    return s, e


def header_end(lines):
    return next(i for i, l in enumerate(lines) if l.startswith("BeginChars:"))


def fmt(v):
    return ("%d" % v) if float(v).is_integer() else repr(float(v))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    ops, cur = [], []
    for a in args:
        if a == "--":
            if cur:
                ops.append(cur)
            cur = []
        else:
            cur.append(a)
    if cur:
        ops.append(cur)
    raw = open(src, "rb").read().decode("utf-8", "surrogateescape")
    trailing_nl = raw.endswith("\n")
    lines = raw.split("\n")
    if trailing_nl:
        lines = lines[:-1]
    for op in ops:
        k = op[0]
        if k == "setfield":
            f, v = op[1], " ".join(op[2:])
            he = header_end(lines)
            idx = [i for i in range(he) if lines[i].startswith(f + ": ")]
            if len(idx) != 1:
                die("setfield %s: %d header lines" % (f, len(idx)))
            print("setfield %s: [%s] -> [%s]" % (f, lines[idx[0]][len(f) + 2:], v))
            lines[idx[0]] = "%s: %s" % (f, v)
        elif k == "addfield":
            f, v = op[1], " ".join(op[2:])
            he = header_end(lines)
            if any(lines[i].startswith(f + ": ") for i in range(he)):
                die("addfield %s: already present" % f)
            fn = [i for i in range(he) if lines[i].startswith("FontName: ")]
            lines.insert(fn[0] + 1, "%s: %s" % (f, v))
            print("addfield %s: %s" % (f, v))
        elif k in ("setunicode", "setencoding", "setrefer", "setwidth", "translateglyph"):
            s, e = glyph_range(lines, op[1])
            if k in ("setunicode", "setencoding"):
                idx = [i for i in range(s, e) if lines[i].startswith("Encoding: ")]
                if len(idx) != 1:
                    die("%s %s: %d Encoding lines" % (k, op[1], len(idx)))
                t = lines[idx[0]].split()
                old = lines[idx[0]]
                if k == "setunicode":
                    t[2] = op[2]
                else:
                    t[1], t[2] = op[2], op[3]
                lines[idx[0]] = " ".join(t)
                print("%s %s: [%s] -> [%s]" % (k, op[1], old, lines[idx[0]]))
            elif k == "setwidth":
                idx = [i for i in range(s, e) if lines[i].startswith("Width: ")]
                if len(idx) != 1:
                    die("setwidth %s: %d Width lines" % (op[1], len(idx)))
                old = lines[idx[0]]
                lines[idx[0]] = "Width: %s" % op[2]
                print("setwidth %s: [%s] -> [%s]" % (op[1], old, lines[idx[0]]))
            elif k == "setrefer":
                n = int(op[2])
                idx = [i for i in range(s, e) if lines[i].startswith("Refer: ")]
                if n < 1 or n > len(idx):
                    die("setrefer %s: no Refer #%d (has %d)" % (op[1], n, len(idx)))
                t = lines[idx[n - 1]].split(" ")
                old = lines[idx[n - 1]]
                # "Refer:" gid uni N|S xx xy yx yy tx ty flags
                t[8], t[9] = op[3], op[4]
                lines[idx[n - 1]] = " ".join(t)
                print("setrefer %s #%d: [%s] -> [%s]" % (op[1], n, old, lines[idx[n - 1]]))
            else:
                dx, dy = float(op[2]), float(op[3])
                for bad in ("Refer:", "AnchorPoint:", "HStem:", "VStem:", "DStem2:", "TtInstrs:"):
                    if any(lines[i].startswith(bad) for i in range(s, e)):
                        die("translateglyph %s: has %s" % (op[1], bad))
                ss = [i for i in range(s, e) if lines[i] == "SplineSet"]
                es = [i for i in range(s, e) if lines[i] == "EndSplineSet"]
                if len(ss) != 1 or len(es) != 1:
                    die("translateglyph %s: %d/%d SplineSet blocks" % (op[1], len(ss), len(es)))
                moved = 0
                for i in range(ss[0] + 1, es[0]):
                    lead = lines[i][: len(lines[i]) - len(lines[i].lstrip(" "))]
                    t = lines[i].split()
                    j = [x for x in range(len(t)) if t[x] in ("m", "l", "c")]
                    if len(j) != 1:
                        die("translateglyph %s: odd line %r" % (op[1], lines[i]))
                    j = j[0]
                    nums = [float(x) for x in t[:j]]
                    nums = [v + (dx if q % 2 == 0 else dy) for q, v in enumerate(nums)]
                    lines[i] = lead + " ".join(fmt(v) for v in nums + []) + " " + " ".join(t[j:])
                    moved += 1
                print("translateglyph %s by %g,%g: %d point lines" % (op[1], dx, dy, moved))
        elif k == "ffnotdef":
            if any(l == "StartChar: .notdef" for l in lines):
                die("ffnotdef: .notdef exists")
            he = header_end(lines)
            hdr = {}
            for i in range(he):
                if ": " in lines[i]:
                    key, val = lines[i].split(": ", 1)
                    hdr.setdefault(key, val)
            asc, dsc = int(hdr["Ascent"]), int(hdr["Descent"])

            def private(key):
                # "StdVW 5 [70]" -> the string after the length, as PSDictHasEntry returns it
                bp = [i for i in range(he) if lines[i].startswith("BeginPrivate:")]
                if not bp:
                    return None
                for i in range(bp[0] + 1, he):
                    if lines[i] == "EndPrivate":
                        break
                    t = lines[i].split(" ", 2)
                    if t[0] == key:
                        return t[2] if len(t) > 2 else ""
                return None

            def c_strtod(s):
                # C strtod: leading whitespace, then the longest numeric prefix; 0 if none
                s = s.lstrip()
                best = 0.0
                for L in range(len(s), 0, -1):
                    try:
                        best = float(s[:L])
                        break
                    except ValueError:
                        continue
                return best

            stem = 0
            v = private("StdVW")
            if v is not None:
                stem = int(c_strtod(v))
            else:
                h = private("StdHW")
                if h is not None:
                    stem = int(c_strtod(h))
            if stem <= 0:
                stem = (asc + dsc) // 30
            ymax = 2 * (asc + dsc) // 3
            xmax = 5 * stem + (asc + dsc) // 10
            xmax += stem
            if ymax > asc:
                ymax = asc
            adv = xmax + 2 * stem
            pts = [(stem, 0), (stem, ymax), (xmax, ymax), (xmax, 0),
                   (2 * stem, stem), (xmax - stem, stem), (xmax - stem, ymax - stem), (2 * stem, ymax - stem)]
            encs = [l.split() for l in lines if l.startswith("Encoding: ") and len(l.split()) == 4]
            slot = max(int(t[1]) for t in encs) + 1
            gid = max(int(t[3]) for t in encs) + 1
            blk = ["StartChar: .notdef", "Encoding: %d -1 %d" % (slot, gid), "Width: %d" % adv,
                   "Flags: W", "LayerCount: 2", "Fore", "SplineSet"]
            for c in (pts[:4], pts[4:]):
                blk.append("%d %d m 1" % c[0])
                for p in c[1:] + [c[0]]:
                    blk.append(" %d %d l 1" % p)
            blk += ["EndSplineSet", "EndChar", ""]
            ec = [i for i, l in enumerate(lines) if l == "EndChars"]
            if len(ec) != 1:
                die("ffnotdef: %d EndChars" % len(ec))
            lines[ec[0]:ec[0]] = blk
            bc = header_end(lines)
            t = lines[bc].split()
            lines[bc] = "BeginChars: %d %d" % (int(t[1]) + 1, int(t[2]) + 1)
            print("ffnotdef: stem %d ymax %d xmax %d advance %d slot %d gid %d" % (stem, ymax, xmax, adv, slot, gid))
        else:
            die("unknown op %s" % k)
    out = "\n".join(lines) + ("\n" if trailing_nl else "")
    open(dst, "wb").write(out.encode("utf-8", "surrogateescape"))


if __name__ == "__main__":
    main()
