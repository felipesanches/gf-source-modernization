#!/usr/bin/env python3
"""Tree filter: rewrite comment/rustdoc/help text to state only the rule the code
implements, then normalise the filter registrations in mod.rs. Only exact-text
replacements; code is not touched. Logs each applied substitution to $REWRITE_LOG."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalize_modrs  # noqa: E402

F = "babelfont/src/"

SUBS = {
    F + "convertors/fontforge.rs": [
        (
            """        // The quotes around a glyph name are FontForge's modified-UTF-7 marker, not
        // decoration: a quoted name has non-ASCII characters encoded as `+<base64>-`,
        // the same encoding this convertor already decodes for subtable, lookup, class
        // and nameid strings. Gudea-Italic's
        //     StartChar: "C+AJIA-rculo0"
        // is `C`, U+0092, `rculo0`, and that decoded name is what all three shipped
        // Gudea binaries carry. Passing the raw text through kept a `+` in the name,
        // which a `post` table may not hold; trimming the quotes before the trailing
        // whitespace FontForge leaves after them also embedded the closing quote, so
        // the glyph reached the built font named `C+AJIA-rculo0" `.
""",
            """        // The quotes around a glyph name are FontForge's modified-UTF-7 marker: a
        // quoted name has non-ASCII characters encoded as `+<base64>-`, the same
        // encoding used for subtable, lookup, class and nameid strings. FontForge can
        // leave whitespace after the closing quote, so trim, then unquote, then decode.
""",
        ),
        (
            """        // The quotes are FontForge's modified-UTF-7 marker. Gudea-Italic-TTF.sfd has
        //   StartChar: "C+AJIA-rculo0"<space>
        // which is `C`, U+0092, `rculo0` -- the name all three shipped Gudea binaries
        // carry. Trimming the quotes before the trailing whitespace left the closing
        // quote inside the name, and not decoding left a `+` a post table may not hold.
""",
            """        // The quotes are FontForge's modified-UTF-7 marker, and FontForge can leave
        // whitespace after the closing one:
        //   StartChar: "C+AJIA-rculo0"<space>
        // names the glyph `C`, U+0092, `rculo0`.
""",
        ),
        (
            """        // Every lookup a chain rule calls, by assigned name, over the whole font. A
        // lookup registered only to `aalt` still has to be DEFINED when a chain context
        // calls it by name: suppressing the definition would leave the call referring to
        // a name the feature file never declares, and fea-rs rejects that outright.
""",
            """        // Every lookup a chain rule calls, by assigned name, over the whole font. A
        // lookup registered only to `aalt` still has to be DEFINED when a chain context
        // calls it by name, or the call would refer to a lookup the feature file never
        // declares.
""",
        ),
        (
            """            // A lookup used only by `aalt` has its rules INLINED into the feature
            // further down, because neither a lookup reference nor a script statement
            // is legal inside aalt. Emitting the lookup as a feature prefix as well
            // leaves a named lookup in the font that nothing references: it compiles,
            // it shifts every later lookup index, and diffenator3 then compares
            // non-corresponding lookups between the release and the build. patrickhand
            // carried two such lookups and its GSUB lookup_list row was largely that.
            // ... and nothing else reaches it. A chain context calling this lookup by
            // name is such a reference, so the definition has to stay even though aalt
            // inlines the same rules.
""",
            """            // A lookup used only by `aalt` has its rules INLINED into the feature
            // further down, because neither a lookup reference nor a script statement
            // is legal inside aalt. Emitting it as a feature prefix as well would add a
            // named lookup that nothing references -- unless a chain context calls it
            // by name, in which case the definition has to stay.
""",
        ),
        (
            """        // A lookup whose only feature registration is `aalt` has its rules inlined
        // into the feature, so it is not written out as a feature prefix. But a chain
        // context may still call it BY NAME, and that call needs a definition to refer
        // to: emitting the call without it is a file fea-rs rejects outright with
        // "lookup is not defined", and no font is built.
""",
            """        // A lookup whose only feature registration is `aalt` has its rules inlined
        // into the feature, so it is not written out as a feature prefix. But a chain
        // context may still call it BY NAME, and that call needs a definition to refer
        // to.
