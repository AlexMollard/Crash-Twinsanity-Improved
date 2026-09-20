"""Names engine functions from the tables the engine dispatches through.

Scripts pick engine behaviour by number - condition 572, command 619 - and the executable turns those numbers
into objects through two jump tables. The Twinsanity Editor already knows what most of those numbers are called
(`DefaultEnums.cs`, `ConditionID` and `CommandID`), so the names are sitting there waiting to be joined up:

    condition id  ->  jump table 0x2ECF90[id + 1]  ->  builder  ->  a methods vtable
    command id    ->  jump table 0x2EC530[id]      ->  builder  ->  a methods vtable

Each builder is the same shape - allocate, store a pointer to a static methods table, store the id - so the
builder can be named after the id, and so can the methods table it installs. That is the interesting one,
because it holds the functions that actually do the work. Every one of the 172 tables has the same shape, with
code in three slots:

    +0x0C  conditions: reads the condition out of the level data
    +0x14  conditions: the check - what a script evaluates      commands: reads the command out of level data
    +0x1C  conditions: a destructor, the same one in all 118     commands: the action - what the command does

Both slot meanings are checked against things already known independently: the mod re-points condition 572's
check at `0x2F0AB8 + 0x14`, and the function in `Command_BottomTextDisplay_Methods + 0x1C` is the one that
writes a string, a position and a duration into the renderer.

Writes tools/re/db/generated.tsv, which `ghidra.py import` applies alongside the hand-written symbols.tsv.
Regenerating is safe: nothing here is hand-edited, and names already in symbols.tsv win.

  python tools/re/autoname.py [--iso ISO] [--dry]
"""
import argparse, os, re, struct, sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it

ENUMS = os.path.join(ROOT, "tools", "twinsanity-editor", "Twinsanity", "DefaultEnums.cs")
OUT = os.path.join(HERE, "db", "generated.tsv")

# Both bounds are the `sltiu` in the dispatch, so they are the engine's own and not a guess: conditions are
# indexed by id + 1 (BuildScriptCondition at 0x106C40), commands by the id itself (BuildScriptCommand 0x101720).
CONDITION_TABLE, CONDITION_COUNT, CONDITION_BIAS = 0x2ECF90, 0x286, 1
COMMAND_TABLE, COMMAND_COUNT, COMMAND_BIAS = 0x2EC530, 0x297, 0
STATIC_DATA = range(0x2E6F00, 0x30A460)        # .data/.rodata/.sdata: where a methods table can live
TEXT = range(0x100000, 0x2D9D88)

# Slots in a methods table worth naming, and what the function there does. The destructor at a condition's
# +0x1C is the same function in all 118 tables, so there is nothing to name.
SLOTS = {"Condition": {0x0C: "Read", 0x14: "Check"},
         "Command": {0x14: "Read", 0x1C: "Run"}}

_md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)


def read_enum(name):
    """{value: name} for a `enum NAME : ushort` in the editor library."""
    src = open(ENUMS, encoding="utf-8-sig", errors="replace").read()
    m = re.search(r"enum\s+" + name + r"\s*:\s*ushort\s*\{(.*?)\n\s*\}", src, re.S)
    out, nxt = {}, 0
    for line in m.group(1).splitlines():
        line = line.split("//")[0].strip().rstrip(",")
        if not line: continue
        if "=" in line:
            key, value = line.split("=", 1)
            try: nxt = int(value.strip(), 0)
            except ValueError: continue
            out[nxt] = key.strip()
        else:
            out[nxt] = line
        nxt += 1
    return out


class Image:
    def __init__(self, data):
        self.d = data

    def word(self, va):
        return struct.unpack_from("<I", self.d, va - 0x100000 + 0x1000)[0]

    def code(self, va, n=14):
        off = va - 0x100000 + 0x1000
        return list(_md.disasm(self.d[off:off + 4 * n], va))

    def methods_table(self, builder):
        """The static address a builder installs as the object's methods pointer.

        Every builder allocates, then builds one address out of a lui/addiu pair and stores it. Taking the
        first such pair that lands in static data is enough - there is only ever one.

        Most builders finish with `b <shared tail>` and put the `addiu` that completes the address in the
        delay slot, so the scan has to run one instruction past the branch, not stop at it."""
        parts, left = {}, None
        for insn in self.code(builder):
            op = insn.mnemonic
            args = [a.strip() for a in insn.op_str.split(",")]
            if op == "lui" and len(args) == 2:
                parts[args[0]] = int(args[1], 0) << 16
            elif op in ("addiu", "ori") and len(args) == 3 and args[1] in parts:
                value = parts[args[1]] + int(args[2], 0)
                if value in STATIC_DATA: return value
                parts[args[0]] = value
            if left is not None:
                left -= 1
                if left < 0: break
            elif op in ("jr", "b", "j") or (op.startswith("b") and op != "break"):
                left = 1                               # the delay slot still runs
        return None


