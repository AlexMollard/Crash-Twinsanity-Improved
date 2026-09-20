"""Names the functions whose whole behaviour is visible in their first few instructions.

Roughly six hundred of the executable's functions are two to eight instructions long, and most of them are one
of four things: a jump to somewhere else, a constant, a field read or a field write. None of that needs
understanding the game - it is structure, and structure can be read off the machine code exactly.

The rule throughout is that a name is only emitted when it says something true and useful:

  * a thunk is named after what it forwards to, and only when that target already has a name, because
    `Thunk_FUN_00123456` tells you nothing you did not have;
  * a constant-returning stub is named for the constant, but only where a single function returns it -
    the engine has dozens of `return 0` stubs and calling them all ReturnZero would be a lie by collision;
  * an accessor is named for the field it touches and the type it touches it on, which needs the parameter
    type to be known - `Get_0x3c` on an unknown struct is not worth the line it costs.

Everything it cannot place confidently is left as FUN_, which is an honest label.

  python tools/re/shapes.py [--dry]
"""
import argparse, collections, os, re, struct, sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it

OUT = os.path.join(HERE, "db", "shapes.tsv")
DECOMP = os.path.join(ROOT, "tools", "ghidra", "SLES_525.68.c")
TEXT = range(0x100000, 0x2D9D88)
_md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)

LOADS = {"lw": "", "lh": "Short", "lhu": "UShort", "lb": "Byte", "lbu": "UByte",
         "lwc1": "Float", "ld": "Long", "lwu": "UWord"}
STORES = {"sw": "", "sh": "Short", "sb": "Byte", "swc1": "Float", "sd": "Long"}


def load_functions():
    """[(address, name, signature)] from the whole-program decompile, in address order."""
    text = open(DECOMP, encoding="utf-8", errors="replace").read()
    heads = [(int(m.group(1), 16), m.group(2), m.start()) for m in
             re.finditer(r"^//// ([0-9a-f]{8}) (\S+)$", text, re.M)]
    heads.sort()
    out = []
    for i, (addr, name, pos) in enumerate(heads):
        end = heads[i + 1][2] if i + 1 < len(heads) else len(text)
        body = text[pos:end]
        m = re.search(r"\n([A-Za-z_][\w \*]*?)\b" + re.escape(name) + r"\(([^)]*)\)\s*\n\{", body)
        out.append((addr, name, (m.group(1).strip(), m.group(2).strip()) if m else ("", "")))
    return out


def first_param_type(signature):
    """The declared type of a function's first parameter, when it is a pointer to a named struct."""
    params = signature[1]
    if not params or params == "void": return None
    m = re.match(r"(?:struct\s+)?(\w+)\s*\*\s*\w+", params.split(",")[0].strip())
    if not m: return None
    t = m.group(1)
    return None if t.startswith(("undefined", "int", "uint", "char", "byte", "void", "long", "ulong",
                                 "short", "ushort", "float")) else t


def field_name(types_h, struct_name, offset, kind):
    """The field at OFFSET of STRUCT_NAME, if the exported header lets us work it out."""
    m = re.search(r"struct " + re.escape(struct_name) + r" \{(.*?)\n\};", types_h, re.S)
    if not m: return None
    at = 0
    sizes = {"byte": 1, "char": 1, "bool": 1, "undefined": 1, "undefined1": 1,
             "short": 2, "ushort": 2, "word": 2, "undefined2": 2,
             "int": 4, "uint": 4, "float": 4, "dword": 4, "undefined4": 4,
             "long": 8, "ulong": 8, "undefined8": 8, "qword": 8}
    for line in m.group(1).splitlines():
        line = line.strip().rstrip(";")
        if not line: continue
        decl = re.match(r"(?:struct\s+|union\s+|enum\s+)?([\w]+)\s+\**(\w+)(?:\[(\d+)\])?$", line)
        if not decl: return None                       # an unparsed line makes every later offset a guess
        typ, nm, count = decl.group(1), decl.group(2), decl.group(3)
        size = 4 if "*" in line else sizes.get(typ, 0)
        if size == 0: return None
        size *= int(count) if count else 1
        if at == offset: return nm
        if at > offset: return None
        at += size
    return None