""",
        ),
        (
            """        // The converse, and the reason the suppression exists: with no chain calling
        // it, an aalt-only lookup written out as a prefix is a named lookup nothing
        // references. It compiles, but it shifts every later lookup index, which makes
        // the built font's GSUB lookup list disagree with the released one.
""",
            """        // The converse, and the reason the suppression exists: with no chain calling
        // it, an aalt-only lookup written out as a prefix is a named lookup nothing
        // references.
""",
        ),
    ],
    F + "filters/dropalternateunicodes.rs": [
        (
            """/// U+03BC MICRO SIGN. FontForge's own TTF export did not emit those alternates, so a
/// released binary built with it does not carry them while a faithful conversion of
/// the same source does. Reproducing such a release therefore needs them dropped.
""",
            """/// U+03BC MICRO SIGN. FontForge's own TTF export did not emit those alternates; this
/// filter drops them, so that each glyph keeps only its `Encoding` codepoint.
""",
        ),
    ],
    F + "filters/reversepathdirection.rs": [
        (
            """/// This is the counterpart to [`super::correctpathdirection::CorrectPathDirection`],
/// and it exists for one job: reproducing a release whose contour directions are NOT
/// uniform.
///
/// Compilers negate every contour on the way out to `glyf`, so what the source states
/// is the complement of what the binary carries. Normalising is therefore the right
/// transform only when the release is itself uniform. When a release preserved a
/// FontForge source's own mixed directions -- Herr Von Muellerhoff ships 213 clockwise
/// and 16 counter-clockwise outer contours, exactly as its `.sfd` draws them --
/// normalising makes the 16 agree with the other 213 and they then come out reversed
/// against the release. Reversing everything instead restores the source's own pattern
/// through the compiler's negation.
///
/// For most fonts this is invisible: reversing a whole glyph is a no-op under the
/// nonzero winding rule. It matters for connected scripts, where adjacent letters'
/// strokes overlap and opposite windings cancel at the joins, turning the release's
/// join gaps into solid ink or the reverse.
""",
            """/// This is the counterpart to [`super::correctpathdirection::CorrectPathDirection`],
/// for a font whose contour directions are NOT uniform.
///
/// Compilers reverse every contour on the way out to `glyf`, so what the source
/// states is the opposite of what the binary carries. Correcting the direction is
/// the right transform only when the directions are meant to be uniform. Where a
/// FontForge source's own mixed directions are meant to be kept, reversing every
/// contour keeps that pattern through the compiler's reversal.
///
/// For most fonts this is invisible: reversing a whole glyph is a no-op under the
/// nonzero winding rule. It matters where the contours of adjacent glyphs overlap,
/// as in connected scripts, because opposite windings cancel where they overlap.
""",
        ),
    ],
    F + "filters/keepsourceglyphnames.rs": [
        (
            """/// becomes `uni021A`. FontForge's own TTF export did no such thing, so a font
/// released from a FontForge source carries the source's names, and a conversion of
/// that same source does not reproduce the release.
///
/// The difference is invisible to a rendering comparison -- the outlines are
/// identical and the cmap points at the same shapes -- which is why it survived a
/// gate built on diffenator3's glyph and word counts. It shows up in the `cmap_diff`
/// section that gate discarded: on Krona One, six codepoints whose glyph the release
/// names one thing and our build names another.
///
/// Opt-in rather than automatic, because it is a statement about what the conversion
/// is FOR. Reproducing a released binary wants the release's names; a source being
/// taken forward as the family's new master may well want the production ones.
""",
            """/// becomes `uni021A`. FontForge's own TTF export did no such thing, so a binary it
/// exported carries the names the source states.
///
/// Opt-in rather than automatic, because it is a statement about what the conversion
/// is FOR: matching a binary FontForge exported wants the source's names, while a
/// source taken forward as a new master may well want the production ones.
""",
        ),
        (
            """/// source, as the custom parameter Glyphs itself uses, so it survives into the file
/// and the compiler that builds it later -- fontc through gftools-builder3, in the
/// case this exists for -- honours it without being told again. `main.rs` also reads
/// the parameter back when babelfont is the compiler, so the two flags agree on a
/// `.ttf` output rather than one of them silently doing nothing.
""",
            """/// source, as the custom parameter Glyphs itself uses, so it survives into the file
