"""Disassemble a range of the PAL executable, for the functions Ghidra could not decompile.

Ghidra times out on some of the larger functions and writes `// decompile failed` into SLES_525.68.c in place
of the body. One of those is `FUN_001f4ec0`, the trigger dispatch - the function that decides what happens
when the player walks into a trigger volume - which is exactly the code needed to explain how a trigger
starts a cutscene director. A missing body there reads like an absence of information, and is not one: the
instructions are right there in the file.

Addresses are EE virtual; the file offset is ADDR - 0x100000 + 0x1000, the same mapping elf_patches.txt uses.

  python tools/re/disasm.py 0x1f4ec0 0x1f5428          # a range
  python tools/re/disasm.py 0x1f4ec0 --len 0x200       # or a length
  python tools/re/disasm.py 0x1f4ec0 0x1f5428 --calls  # only the calls, named
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ELF = os.path.join(ROOT, "work", "re", "SLES_525.68")
BASE, FILE_BASE = 0x100000, 0x1000

sys.path.insert(0, HERE)
import addrname

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=lambda v: int(v, 0))
    ap.add_argument("end", nargs="?", type=lambda v: int(v, 0))
    ap.add_argument("--len", dest="length", type=lambda v: int(v, 0))
    ap.add_argument("--calls", action="store_true", help="only jal/j targets, with their names")
    ap.add_argument("--elf", default=ELF)
    o = ap.parse_args()
    end = o.end or (o.start + (o.length or 0x100))

    import capstone
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
    names = addrname.Names()
    data = open(o.elf, "rb").read()
    off = o.start - BASE + FILE_BASE
    blob = data[off:off + (end - o.start)]

    for ins in md.disasm(blob, o.start):
        target = None
        if ins.mnemonic in ("jal", "j", "bal") and ins.op_str.startswith("0x"):
            target = int(ins.op_str, 16)
        if o.calls:
            if target is not None:
                print(f"{ins.address:08x}  {ins.mnemonic:8s} {names.describe(target)}")
            continue
        note = f"   ; {names.describe(target)}" if target is not None else ""
        print(f"{ins.address:08x}  {ins.bytes.hex()}  {ins.mnemonic:10s} {ins.op_str}{note}")

if __name__ == "__main__":
    main()
