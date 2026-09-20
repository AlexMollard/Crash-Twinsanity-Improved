"""Reads mod/asm/*.s - executable patches written as MIPS assembly instead of hand-assembled hex.

A file is a series of blocks, each opened by a directive:

    .cave  NAME                  code placed in the cave (tools/elfpatch.py), address assigned by the build
    .patch ADDR  ORIG[,ORIG..]   words replaced in place at ADDR; every ORIG is checked against the disc first

Everything else is MIPS for tools/mipsasm.py. Labels defined anywhere in any file are visible everywhere, and
so is every name in tools/re/db/symbols.tsv - so a hook can say

    jal GetButtonPressure

and mean it. A .patch block must assemble to exactly as many words as it lists originals for, which is what
stops a patch from running over the instruction after it.

Caves are laid out in the order the files are read (sorted by name), so adding a block only moves the ones
after it. Nothing in the game refers to cave addresses, so that is free.
"""
import glob, os, re

import mipsasm

_DIRECTIVE = re.compile(r"^\.(cave|patch)\s+(.*)$", re.I)


class Block:
    def __init__(self, kind, name, addr, originals, where):
        self.kind, self.name, self.addr, self.originals, self.where = kind, name, addr, originals, where
        self.lines = []
        self.code = b""

    @property
    def source(self):
        return "\n".join(self.lines)


def parse(paths):
    """[Block] from the given .s files, in file order."""
    blocks = []
    for path in paths:
        block = None
        for n, raw in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
            stripped = raw.split("#", 1)[0].strip()
            where = f"{os.path.basename(path)}:{n}"
            m = _DIRECTIVE.match(stripped)
            if m:
                kind, rest = m.group(1).lower(), m.group(2).split()
                if kind == "cave":
                    if len(rest) != 1: raise SystemExit(f"{where}: .cave takes a name")
                    block = Block("cave", rest[0], None, [], where)
                else:
                    if len(rest) != 2: raise SystemExit(f"{where}: .patch takes an address and the original words")
                    originals = [int(v, 16) for v in rest[1].split(",")]
                    block = Block("patch", None, int(rest[0], 16), originals, where)
                blocks.append(block)
                continue
            if not stripped:
                if block: block.lines.append("")
                continue
            if block is None: raise SystemExit(f"{where}: code before the first .cave or .patch")
            block.lines.append(raw.split("#", 1)[0].rstrip())
    return blocks


def assemble(blocks, cave_base, symbols):
    """Assemble every block. Returns (cave bytes, [(vaddr, [original words], new bytes, note)], labels).

    Two rounds: the cave is laid out first so its labels have addresses, then everything is assembled again
    with the full symbol table, so a cave block may call a label defined in a later one."""
    labels = dict(symbols)
    for _ in range(2):
        addr = cave_base
        found = {}
        for b in blocks:
            if b.kind != "cave": continue
            b.addr = addr
            b.code, got = mipsasm.assemble(b.source, addr, labels, b.where)
            found[b.name] = addr
            found.update(got)
            addr += len(b.code)
        labels = {**symbols, **found}

    cave = bytearray()
    for b in blocks:
        if b.kind != "cave": continue
        cave += b.code

    patches = []
    for b in blocks:
        if b.kind != "patch": continue
        b.code, _ = mipsasm.assemble(b.source, b.addr, labels, b.where)
        if len(b.code) != 4 * len(b.originals):
            raise SystemExit(f"{b.where}: .patch lists {len(b.originals)} original word(s) but assembles to "
                             f"{len(b.code) // 4} - a patch may only replace what it declares")
        patches.append((b.addr, b.originals, bytes(b.code), b.where))
    return bytes(cave), patches, labels


def load(directories, cave_base, symbols):
    paths = sorted(p for d in directories for p in glob.glob(os.path.join(d, "*.s")))
    return (*assemble(parse(paths), cave_base, symbols), paths)