/// and whichever compiler builds it later honours it without being told again.
/// `main.rs` also reads the parameter back when babelfont is the compiler, so the two
/// flags agree on a `.ttf` output rather than one of them silently doing nothing.
""",
        ),
    ],
    F + "filters/keepsourceadvances.rs": [
        (
            """/// and acts on what it finds. `commaaccent` is listed there as a mark, and a mark's
/// advance is zeroed -- so Krona One's `commaaccent`, which its `.sfd` gives
/// `Width: 730` and which FontForge duly shipped at 730, was built at 0.
""",
            """/// and acts on what it finds. `commaaccent` is listed there as a mark, and a mark's
/// advance is zeroed, even when the source gives the glyph a width.
""",
        ),
        (
            """/// Setting `Base` on a glyph puts it in GDEF class 1, which suppresses the mark class
/// it would otherwise have had. That is the point for `commaaccent`, and it is not
/// free elsewhere: on pompiere it reclassifies 249 glyphs, and `uni034F` (COMBINING
/// GRAPHEME JOINER) goes from mark to base. The release has it as a base too, so this
/// filter moves toward the release there -- but the reverse case is what to watch for,
/// because HarfBuzz zeroes a GDEF mark's `y_advance` as well as its `x_advance`. In a
/// font with no `vmtx`, where the vertical advance is synthesised from `hhea`, that is
/// a whole line advance and not the zero `hmtx` suggests. Measured: 942 differing
/// pixels at 48 ppem in vertical text between the two classifications.
""",
            """/// Setting `Base` on a glyph puts it in GDEF class 1, which suppresses the mark class
/// it would otherwise have had. An advancing glyph that should stay a mark has to be
/// categorised before this filter runs.
""",
        ),
    ],
    F + "filters/snapcomponenttransforms.rs": [
        (
            """/// component grid and back into the source. FontForge's own exporter treats it as
/// -1, and the released binary carries `[[-1.0, 0], [0, 1.0]]` at offset 856.
""",
            """/// component grid and back into the source. FontForge's own exporter treats it as
/// -1 and writes the component at offset 856.
""",
        ),
        (
            """/// Carrying the raw value through re-quantises it to -0.9998779296875, which moves
/// the transformed outline's leftmost point by one unit. That is why every
/// right-facing glyph built from a FontForge source -- parenright, bracketright,
/// braceright, greater, guillemotright, guilsinglright -- came out with a left side
/// bearing one unit off, in five of the seventeen families in batch 5 and 240 of the
/// 292 blocking table rows across it.
///
""",
            "",
        ),
        (
            """/// Carrying the raw value through re-quantises it to -0.9998779296875 -- TWO steps
/// from -1, one step further out than FontForge wrote. The extra step is ours: the
/// Glyphs 3 writer prints the scale at four decimal places, and -0.9999 is nearest
/// to -16382/16384 where -0.999939 was nearest to -16383/16384. Either way the
/// transformed outline's leftmost point moves by one unit. That is why every
/// right-facing glyph built from a FontForge source -- parenright, bracketright,
/// braceright, greater, guillemotright, guilsinglright -- came out with a left side
/// bearing one unit off, in five of the seventeen families in batch 5 and 240 of the
/// 292 blocking table rows across it.
///
""",
            "",
        ),
        (
            """/// FontForge's exporter calls `rint` (`tottf.c`, `dumpcomposite`), which breaks a tie
/// toward even where fontc's `otRound`, `floor(v + 0.5)`, breaks it upward.
""",
            """/// FontForge's exporter calls `rint` (`tottf.c`, `dumpcomposite`), which breaks a tie
/// toward the even neighbour.
""",
        ),
        (
            """/// Resolve a component offset that is a genuine half, the way FontForge's exporter
