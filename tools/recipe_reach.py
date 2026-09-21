"""Does every recipe cover every level file its scripts live in?

Script ids are game-wide, and the same script sits in as many `.rm2` files as need it - but a recipe only
edits the files its `file` lines name. Miss one and the fix silently does not apply there. That is not
hypothetical: `rooftop.ops` named `roof01` and the Rooftop director is also in `roofcor2`, so anyone playing
the Nina route through that level got no skip and no prompt at all.

This reads every recipe, collects the script ids it edits, and asks which levels hold each of those scripts.
Anything a recipe edits that also lives somewhere it does not patch is reported.

A clean run is only meaningful if the check can see multi-file scripts at all, so it asserts that at least
one edited script really does live in more than one level - otherwise "no gaps" would just mean the lookup
found nothing and the report would be vacuously reassuring.

  python tools/recipe_reach.py                 # mod/levels
  python tools/recipe_reach.py mod/levels-wip  # or another recipe directory
"""
import glob, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it
from psm_extract import source_iso, archive_names

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
OPS = {"addbody", "copybody", "clearbodies", "appendcmds", "delcmd", "movebody", "settarget",
       "setcond", "setarg", "runscript", "skipprompt"}

def read_recipes(folder):
    """recipe name -> (levels it patches, script ids it edits)"""
    out = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.ops"))):
        files, ids = set(), set()
        for line in open(path, encoding="utf-8"):
            s = line.split("#", 1)[0].split()
            if not s:
                continue
            if s[0] == "file":
                files.add(os.path.basename(s[1]).rsplit(".", 1)[0].lower())
            elif s[0] in OPS and len(s) > 1 and s[1].isdigit():
                ids.add(int(s[1]))
        if ids:
            out[os.path.basename(path)] = (files, ids)
    return out

def holders(script_ids):
    """script id -> set of levels whose .rm2 contains it"""
    found = {i: set() for i in script_ids}
    iso = source_iso()
    names = [n for n in archive_names(iso) if n.lower().endswith(".rm2")]
    with open(iso, "rb") as f, tempfile.TemporaryDirectory() as work:
        table = it.iso_files(f)
        for n in sorted(names):
            level = os.path.basename(n).rsplit(".", 1)[0].lower()
            p = os.path.join(work, os.path.basename(n))
            open(p, "wb").write(it.archive_file(f, table, n))
            out = subprocess.run([TWINSDUMP, p, "scripts", "."], capture_output=True, text=True).stdout
            here = {int(m) for m in re.findall(r"^=== script (\d+) ", out, re.M)}
            for i in script_ids & here:
                found[i].add(level)
            os.remove(p)
    return found

def main():
    folder = os.path.join(ROOT, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "mod", "levels")
    recipes = read_recipes(folder)
    wanted = set().union(*(ids for _, ids in recipes.values())) if recipes else set()
    if not wanted:
        raise SystemExit(f"no recipes with script edits in {folder}")
    print(f"{len(recipes)} recipes edit {len(wanted)} distinct scripts", flush=True)

    where = holders(wanted)
    spread = max((len(v) for v in where.values()), default=0)
    print(f"validation: the most widely shared edited script is in {spread} level file(s) - "
          + ("the check can see multi-file scripts\n" if spread > 1 else
             "NOTHING is shared, so a clean result below would prove nothing; the lookup is broken\n"))
    if spread <= 1:
        return

    gaps = 0
    for name, (files, ids) in sorted(recipes.items()):
        extra = {i: sorted(where[i] - files) for i in sorted(ids) if where[i] - files}
        if not extra:
            continue
        gaps += 1
        print(f"{name}: patches {', '.join(sorted(files))}")
        for i, levels in extra.items():
            print(f"    script {i} also lives in: {', '.join(levels)}")
    if not gaps:
        print("no gaps: every script a recipe edits lives only in the levels that recipe patches")

if __name__ == "__main__":
    main()
