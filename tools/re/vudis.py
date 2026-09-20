"""Disassembles the R5900's COP2 (VU0 macro-mode) instructions, which Capstone and Ghidra both give up on.

Ghidra renders macro-mode code as `_vsub(auVar7, auVar8)` with invented locals, which is readable but loses
the thing that matters: **which VU register** each value lives in. That is fatal for two reasons. Some routines
leave results in VU registers across a call boundary - SegmentTriangleDistances parks six edge tests in
vf17, vf18, vf22, vf23, vf27 and vf28 and ReadEdgeTestsFromVu0 collects them - so the data flow is invisible
unless you can see the register numbers. And a faithful rewrite has to reproduce the operation order, because
VU0 arithmetic is not IEEE-754.

  python tools/re/vudis.py 0x293340 [instructions]

Only the encodings this executable actually uses are decoded; anything else prints as a raw word rather than
a guess.
"""
import argparse, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it

BC = "xyzw"
DEST = "xyzw"


def dest_mask(word):
    """The xyzw field: which components the instruction writes."""
    m = (word >> 21) & 0xF
    s = "".join(DEST[i] for i in range(4) if m & (8 >> i))
    return s or "-"


SPECIAL1 = {}
for i, name in enumerate(("vaddbc", "vsubbc", "vmaddbc", "vmsubbc", "vmaxbc", "vminibc", "vmulbc")):
    for b in range(4):
        SPECIAL1[i * 4 + b] = (name.replace("bc", "") + BC[b], "fd,fs,ft" + BC[b])
SPECIAL1.update({
    0x1C: ("vmulq", "fd,fs,Q"), 0x1D: ("vmaxi", "fd,fs,I"), 0x1E: ("vmuli", "fd,fs,I"),
    0x1F: ("vminii", "fd,fs,I"),
    0x20: ("vaddq", "fd,fs,Q"), 0x21: ("vmaddq", "fd,fs,Q"), 0x22: ("vaddi", "fd,fs,I"),
    0x23: ("vmaddi", "fd,fs,I"),
    0x24: ("vsubq", "fd,fs,Q"), 0x25: ("vmsubq", "fd,fs,Q"), 0x26: ("vsubi", "fd,fs,I"),
    0x27: ("vmsubi", "fd,fs,I"),
    0x28: ("vadd", "fd,fs,ft"), 0x29: ("vmadd", "fd,fs,ft"), 0x2A: ("vmul", "fd,fs,ft"),
    0x2B: ("vmax", "fd,fs,ft"),
    0x2C: ("vsub", "fd,fs,ft"), 0x2D: ("vmsub", "fd,fs,ft"), 0x2E: ("vopmsub", "fd,fs,ft"),
    0x2F: ("vmini", "fd,fs,ft"),
    0x30: ("viadd", "id,is,it"), 0x31: ("visub", "id,is,it"), 0x32: ("viaddi", "it,is,imm5"),
    0x34: ("viand", "id,is,it"), 0x35: ("vior", "id,is,it"),
    0x38: ("vcallms", "imm15"), 0x39: ("vcallmsr", "CMSAR0"),
})

SPECIAL2 = {}
for i, name in enumerate(("vaddabc", "vsubabc", "vmaddabc", "vmsubabc")):
    for b in range(4):
        SPECIAL2[i * 4 + b] = (name.replace("bc", "") + BC[b], "ACC,fs,ft" + BC[b])
for b in range(4):
    SPECIAL2[0x10 + b] = (f"vitof{(0,4,12,15)[b]}", "ft,fs")
    SPECIAL2[0x14 + b] = (f"vftoi{(0,4,12,15)[b]}", "ft,fs")
    SPECIAL2[0x18 + b] = ("vmula" + BC[b], "ACC,fs,ft" + BC[b])
