"""Finds the engine's C++ vtables and the constructors that install them.

A vtable slot in this executable is eight bytes - a zero word and a function pointer - so a table is a run of
`{0, fn}` pairs. Scanning static data for those runs alone does not work, because vtables sit directly next to
each other and a naive scan swallows a thousand slots in one gulp.

What does work is to come at them from the code. A vtable is only useful when something stores its address
into an object, and on MIPS an address is materialised as a `lui`/`addiu` pair. So: scan every instruction in
.text for a materialised constant that lands on a vtable slot boundary, and each one is a vtable start plus,
for free, the function that installs it - which is the class's constructor. Where that constructor already has
a name, the vtable and every method in it can be named after it.

The same delay-slot trap applies as in autoname.py: builders routinely finish with `b <shared tail>` and put
the `addiu` that completes the address in the slot after the branch, which still runs.

  python tools/re/vtables.py [--dry]
"""
import argparse, os, re, struct, sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it

OUT = os.path.join(HERE, "db", "vtables.tsv")
TEXT = range(0x100000, 0x2D9D88)
STATIC = range(0x2E6F00, 0x30A460)
_md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)


def load_image():
    iso = next(p for p in sorted(os.listdir(ROOT))
               if p.lower().endswith(".iso") and it.iso_crc(os.path.join(ROOT, p)) == it.ORIGINAL_CRC)
    with open(os.path.join(ROOT, iso), "rb") as f:
        return it.read_file(f, it.iso_files(f), it.ELF_PATH)


def load_functions():
    """[(address, name)] sorted, from the whole-program decompile's headers."""
    path = os.path.join(ROOT, "tools", "ghidra", "SLES_525.68.c")
    if not os.path.exists(path): raise SystemExit(f"{path} missing - run ghidra.py decompile")
    out = [(int(m.group(1), 16), m.group(2))
           for m in re.finditer(r"^//// ([0-9a-f]{8}) (\S+)$", open(path, encoding="utf-8", errors="replace").read(), re.M)]
    return sorted(set(out))


class Image:
    def __init__(self, data):
        self.d = data

    def word(self, va):
        return struct.unpack_from("<I", self.d, va - 0x100000 + 0x1000)[0]

    def is_slot(self, va):
        """'fn', 'null', or None if this is not an eight-byte vtable slot."""
        if va + 8 > STATIC.stop: return None
        if self.word(va) != 0: return None
        target = self.word(va + 4)
        if target == 0: return "null"
        return "fn" if target in TEXT else None


def materialised(img, functions):
    """{static address: set of functions that build it} for every lui/addiu pair in .text."""
    owners = {}
    starts = [a for a, _ in functions]
    fn_at = 0
    parts, pending = {}, None
    data = img.d
    for va in range(TEXT.start, TEXT.stop, 4):
        while fn_at + 1 < len(starts) and starts[fn_at + 1] <= va: fn_at += 1
        word = struct.unpack_from("<I", data, va - 0x100000 + 0x1000)[0]
        op = word >> 26
        if op == 0x0F:                                        # lui rt, imm
            parts[(word >> 16) & 0x1F] = (word & 0xFFFF) << 16
        elif op in (0x09, 0x0D):                              # addiu / ori  rt, rs, imm
            rs, rt, imm = (word >> 21) & 0x1F, (word >> 16) & 0x1F, word & 0xFFFF
            if rs in parts:
                if op == 0x09: imm = struct.unpack("<h", struct.pack("<H", imm))[0]
                value = parts[rs] + imm
                parts[rt] = value
                if value in STATIC:
                    owners.setdefault(value, set()).add(functions[fn_at])
            elif rt in parts:
                del parts[rt]
        elif op in (0x02, 0x03) or (0x04 <= op <= 0x07):      # j / jal / branches: the delay slot still runs
            pass
    return owners


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    o = ap.parse_args()

    img = Image(load_image())
    functions = load_functions()
    owners = materialised(img, functions)

    starts = sorted(a for a in owners if img.is_slot(a) == "fn")
    print(f"{len(owners)} static addresses built in code, {len(starts)} of them land on a vtable slot")

    rows, named, total_slots = [], 0, 0
    boundaries = set(starts)
    for base in starts:
        va, slots = base, []
        while img.is_slot(va) and (va == base or va not in boundaries):
            slots.append(img.word(va + 4) if img.is_slot(va) == "fn" else 0)
            va += 8
        if sum(1 for s in slots if s) < 2: continue
        total_slots += sum(1 for s in slots if s)
        ctors = sorted(owners[base], key=lambda f: f[0])
        real = [n for _, n in ctors if not n.startswith("FUN_")]
        rows.append((base, len(slots), slots, ctors, real))
        if real: named += 1

    print(f"{len(rows)} vtables, {total_slots} method slots, {named} installed by an already-named function")
    if o.dry:
        for base, n, slots, ctors, real in rows[:20]:
            who = real[0] if real else f"{len(ctors)} unnamed ctor(s)"
            print(f"   {base:08x}  {n:>3} slots  <- {who}")
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Generated by tools/re/vtables.py - the engine's C++ vtables, found from the code that\n"
                "# installs them. Do not edit: regenerate instead.\n"
                "# vtable\tslots\tinstalled by\tmethod addresses\n")
        for base, n, slots, ctors, real in rows:
            who = ",".join(real) if real else ",".join(f"{a:08x}" for a, _ in ctors)
            f.write(f"{base:08x}\t{n}\t{who}\t" + ",".join(f"{s:08x}" if s else "-" for s in slots) + "\n")
    print(f"wrote {len(rows)} vtables to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
