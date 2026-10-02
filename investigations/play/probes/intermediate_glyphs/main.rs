//! Question: what .glyphs does gftools-builder's InstantiateSource hand to fontc for each
//! instance (load -> SetDefaultLocation(instance.location) -> DropVariations -> save)?
//! Usage: dumpinst <in.glyphs> <outdir>
use babelfont::filters::{DropVariations, FontFilter, SetDefaultLocation};
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let font = babelfont::load(&a[1]).unwrap();
    for inst in font.instances.iter() {
        let n = inst.name.get_default().unwrap().to_string();
        eprintln!("instance {n}: loc {:?} fs {}", inst.location, serde_json::to_string(&inst.format_specific).unwrap());
        let mut f = font.clone();
        SetDefaultLocation::new(inst.location.clone()).apply(&mut f).unwrap();
        DropVariations.apply(&mut f).unwrap();
        f.save(format!("{}/{}.glyphs", a[2], n)).unwrap();
    }
}
