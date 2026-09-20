"""Turns a raw address into the function that actually contains it.

The obvious way to do this - take the nearest preceding entry in symbols.tsv - is wrong, and wrong in a way
that is worse than useless. symbols.tsv holds only the functions that have been *named*, about a quarter of
them, so the nearest preceding name can be thousands of bytes back and in an entirely different function.
A return address of 0x113fdc reported as `Command_PlayMovie_Read+0x1594` sent someone reading movie code;
it is really `FUN_00113a18+0x5c4`, in the focus resolver.

A wrong name is worse than a raw address, because a raw address invites a lookup and a wrong name does not.

So this uses db/funcs.tsv, which lists every function start in the executable whether named or not, and
prefers the curated name where there is one. With a complete list the answer is exact and needs no threshold:
the greatest start not exceeding the address is by definition the function containing it.

Regenerate db/funcs.tsv after a Ghidra decompile with `python tools/re/addrname.py --rebuild`.
"""
import bisect
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FUNCS = os.path.join(HERE, "db", "funcs.tsv")


class Names:
    def __init__(self, path=FUNCS):
        self.starts, self.names = [], []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                col = line.rstrip("\n").split("\t")
                if len(col) >= 2:
                    try:
                        self.starts.append(int(col[0], 16))
                    except ValueError:
                        continue
                    self.names.append(col[1])

    def describe(self, addr):
        """`name+0xoffset`, or the bare address if it falls outside every known function."""
        i = bisect.bisect_right(self.starts, addr) - 1
        if i < 0:
            return f"{addr:08x}"
        delta = addr - self.starts[i]
        return f"{self.names[i]}+0x{delta:x}" if delta else self.names[i]


def rebuild(decomp=None, out=FUNCS):
    """Rebuild funcs.tsv from the Ghidra decompile's `//// <addr> <name>` headers."""
    decomp = decomp or os.path.join(os.path.dirname(HERE), "ghidra", "SLES_525.68.c")
    starts = {}
    with open(decomp, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("//// "):
                part = line[5:].split()
                if len(part) >= 2:
                    try:
                        starts[int(part[0], 16)] = part[1]
                    except ValueError:
                        pass
    named = {}
    with open(os.path.join(HERE, "db", "symbols.tsv"), encoding="utf-8") as fh:
        for line in fh:
            col = line.rstrip("\n").split("\t")
            if len(col) >= 3 and col[1] == "F":
                try:
                    named[int(col[0], 16)] = col[2]
                except ValueError:
                    pass
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# Every function start in the executable, named or not - generated from the Ghidra decompile.\n")
        fh.write("# Needed so an address can be attributed to the function that actually contains it: symbols.tsv\n")
        fh.write("# holds only named functions, so the nearest preceding *name* can be thousands of bytes away and\n")
        fh.write("# in a different function entirely.\n")
        for a in sorted(starts):
            fh.write(f"{a:08x}\t{named.get(a, starts[a])}\n")
    return len(starts)


if __name__ == "__main__":
    import sys
    if "--rebuild" in sys.argv:
        print(f"wrote {rebuild()} function starts to {FUNCS}")
    else:
        n = Names()
        for arg in sys.argv[1:]:
            a = int(arg, 16)
            print(f"{a:08x}  {n.describe(a)}")