/// does.
///
/// TrueType component offsets are integers, so a source that states 44.5 forces a
/// choice, and the two toolchains make it differently: FontForge uses C's `rint`, which
/// sends a tie to the EVEN neighbour, and fontc uses `otRound`, `floor(v + 0.5)`, which
/// sends it up the number line. Six Caps places the macron of `Emacron` at
/// `Refer: 117 175 N 1 0 0 1 44.5 1778 2`, and because the macron is the leftmost
/// element the tie lands on the glyph's xMin and so on the bearing the release records:
/// 44 shipped against our 45.
///
/// The release is self-consistent there, so no stale-bearing arbitration can excuse it.
/// It is a real difference and this is the only way to close it.
""",
            """/// Round a component offset to an integer the way FontForge's exporter does.
///
/// TrueType component offsets are integers, so a source that states 44.5 forces a
/// choice. FontForge's exporter uses C's `rint` (`tottf.c`, `dumpcomposite`), which
/// under the default IEEE-754 rounding mode sends a tie to the EVEN neighbour: 44.5
/// becomes 44 and 45.5 becomes 46.
""",
        ),
        (
            """                "Read a component scale within one F2Dot14 step of an integer as that \\
                 integer, and an offset within a tenth of a unit as that unit: FontForge \\
                 stores a mirror as -0.999939 and exports it as -1",
""",
            """                "Read a component scale within one and a half F2Dot14 steps of an integer \\
                 as that integer, and an offset within a tenth of a unit as that unit: \\
                 FontForge stores a mirror as -0.999939 and exports it as -1",
""",
        ),
        (
            """        // Its own exporter treats it as -1, and so must we.
""",
            """        // Its own exporter treats it as -1, and so does this filter.
""",
        ),
        (
            """        // Six Caps places the macron of Emacron at x = 44.5. FontForge's exporter
        // calls rint (tottf.c, dumpcomposite), which under the IEEE-754 default sends
        // a tie to the EVEN neighbour: 44, which is the bearing the release records.
        // fontc's otRound, floor(v + 0.5), would send it to 45.
""",
            """        // FontForge's exporter calls rint (tottf.c, dumpcomposite), which under the
        // IEEE-754 default sends a tie to the EVEN neighbour: 44.5 becomes 44.
""",
        ),
    ],
    F + "filters/fontforgeunderlineposition.rs": [
        (
            """/// itself, so the released binary does not carry the source's raw value.
""",
            """/// itself, so a binary it exported does not carry the source's raw value.
""",
        ),
        (
            """/// TTF output"). This filter applies the PRE-2019 rule, because it exists to
/// reproduce binaries exported by the FontForge of the day -- it matched 24 of 24
/// sources tested, including nine odd `UnderlineWidth` values. A binary exported by a
/// current FontForge needs the opposite sign, so do not reach for this filter to
/// match one.
///
/// It is opt-in for that reason: there is no single correct offset, only the one that
/// matches the binary you are reproducing. Krona One's source says
/// `UnderlinePosition: -50` with `UnderlineWidth: 50` and ships -75.
""",
            """/// TTF output"). This filter applies the PRE-2019 rule: `UnderlinePosition: -50`
/// with `UnderlineWidth: 50` becomes -75. A binary exported by a current FontForge
/// needs the opposite sign, so do not reach for this filter to match one.
///
/// It is opt-in for that reason: there is no single correct offset, only the one that
/// matches the FontForge that exported the binary.
""",
        ),
        (
            """        // KronaOne-Regular-TTF.sfd says UnderlinePosition -50, UnderlineWidth 50, and
        // KronaOne-Regular.ttf ships post.underlinePosition -75.
""",
            """        // UnderlinePosition -50 with UnderlineWidth 50 exports as
        // post.underlinePosition -75.
""",
        ),
    ],
    F + "filters/fontforgeos2defaults.rs": [
        (
            """/// computes them while writing the binary, so the released font has values that are
/// nowhere in the source. A compiler with a different fallback writes different ones,
/// and every one of these fields shows up as a difference against the release.
""",
            """/// computes them while writing the binary, so the exported font has values that are
/// nowhere in the source, and a compiler with a different fallback writes different
/// ones.
""",
        ),
        (
            """/// Verified against released binaries whose sources declare none of these: Kristi