class Shaper:
    def __init__(self, image):
        self.d = image

    def body(self, addr, end):
        off = addr - 0x100000 + 0x1000
        n = min(end - addr, 64)
        return list(_md.disasm(self.d[off:off + n], addr))

    def classify(self, addr, end, names, types_h, sig):
        ins = self.body(addr, end)
        if not ins: return None
        ops = [(i.mnemonic, [a.strip() for a in i.op_str.split(",")]) for i in ins]
        real = [o for o in ops if o[0] != "nop"]
        if not real: return None

        # a tail jump to somewhere else: this function IS that function
        if real[0][0] in ("j", "b") and len(real) <= 2:
            try: target = int(real[0][1][0], 0)
            except (ValueError, IndexError): return None
            if target in names and not names[target].startswith("FUN_"):
                return ("thunk", f"{names[target]}_thunk", f"tail jump to {target:08x}")
            return None

        # return a constant
        if real[0][0] == "jr" and real[0][1][0] == "$ra":
            if len(real) == 1: return ("stub", None, "returns nothing")
            second = real[1]
            if second[0] in ("addiu", "li", "ori") and second[1][0] == "$v0":
                try: value = int(second[1][-1], 0)
                except ValueError: return None
                return ("const", None, f"returns {value}")
            if second[0] == "move" and second[1] == ["$v0", "$zero"]:
                return ("const", None, "returns 0")
            return None

        # one load or one store, then return
        if len(real) >= 2 and real[-1][0] == "jr" and real[-1][1][0] == "$ra":
            core = real[:-1]
            if len(core) != 1: return None
            mnem, args = core[0]
            table = LOADS if mnem in LOADS else STORES if mnem in STORES else None
            if table is None or len(args) != 2: return None
            m = re.match(r"(-?(?:0x)?[0-9a-fA-F]*)\(\$(\w+)\)$", args[1])
            if not m or m.group(2) not in ("a0", "s0"): return None
            offset = int(m.group(1), 0) if m.group(1) else 0
            if offset < 0: return None
            struct_name = first_param_type(sig)
            if not struct_name: return None
            field = field_name(types_h, struct_name, offset, mnem)
            if not field or field.startswith(("field", "unk", "undefined")): return None
            verb = "Get" if mnem in LOADS else "Set"
            flavour = (LOADS if mnem in LOADS else STORES)[mnem]
            pretty = field[0].upper() + field[1:]
            return ("accessor", f"{struct_name}_{verb}{flavour}{pretty}", f"{mnem} +{offset:#x}")
        return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    o = ap.parse_args()

    iso = next(p for p in sorted(os.listdir(ROOT))
               if p.lower().endswith(".iso") and it.iso_crc(os.path.join(ROOT, p)) == it.ORIGINAL_CRC)
    with open(os.path.join(ROOT, iso), "rb") as f:
        image = it.read_file(f, it.iso_files(f), it.ELF_PATH)
    types_h = open(os.path.join(HERE, "db", "types.h"), encoding="utf-8", errors="replace").read()

    functions = load_functions()
    names = {a: n for a, n, _ in functions}
    shaper = Shaper(image)

    found, kinds = [], collections.Counter()
    for i, (addr, name, sig) in enumerate(functions):
        if not name.startswith("FUN_"): continue
        end = functions[i + 1][0] if i + 1 < len(functions) else addr + 0x40
        got = shaper.classify(addr, end, names, types_h, sig)
        if not got: continue
        kind, new, note = got
        kinds[kind] += 1
        if new: found.append((addr, new, note))

    print("shapes recognised: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()))
    print(f"of those, nameable: {len(found)}")

    # a name used at more than one address is a collision, not a name
    by_name = collections.Counter(n for _, n, _ in found)
    found = [r for r in found if by_name[r[1]] == 1]
    dropped = sum(v for v in by_name.values() if v > 1)
    print(f"after dropping {dropped} colliding name(s): {len(found)}")

    if o.dry:
        for addr, new, note in found[:30]: print(f"   {addr:08x}  {new:<52} {note}")
        return
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Generated by tools/re/shapes.py from the machine code: thunks and field accessors whose\n"
                "# whole behaviour is their first few instructions. Do not edit: regenerate instead.\n"
                "# address\tkind\tname\tdetail\n")
        for addr, new, note in sorted(found):
            f.write(f"{addr:08x}\tF\t{new}\t{note}\n")
    print(f"wrote {len(found)} names to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