SPECIAL2.update({
    0x1C: ("vmulaq", "ACC,fs,Q"), 0x1D: ("vabs", "ft,fs"), 0x1E: ("vmulai", "ACC,fs,I"),
    0x1F: ("vclip", "fs,ftw"),
    0x20: ("vaddaq", "ACC,fs,Q"), 0x21: ("vmaddaq", "ACC,fs,Q"), 0x22: ("vaddai", "ACC,fs,I"),
    0x23: ("vmaddai", "ACC,fs,I"),
    0x24: ("vsubaq", "ACC,fs,Q"), 0x25: ("vmsubaq", "ACC,fs,Q"), 0x26: ("vsubai", "ACC,fs,I"),
    0x27: ("vmsubai", "ACC,fs,I"),
    0x28: ("vadda", "ACC,fs,ft"), 0x29: ("vmadda", "ACC,fs,ft"), 0x2A: ("vmula", "ACC,fs,ft"),
    0x2C: ("vsuba", "ACC,fs,ft"), 0x2D: ("vmsuba", "ACC,fs,ft"),
    0x8B: ("vopmula", "ACC,fs,ft"),        # index calibrated against this executable, not the manual
    0xAF: ("vnop", ""),
    0x30: ("vmove", "ft,fs"), 0x31: ("vmr32", "ft,fs"), 0x34: ("vlqi", "ft,(is++)"),
    0x35: ("vsqi", "fs,(it++)"), 0x36: ("vlqd", "ft,(--is)"), 0x37: ("vsqd", "fs,(--it)"),
    0x38: ("vdiv", "Q,fsF,ftF"), 0x39: ("vsqrt", "Q,ftF"), 0x3A: ("vrsqrt", "Q,fsF,ftF"),
    0x3B: ("vwaitq", ""),
    0x3C: ("vmtir", "it,fsF"), 0x3D: ("vmfir", "ft,is"), 0x3E: ("vilwr", "it,(is)"),
    0x3F: ("viswr", "it,(is)"),
    0x40: ("vrnext", "ft,R"), 0x41: ("vrget", "ft,R"), 0x42: ("vrinit", "R,fsF"),
    0x43: ("vrxor", "R,fsF"),
})


GPR = ["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
       "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]


def decode(word):
    """(mnemonic, operands) for one COP2 instruction, or None if this is not one we know."""
    op = word >> 26
    if op in (0x36, 0x3E):                                     # lqc2 / sqc2 - Capstone decodes neither
        base, ft = (word >> 21) & 0x1F, (word >> 16) & 0x1F
        imm = struct.unpack("<h", struct.pack("<H", word & 0xFFFF))[0]
        name = "lqc2" if op == 0x36 else "sqc2"
        return (name, f"vf{ft}, {imm:#x}(${GPR[base]})")
    if op != 0x12: return None
    ft, fs, fd = (word >> 16) & 0x1F, (word >> 11) & 0x1F, (word >> 6) & 0x1F
    rs = (word >> 21) & 0x1F
    if not (word >> 25) & 1:                                   # the non-CO forms
        return {1: ("qmfc2", f"rt{ft}, vf{fs}"), 2: ("cfc2", f"rt{ft}, vi{fs}"),
                5: ("qmtc2", f"vf{fs}, rt{ft}"), 6: ("ctc2", f"vi{fs}, rt{ft}")}.get(rs)
    funct = word & 0x3F
    if funct < 0x3C:
        entry = SPECIAL1.get(funct)
        if not entry: return None
        name, form = entry
        d = dest_mask(word)
        if form.startswith("fd"):
            bc = form[-1] if form.endswith(tuple(BC)) and "ft" in form else ""
            return (f"{name}.{d}", f"vf{fd}, vf{fs}, vf{ft}{bc}" if "ft" in form else f"vf{fd}, vf{fs}, {form.split(',')[-1]}")
        return (name, form)
    op2 = ((funct & 3) << 6) | ((word >> 6) & 0x3F)   # calibrated below against known ops
    entry = SPECIAL2.get(op2)
    if not entry: return None
    name, form = entry
    d = dest_mask(word)
    if form.startswith("ACC"):
        bc = form[-1] if form.endswith(tuple(BC)) else ""
        return (f"{name}.{d}", f"ACC, vf{fs}, vf{ft}{bc}" if "ft" in form else f"ACC, vf{fs}, {form.split(',')[-1]}")
    if name == "vnop": return ("vnop", "")
    if form.startswith("ft,fs"): return (f"{name}.{d}", f"vf{ft}, vf{fs}")
    return (f"{name}.{d}", form.replace("fs", f"vf{fs}").replace("ft", f"vf{ft}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("address"); ap.add_argument("count", nargs="?", type=int, default=64)
    ap.add_argument("--iso")
    o = ap.parse_args()

    iso = o.iso or next(os.path.join(ROOT, p) for p in sorted(os.listdir(ROOT))
                        if p.lower().endswith(".iso") and it.iso_crc(os.path.join(ROOT, p)) == it.ORIGINAL_CRC)
    with open(iso, "rb") as f:
        elf = it.read_file(f, it.iso_files(f), it.ELF_PATH)

    import capstone
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
    va = int(o.address, 0)
    off = va - 0x100000 + 0x1000
    for i in range(o.count):
        word = struct.unpack_from("<I", elf, off + i * 4)[0]
        got = decode(word)
        if got:
            print(f"{va + i*4:08x}  {word:08x}  {got[0]:<14}{got[1]}")
        else:
            ins = list(md.disasm(elf[off + i*4: off + i*4 + 4], va + i * 4))
            text = f"{ins[0].mnemonic:<14}{ins[0].op_str}" if ins else f"{'.word':<14}{word:#010x}"
            print(f"{va + i*4:08x}  {word:08x}  {text}")


if __name__ == "__main__":
    main()
