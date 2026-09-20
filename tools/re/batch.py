"""Pulls batches of still-unnamed functions out of the decompile, with the context needed to name them.

Everything that could be derived from the engine's own tables, from signatures or from instruction shapes has
been derived. What is left has to be read, and reading it goes faster with the two things the decompile does
not put next to the body: who calls this function, and what it calls in turn. A function that is called only
by `Command_SetCamera_Run` and calls only `RotateVecByVec` names itself.

  python tools/re/batch.py --min 9 --max 20 --count 25 [--skip N]

Functions already named in db/*.tsv are excluded, so re-running walks forward through the remainder.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DECOMP = os.path.join(ROOT, "tools", "ghidra", "SLES_525.68.c")


def load():
    text = open(DECOMP, encoding="utf-8", errors="replace").read()
    heads = [(int(m.group(1), 16), m.group(2), m.start()) for m in
             re.finditer(r"^//// ([0-9a-f]{8}) (\S+)$", text, re.M)]
    heads.sort()
    bodies, names = {}, {}
    for i, (addr, name, pos) in enumerate(heads):
        end = heads[i + 1][2] if i + 1 < len(heads) else len(text)
        bodies[addr] = text[pos:end]
        names[addr] = name
    return bodies, names


def declined():
    """Addresses looked at and deliberately not named, so the frontier keeps moving.

    Some functions are perfectly legible and still not nameable - a two-level table lookup through a global
    nobody has identified, a generic `return x == 0`. Recording them keeps them out of the next batch without
    pretending they have been understood."""
    path = os.path.join(HERE, "db", "declined.txt")
    if not os.path.exists(path): return set()
    out = set()
    for line in open(path, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if line:
            try: out.add(int(line, 16))
            except ValueError: pass
    return out


def already_named():
    """Every address that has a name in the database, whatever produced it.

    The decompile is only regenerated occasionally, so it lags behind: without this, a function named an
    hour ago still looks like FUN_ to the caller check and its callees never enter the frontier."""
    out = set()
    db = os.path.join(HERE, "db")
    for f in os.listdir(db):
        if not f.endswith(".tsv"): continue
        for line in open(os.path.join(db, f), encoding="utf-8", errors="replace"):
            if line.startswith("#") or not line.strip(): continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1].strip() == "F":
                try: out.add(int(parts[0], 16))
                except ValueError: pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=9); ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--count", type=int, default=25); ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--named-callers", action="store_true",
                    help="only functions with at least one already-named caller: the context makes them nameable")
    ap.add_argument("--by-callers", action="store_true",
                    help="most-called first: naming these improves the most call sites")
    o = ap.parse_args()

    bodies, names = load()
    known = already_named() | declined()
    for a in known:
        if a in names and names[a].startswith('FUN_'): names[a] = 'NAMED_%08x' % a

    # who calls whom, by scanning every body for references to FUN_/named symbols
    callers = {}
    for addr, body in bodies.items():
        for m in re.finditer(r"\b(FUN_([0-9a-f]{8})|[A-Za-z_]\w{3,})\s*\(", body):
            if m.group(2):
                callers.setdefault(int(m.group(2), 16), set()).add(addr)

    candidates = []
    for addr in sorted(bodies):
        if not names[addr].startswith("FUN_") or addr in known: continue
        lines = [l for l in bodies[addr].splitlines() if l.strip()]
        code = [l for l in lines if not l.startswith("////") and not l.startswith("/*")]
        if not o.min <= len(code) <= o.max: continue
        if o.named_callers and not any(not names[c].startswith('FUN_') for c in callers.get(addr, ())):
            continue
        candidates.append(addr)
    if o.by_callers:
        candidates.sort(key=lambda a: (-len(callers.get(a, ())), a))
    seen = len(candidates)
    picked = candidates[o.skip:o.skip + o.count]

    print(f"# {seen - o.skip} unnamed functions of {o.min}-{o.max} lines remain from here; showing {len(picked)}\n")
    for addr in picked:
        who = sorted(callers.get(addr, ()))
        named_callers = [names[c] for c in who if not names[c].startswith("FUN_")]
        print(f"=== {addr:08x}   callers: {len(who)}"
              + (f"  ({', '.join(named_callers[:4])})" if named_callers else "  (none named)"))
        print(bodies[addr].strip())
        print()


if __name__ == "__main__":
    main()
