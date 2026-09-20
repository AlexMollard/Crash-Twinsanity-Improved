"""Builds a game-wide index of object id -> name, across every level file.

Object ids are not per-file indices. An agent running in `altdoc` can carry an id that appears in no object
list in `altdoc`, `altdoc_b`, `altdoc_c` or `Startup/Default.rm2` - and naming it from any single level's
table hands you an unrelated object that happens to share the number.

The absence is also worth nothing on its own. Each level lists only a few dozen objects spread across a range
of roughly 0-1160, so around 96% of the id range is missing from any given file. "Not defined in this level"
is the expected case, not evidence.

So this runs `twinsdump objects` over every extracted .rm2 and collects every (id, name) pair in the game,
which is the only table that can answer "what is object 871" without guessing.

    python tools/re/objindex.py --rebuild          # rescan work/extracted, write db/objects.json
    python tools/re/objindex.py 871 299 567        # look ids up
    python tools/re/objindex.py --name EVILCRASH   # search by name
"""
import collections
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "db", "objects.json")
EXE = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted")


def rebuild():
    files = sorted(glob.glob(os.path.join(EXTRACTED, "**", "*.rm2"), recursive=True))
    if not files:
        raise SystemExit(f"no .rm2 under {EXTRACTED} - extract the ISO first")
    idx, failed = collections.defaultdict(lambda: collections.defaultdict(list)), []
    for n, f in enumerate(files, 1):
        try:
            out = subprocess.run([EXE, f, "objects", "."], capture_output=True, text=True, timeout=180).stdout
        except Exception as e:
            failed.append((f, str(e)))
            continue
        rel = os.path.relpath(f, EXTRACTED).replace(os.sep, "/")
        for m in re.finditer(r"^object (\d+) (.*)$", out, re.M):
            idx[int(m.group(1))][m.group(2).strip()].append(rel)
        if n % 25 == 0:
            print(f"  {n}/{len(files)}", flush=True)
    data = {str(k): dict(v) for k, v in sorted(idx.items())}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=0, sort_keys=True)
    ids = sorted(idx)
    print(f"scanned {len(files)} files, {len(failed)} failed, {len(ids)} distinct ids "
          f"spanning {ids[0]}..{ids[-1]}")
    for f, e in failed[:5]:
        print(f"  FAILED {os.path.basename(f)}: {e[:80]}")
    return data


def load():
    if not os.path.exists(OUT):
        raise SystemExit(f"{OUT} missing - run with --rebuild")
    with open(OUT, encoding="utf-8") as fh:
        return json.load(fh)


def show(idx, want):
    names = idx.get(str(want))
    if not names:
        print(f"id {want}: defined in no level file in the game")
        return
    print(f"id {want}:")
    for name, files in sorted(names.items()):
        where = ", ".join(files[:4]) + (f" ... (+{len(files) - 4})" if len(files) > 4 else "")
        print(f"   {name:<36} {len(files):>3} file(s)  {where}")


def main():
    args = sys.argv[1:]
    if "--rebuild" in args:
        rebuild()
        return
    idx = load()
    if "--name" in args:
        pat = re.compile(args[args.index("--name") + 1], re.I)
        hits = [(int(i), n, f) for i, d in idx.items() for n, f in d.items() if pat.search(n)]
        for i, n, f in sorted(hits):
            print(f"  {i:>5}  {n:<36} {len(f):>3} file(s)  {f[0]}")
        print(f"{len(hits)} match(es)")
        return
    for a in args:
        show(idx, int(a))


if __name__ == "__main__":
    main()