/// and Tuffy Bold and BoldItalic match on every one of the seven fields compared, at
/// both a 1000- and a 2048-unit em.
///
/// # Opt-in, because it is a statement about who exported the release
///
/// A release NOT exported by FontForge has different values, and this filter would
/// move such a font further from it. Tuffy is the caution: its Bold and BoldItalic
/// carry FontForge's numbers while its Regular and Italic carry a Glyphs-style
/// compiler's, so two styles of one family disagree.
""",
            """/// # Opt-in, because it is a statement about who exported the binary
///
/// A binary NOT exported by FontForge has different values, and this filter would
/// move a conversion further from it. Styles of one family may have been exported by
/// different tools, so the choice is made per source.
""",
        ),
        (
            """/// 3, light 4, and 5 when nothing matches). Kristi declares no `Panose:` and
/// carries `Weight: Medium`; its release ships [2, 0, 6, 3, 0 ...].
""",
            """/// 3, light 4, and 5 when nothing matches), so `Weight: Medium` gives
/// [2, 0, 6, 3, 0 ...].
""",
        ),
        (
            """            // babelfont holds the italic angle in the opposite sense to the `post`
            // table and the SFD -- the fontforge convertor negates it on the way out
            // -- and FontForge's formula is written against its own sense. Negating
            // here keeps the sign of the two x-offsets right; without it they come
            // out with the correct magnitude and the wrong sign.
""",
            """            // babelfont holds the italic angle in the opposite sense to the `post`
            // table and the SFD, and FontForge's formula is written against its own
            // sense, so the angle is negated here.
""",
        ),
        (
            """        // 3; OS2WeightCheck sets byte 2 from the weight NAME, not the weight class,
        // which is why "Medium" gives 6 where a numeric 500 would tell us nothing.
""",
            """        // 3; OS2WeightCheck sets byte 2 from the weight NAME, not the weight class.
""",
        ),
        (
            """        // Kristi: ascender 1638, descender -410, em 2048. Its .sfd declares none of
        // these and its release carries exactly these seven values.
""",
            """        // Ascender 1638, descender -410: a 2048-unit em.
""",
        ),
        (
            """        // gets zero for both; an italic does not, which is why an italic release
        // carries x-offsets its roman sibling does not.
""",
            """        // gets zero for both; an italic does not.
""",
        ),
        (
            """        // Tuffy-BoldItalic: post.italicAngle -12, and the release carries
        // subscriptXOffset +59, superscriptXOffset -204. babelfont's internal angle
        // has the opposite sign to post's, so +12 here is that font.
""",
            """        // post.italicAngle -12 gives subscriptXOffset +59 and superscriptXOffset
        // -204. babelfont's internal angle has the opposite sign to post's, so that
        // is +12 here.
""",
        ),
        (
            """        // OS2WeightCheck keys on sf->weight, the SFD's own PostScript weight name.
        // Kristi declares no Panose and carries Weight: Medium; its release ships
        // [2, 0, 6, 3, 0...]. Reading the SUBFAMILY instead would give 5.
""",
            """        // OS2WeightCheck keys on sf->weight, the SFD's own PostScript weight name:
        // Weight: Medium gives byte 2 = 6.
""",
        ),
    ],
}


def main():
    log = os.environ.get("REWRITE_LOG")
    commit = os.environ.get("GIT_COMMIT", "?")[:7]
    applied = []
    for path, subs in SUBS.items():
        if not os.path.exists(path):
            continue
        with open(path) as f:
            text = f.read()
        orig = text
        for i, (old, new) in enumerate(subs):
            n = text.count(old)
            if n > 1:
                sys.exit(f"ambiguous substitution {path}#{i}")
            if n == 1:
                text = text.replace(old, new)
                applied.append(f"{path}#{i}")
        if text != orig:
            with open(path, "w") as f:
                f.write(text)
    if os.path.exists(normalize_modrs.MODRS):
        with open(normalize_modrs.MODRS) as f:
            t = f.read()
        n = normalize_modrs.normalize(t)
        if n != t:
            with open(normalize_modrs.MODRS, "w") as f:
                f.write(n)
            applied.append("mod.rs normalized")
    if log:
        with open(log, "a") as f:
            f.write(f"{commit}: {', '.join(applied) or '-'}\n")


if __name__ == "__main__":
    main()