def collect(img, table, count, bias, ids, kind):
    """[(builder address, methods address or None, id, name)] for every id the editor has a name for."""
    targets = {}
    for slot in range(count):
        targets.setdefault(img.word(table + 4 * slot), []).append(slot - bias)
    out = []
    for builder, owners in targets.items():
        if builder not in TEXT: continue
        if len(owners) != 1: continue              # a shared body is the "not implemented" stub, not one command
        cid = owners[0]
        name = ids.get(cid)
        if not name or not re.fullmatch(r"[A-Za-z_]\w*", name): continue
        if name.lower() in ("none", "unknown", "unused"): continue
        out.append((builder, img.methods_table(builder), cid, name))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso"); ap.add_argument("--dry", action="store_true")
    o = ap.parse_args()

    iso = o.iso or next(p for p in sorted(os.listdir(ROOT))
                        if p.lower().endswith(".iso") and it.iso_crc(os.path.join(ROOT, p)) == it.ORIGINAL_CRC)
    with open(os.path.join(ROOT, iso) if not os.path.isabs(iso) else iso, "rb") as f:
        img = Image(it.read_file(f, it.iso_files(f), it.ELF_PATH))

    rows, seen = [], {}
    for kind, table, count, bias, enum in (
            ("Condition", CONDITION_TABLE, CONDITION_COUNT, CONDITION_BIAS, "ConditionID"),
            ("Command", COMMAND_TABLE, COMMAND_COUNT, COMMAND_BIAS, "CommandID")):
        found = collect(img, table, count, bias, read_enum(enum), kind)
        tables = {}
        for builder, methods, cid, name in found:
            if methods is not None: tables.setdefault(methods, []).append(name)
        slots = SLOTS[kind]
        shared = {}                                    # a slot function reused by several ids names none of them
        for builder, methods, cid, name in found:
            if methods is None or len(tables[methods]) != 1: continue
            for off, _ in slots.items():
                target = img.word(methods + off)
                if target in TEXT: shared.setdefault(target, []).append(name)
        methods_named = 0
        for builder, methods, cid, name in sorted(found, key=lambda r: r[2]):
            rows.append((builder, "F", f"Build{kind}_{name}", f"{kind.lower()} {cid}"))
            if methods is None or len(tables[methods]) != 1: continue
            methods_named += 1
            rows.append((methods, "L", f"{kind}_{name}_Methods", f"{kind.lower()} {cid} methods"))
            for off, role in slots.items():
                target = img.word(methods + off)
                if target in TEXT and len(shared[target]) == 1:
                    rows.append((target, "F", f"{kind}_{name}_{role}",
                                 f"{kind.lower()} {cid} methods +{off:#x}"))
        print(f"{kind}: {len(found)} named builders, {methods_named} distinct methods tables, "
              f"{sum(1 for t, n in shared.items() if len(n) == 1)} unshared slot functions")

    rows.sort()
    for addr, kind, name, note in rows: seen.setdefault(name, []).append(addr)
    clash = {n: a for n, a in seen.items() if len(a) > 1}
    if clash: print(f"  {len(clash)} name(s) used at more than one address, dropped: {list(clash)[:4]}")
    rows = [r for r in rows if len(seen[r[2]]) == 1]

    if o.dry:
        for addr, kind, name, note in rows[:25]: print(f"  {addr:08x} {kind} {name:<44} {note}")
        print(f"  ... {len(rows)} rows")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Generated by tools/re/autoname.py from the engine's dispatch tables and the Twinsanity\n"
                "# Editor's ConditionID / CommandID enums. Do not edit: regenerate instead.\n"
                "# address\tkind\tname\tdetail\n")
        for addr, kind, name, note in rows:
            f.write(f"{addr:08x}\t{kind}\t{name}\t{note}\n")
    print(f"wrote {len(rows)} names to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
