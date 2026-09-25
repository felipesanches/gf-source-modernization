
// Review harness for babelfont-rs PR #95 follow-up 8042926 (appended to
// babelfont/src/convertors/fontforge/tests.rs in scratch copies of b4dc853 and
// 8042926). It dumps what the SFD reader makes of every ordered arrangement of
// up to three Version/sfntRevision header lines, plus a real-SFD corpus, so the
// two commits can be diffed. Run with REVIEW_DUMP=<out> [REVIEW_CORPUS=<list>].
#[test]
fn zz_review_dump() {
    use std::fmt::Write as _;
    use std::hash::{DefaultHasher, Hash, Hasher};
    let Ok(out_path) = std::env::var("REVIEW_DUMP") else {
        return;
    };
    let digest = |s: &str| {
        let mut h = DefaultHasher::new();
        s.hash(&mut h);
        h.finish()
    };
    let pool = [
        "Version: 1.001",
        "Version: 3.2 beta",
        "Version: abc",
        "sfntRevision: 0x00010000",
        "sfntRevision: 0x0001ffff",
        "sfntRevision: 0xffff0000",
        "sfntRevision: zzz",
        "sfntRevision: 0x80000000",
        "sfntRevision: 0x7fffffff",
        "sfntRevision:",
        "sfntRevision: 0X00020083",
    ];
    let n = pool.len();
    let mut headers: Vec<Vec<&str>> = vec![vec![]];
    for a in 0..n {
        headers.push(vec![pool[a]]);
        for b in 0..n {
            if b == a {
                continue;
            }
            headers.push(vec![pool[a], pool[b]]);
            for c in 0..n {
                if c == a || c == b {
                    continue;
                }
                headers.push(vec![pool[a], pool[b], pool[c]]);
            }
        }
    }
    let mut out = String::new();
    writeln!(out, "TREE {}", env!("CARGO_MANIFEST_DIR")).unwrap();
    let mut rt_version_mismatch = 0usize;
    let mut rt_emit_unstable = 0usize;
    for h in &headers {
        let header: String = h.iter().map(|l| format!("{l}\n")).collect();
        let sfd = sfd_with_header(&header);
        writeln!(out, "=== {h:?}").unwrap();
        let font = match load_str(&sfd) {
            Ok(f) => f,
            Err(e) => {
                writeln!(out, "load error: {e}").unwrap();
                continue;
            }
        };
        writeln!(
            out,
            "version={:?} name5={:?} fs={:?}",
            font.version,
            font.names.version.get_default(),
            font.format_specific.get("sfntRevision")
        )
        .unwrap();
        writeln!(out, "json={}", serde_json::to_string(&font).unwrap()).unwrap();
        let emitted = match to_str(&font) {
            Ok(e) => e,
            Err(e) => {
                writeln!(out, "emit error: {e}").unwrap();
                continue;
            }
        };
        writeln!(out, "emitted={emitted:?}").unwrap();
        match load_str(&emitted) {
            Ok(f2) => {
                let stable = to_str(&f2).map(|e2| e2 == emitted).unwrap_or(false);
                if f2.version != font.version {
                    rt_version_mismatch += 1;
                }
                if !stable {
                    rt_emit_unstable += 1;
                }
                writeln!(
                    out,
                    "rt version={:?} same_version={} emit_stable={stable}",
                    f2.version,
                    f2.version == font.version
                )
                .unwrap();
            }
            Err(e) => writeln!(out, "rt load error: {e}").unwrap(),
        }
    }
    writeln!(
        out,
        "SYNTH headers={} rt_version_mismatch={rt_version_mismatch} rt_emit_unstable={rt_emit_unstable}",
        headers.len()
    )
    .unwrap();
    if let Ok(list) = std::env::var("REVIEW_CORPUS") {
        let base = std::env::var("REVIEW_CORPUS_BASE").unwrap_or_default();
        for p in fs::read_to_string(list).unwrap().lines() {
            if p.is_empty() {
                continue;
            }
            let path = PathBuf::from(format!("{base}{p}"));
            match load(path) {
                Err(e) => writeln!(out, "CORPUS {p}: load error: {e}").unwrap(),
                Ok(font) => {
                    let json = serde_json::to_string(&font).unwrap();
                    let emitted = to_str(&font).map(|e| digest(&e)).ok();
                    writeln!(
                        out,
                        "CORPUS {p}: version={:?} fs={:?} json={:016x} sfd={:?}",
                        font.version,
                        font.format_specific.get("sfntRevision"),
                        digest(&json),
                        emitted.map(|d| format!("{d:016x}"))
                    )
                    .unwrap();
                }
            }
        }
    }
    fs::write(out_path, out).unwrap();
}
