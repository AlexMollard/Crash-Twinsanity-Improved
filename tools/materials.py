"""Material fixes applied to level files (.rm2) by build_mod.py.

Crash's shadow is drawn in a screen-space pass that only darkens pixels whose framebuffer alpha has the top bit set,
which materials request with the GS "alpha correction" flag (FBA). Level scenery has it on; characters have it off
so they don't shadow themselves - and so do most crate materials, which is why Crash's shadow never shows on crates.
crate_shadow_offsets() finds those flags so the build can switch them on (one byte each, sizes unchanged).

Material item (graphics section 11, subsection 1): u64 header, i32 draw layer, i32 name length, name, i32 shader count,
shaders. Shader: u32 type, type-specific params (23: 12 bytes, 26: 20, 16/17: 4), 24 setting bytes
(ABlending first, alpha correction at +24), 6 flag bytes, 2 x u16 LOD, 3 x 16-byte vectors, u32 texture, u32 type."""
import re, struct, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rig"))
import rm2splice

CRATE_NAMES = re.compile(rb"^((AKU)?CRATES?_|life_crate)", re.I)   # life_crate = the extra-life crate
PARAMS = {23: 12, 26: 20, 16: 4, 17: 4}

def materials(buf):
    """Yield (material id, name, [(settings_offset, ablending, fba)]) for every material in an RM2, verifying the layout."""
    try: base, _ = rm2splice.locate(buf, [11, 1])
    except (StopIteration, struct.error): return
    _, _, recs = rm2splice._records(buf, base)
    for off, size, rid in recs:
        p = base + off; end = p + size
        _, _, nlen = struct.unpack_from("<QiI", buf, p); p += 16
        name = bytes(buf[p:p + nlen]); p += nlen
        (count,) = struct.unpack_from("<I", buf, p); p += 4
        shaders = []
        for _ in range(count):
            (kind,) = struct.unpack_from("<I", buf, p); p += 4 + PARAMS.get(kind, 0)
            shaders.append((p, buf[p], buf[p + 24]))
            p += 24 + 6 + 4 + 48 + 8
        if p == end: yield rid, name, shaders

def crate_shadow_offsets(buf):
    """Offsets of the FBA byte of every opaque crate shader that has it off."""
    return [s + 24 for _, name, shaders in materials(buf) if CRATE_NAMES.match(name)
            for s, ablend, fba in shaders if ablend == 0 and fba == 0]

if __name__ == "__main__":
    for path in sys.argv[1:]:
        buf = open(path, "rb").read()
        mats = list(materials(buf))
        crates = [(n, sh) for _, n, sh in mats if CRATE_NAMES.match(n)]
        print(f"{path}: {len(mats)} materials parsed, {len(crates)} crate materials, {len(crate_shadow_offsets(buf))} shaders to fix")
