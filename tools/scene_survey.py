"""Which cutscene directors does something actually start?

An earlier survey answered this with `twinsdump refs <id>` and reported ten directors as having nothing pointing at
them. That method is wrong: `refs` returns nothing for the Henchmania director in gpa11 and nothing for Evil Crash
in altdoc, both of which demonstrably exist and run. An empty result there means nothing at all.

The signal that does work is the **trigger list**. `twinsdump <level> triggers` prints each trigger's target by
name, and the trigger targeting `act_HENCHMANIA_CUTSCENE_DIRECTOR` sits at exactly the coordinates that start that
scene on the rig - so this tool is validated against a scene watched playing, which is the check the old method
never had.

One thing the trigger list alone cannot see: **scene chaining**. gpa11 holds a HUB2_TO_HUB3 director that no
trigger targets, and its scene plays anyway, 2.5 s after the Henchmania scene ends. So a director without a trigger
is "started some other way, or not at all" - a question, not a finding. This tool says which of the two groups each
director falls in and refuses to call anything unused.

  python tools/scene_survey.py                 # every level in the archive
  python tools/scene_survey.py gpa11 altdoc    # just these
"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it
from psm_extract import source_iso, archive_names

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
DIRECTOR = re.compile(r"^object\s+(\d+)\s+(.*?CUTSCENE_DIRECTOR\w*|.*?_CS_\w*|.*?CS_DIRECTOR\w*)\s*$", re.I)

def dump(path, *args):
    r = subprocess.run([TWINSDUMP, path] + list(args), capture_output=True, text=True)
    if "Unhandled Exception" in (r.stdout + r.stderr):      # a crashed dump prints nothing useful and must not
        raise RuntimeError(f"twinsdump {args} crashed on {os.path.basename(path)}")  # be read as an empty result
    return r.stdout

def directors(path):
    out = {}
    for line in dump(path, "objects").splitlines():
        m = DIRECTOR.match(line.strip())
        if m: out[int(m.group(1))] = m.group(2).strip()
    return out

def triggered_names(path):
    names = set()
    for line in dump(path, "triggers").splitlines():
        if "->" not in line: continue
        for tgt in line.split("->", 1)[1].split():
            if ":" in tgt: names.add(tgt.split(":", 1)[1])
    return names

def survey(path, level):
    ds = directors(path)
    if not ds: return []
    tnames = triggered_names(path)
    rows = []
    for oid, name in sorted(ds.items()):
        started = any(name in t or t.endswith(name.split("|")[-1]) for t in tnames)
        rows.append((level, oid, name.split("|")[-1], "trigger" if started else "no trigger"))
    return rows

def main():
    wanted = [a.lower() for a in sys.argv[1:]]
    iso = source_iso()
    names = [n for n in archive_names(iso) if n.lower().endswith(".rm2")]
    if wanted:
        names = [n for n in names if os.path.basename(n).lower().rsplit(".", 1)[0] in wanted]
    rows = []
    with open(iso, "rb") as f, tempfile.TemporaryDirectory() as work:
        files = it.iso_files(f)
        for n in sorted(names):
            level = os.path.basename(n).rsplit(".", 1)[0]
            p = os.path.join(work, os.path.basename(n))
            open(p, "wb").write(it.archive_file(f, files, n))
            try: rows += survey(p, level)
            except RuntimeError as e: print(f"  !! {e}", flush=True)
            os.remove(p)

    # validation: a scene confirmed playing on the rig must come back as started
    check = [r for r in rows if r[0] == "gpa11" and "HENCHMANIA" in r[2]]
    if check:
        ok = check[0][3] == "trigger"
        print(f"validation: gpa11 Henchmania director -> {check[0][3]} "
              f"({'as expected, it plays on the rig' if ok else 'WRONG - method is broken, ignore results below'})\n")
        if not ok: return

    by_state = {}
    for level, oid, name, state in rows: by_state.setdefault(state, []).append((level, oid, name))
    for state in ("trigger", "no trigger"):
        group = by_state.get(state, [])
        print(f"{len(group)} directors with {state}:")
        for level, oid, name in group: print(f"    {level:12s} {oid:5d}  {name}")
        print()
    print("A director with no trigger is started some other way - a scene chain, a script message, arriving in the")
    print("level - or not at all. That is a question to test on the rig, not a finding.")

if __name__ == "__main__":
    main()
