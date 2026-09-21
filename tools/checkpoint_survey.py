"""Which substantial levels have no checkpoint at all, and could one be added?

Adding a checkpoint means adding an Instance, which tools/rig/rm2splice.py can now do. But an instance only
names an object by ID, so the level has to *define* that object already; where it does not, the object, its
scripts, its animations and its OGIs would all have to come too, which is a different and much larger job.
So the question splits in two and this answers both.

Two things it gets right that a first pass did not. There is more than one kind of checkpoint:
act_CHECKPOINTCRATE is the visible crate, and act_INVISIBLE_CHECKPOINT_CRATE* is a trigger volume that saves
your progress without anything on screen - bossarea has no crate but does have those, so calling it
"no checkpoint" was wrong. And a level that defines the object but places none is the interesting case, so
definition and placement are reported separately rather than collapsed.

  python tools/checkpoint_survey.py [MIN_INSTANCES]
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted")
CHECKPOINT = re.compile(r"CHECKPOINT", re.I)
SUBSTANTIAL = 40          # instances; below this a file is a cutscene stage or a fragment, not a level to die in


def dump(path, *op):
    return subprocess.run([TWINSDUMP, path, *op], capture_output=True, text=True).stdout


def scan(path):
    """(defined object names, placed object names) for anything checkpoint-ish, plus the instance count."""
    defined = set(re.findall(r"^object \d+ .*?\|?([A-Za-z0-9_]*CHECKPOINT[A-Za-z0-9_]*)\s*$",
                             dump(path, "objects", "CHECKPOINT"), re.M | re.I))
    insts = dump(path, "instances").splitlines()
    placed = set()
    for l in insts:
        m = CHECKPOINT.search(l)
        if m: placed.add(l.rsplit("|", 1)[-1].strip())
    return defined, placed, len(insts)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else SUBSTANTIAL
    paths = []
    for dirpath, _, names in os.walk(EXTRACTED):
        paths += [os.path.join(dirpath, n) for n in names if n.lower().endswith(".rm2")]
    rows = [(os.path.basename(p).rsplit(".", 1)[0], *scan(p)) for p in sorted(paths)]

    have = [r for r in rows if r[2]]
    print(f"{len(rows)} level files; {len(have)} place a checkpoint of some kind")
    if not have:
        return print("validation: NOTHING matched anywhere - the pattern or the parse is wrong, ignore this")
    kinds = sorted({k for _, _, placed, _ in rows for k in placed})
    print(f"validation: the kinds actually placed are {', '.join(kinds)}")
    # "0 levels define one but place none" is the interesting answer below, and a broken definition regex
    # would print exactly the same thing, so show that the definition side finds anything at all.
    defines = [r for r in rows if r[1]]
    print(f"validation: {len(defines)} files define a checkpoint object "
          + (f"(e.g. {defines[0][0]}: {', '.join(sorted(defines[0][1]))})\n" if defines else
             "- NOTHING does, so the split below proves nothing\n"))
    if not defines:
        return

    big = [r for r in rows if r[3] >= limit]
    missing = [r for r in big if not r[2]]
    print(f"{len(big)} files have {limit}+ instances; {len(missing)} of those place no checkpoint at all\n")

    ready = [r for r in missing if r[1]]
    needs_object = [r for r in missing if not r[1]]
    print(f"-- {len(ready)} already define one, so an added instance would be enough")
    for name, defined, _, n in ready:
        print(f"   {name:14} {n:4d} instances   defines {', '.join(sorted(defined))}")
    print(f"\n-- {len(needs_object)} define none: object, scripts, anims and OGIs would have to be added too")
    for name, _, _, n in needs_object:
        print(f"   {name:14} {n:4d} instances")


if __name__ == "__main__":
    main()
