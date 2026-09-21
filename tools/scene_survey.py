"""Which cutscene directors can actually be started, and by what?

Two earlier answers to this were wrong in instructive ways. The first used `twinsdump refs`, which returns
nothing for objects that plainly exist, and reported ten directors as unused. The second read the trigger list
and asked only "does a trigger name this object", which is better but still cannot tell a trigger that starts
a scene from one that names the object and does nothing.

The mechanism is now known (see wiki/docs/roadmap.md): a trigger carries a **number**, every object holds a
table mapping numbers to scripts - `GetTriggerReceiver`, 0x261d90 - and `FUN_002346b8` runs the script whose
entry matches. Nothing is dispatched, which is why hooking ExecuteEvent over a firing trigger records nothing.
So the question "can this scene start" is now exact and static: a trigger must both target the instance and
carry a number the object's receiver table holds.

The tool refuses to report unless the gpa11 Henchmania director - the one scene watched playing on the rig -
comes back matched, which is the check the first method never had.

What it still cannot see is `TriggerLinkedObjects`, the script command one scene uses to start another. gpa11's
HUB2_TO_HUB3 director has no trigger and its scene plays anyway, 2.5s after the Henchmania scene. So "no
trigger" means "started some other way, or not at all", and stays a question rather than a finding.

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
RECV = re.compile(r"^\s*recv:\s*(.*)$")
INST = re.compile(r"^inst\s+(\d+).*?obj\s+(\d+)\s")
KEY_MASK = 0x3FF                                          # FUN_002346b8 compares the low 10 bits

def dump(path, *args):
    r = subprocess.run([TWINSDUMP, path] + list(args), capture_output=True, text=True)
    if "Unhandled Exception" in (r.stdout + r.stderr):    # a crashed dump prints nothing useful and must not
        raise RuntimeError(f"twinsdump {args} crashed on {os.path.basename(path)}")   # read as an empty result
    return r.stdout

def directors(path):
    """object id -> (name, {receiver number: script it runs})"""
    out, cur = {}, None
    for line in dump(path, "objects").splitlines():
        m = DIRECTOR.match(line.strip())
        if m:
            cur = int(m.group(1)); out[cur] = [m.group(2).strip().split("|")[-1], {}]
            continue
        if cur is not None:
            r = RECV.match(line)
            if r:
                for tok in r.group(1).split():
                    k, _, s = tok.partition("->")
                    if k.isdigit(): out[cur][1][int(k) & KEY_MASK] = s
                cur = None
            elif line.startswith("object "):
                cur = None
    return out

def instance_objects(path):
    """instance index -> object id"""
    out = {}
    for line in dump(path, "instances").splitlines():
        m = INST.match(line.strip())
        if m: out[int(m.group(1))] = int(m.group(2))
    return out

def trigger_numbers(path):
    """object id -> set of numbers triggers carry at it

    A trigger holds *two* numbers, not one: `CreateTriggerEvent` is called with `arg1` and again with `arg2`,
    and which is live depends on the trigger's header. `hdr=0x832` triggers carry theirs in the first slot
    (cavbridg's Cavern director, args=(4,0,0,0), receivers hold 4); `hdr=0x132` ones carry it in the second
    (coreent's, args=(0,4,0,1280), same receiver). Reading only the first invented a whole category of
    "trigger names this object but carries a number it has no receiver for" that was really just the other
    slot. Both are checked, rather than decoding the header bits on one example each."""
    inst = instance_objects(path); out = {}
    for line in dump(path, "triggers").splitlines():
        if "->" not in line: continue
        args = re.search(r"args=\((\d+),(\d+)", line)
        if not args: continue
        carried = {int(args.group(1)) & KEY_MASK, int(args.group(2)) & KEY_MASK}
        for tgt in line.split("->", 1)[1].split():
            if ":" in tgt and tgt.split(":", 1)[0].isdigit():
                oid = inst.get(int(tgt.split(":", 1)[0]))
                if oid is not None: out.setdefault(oid, set()).update(carried)
    return out

def survey(path, level):
    ds = directors(path)
    if not ds: return []
    nums = trigger_numbers(path)
    rows = []
    for oid, (name, recv) in sorted(ds.items()):
        carried = nums.get(oid, set())
        matched = sorted(carried & set(recv))
        if matched:      state, detail = "started", f"trigger carries {matched[0]} -> {recv[matched[0]]}"
        elif carried:    state, detail = "MISMATCH", f"trigger carries {sorted(carried)}, receivers are {sorted(recv)}"
        elif not recv:   state, detail = "no receivers", "nothing can start it by trigger at all"
        else:            state, detail = "no trigger", f"receivers {sorted(recv)} exist but no trigger carries one"
        rows.append((level, oid, name, state, detail))
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

    check = [r for r in rows if r[0] == "gpa11" and "HENCHMANIA" in r[2]]
    if check:
        ok = check[0][3] == "started"
        print(f"validation: gpa11 Henchmania director -> {check[0][3]} ({check[0][4]})\n"
              f"            {'as expected, that scene plays on the rig' if ok else 'WRONG - method is broken, ignore everything below'}\n")
        if not ok: return

    by_state = {}
    for r in rows: by_state.setdefault(r[3], []).append(r)
    for state in ("started", "MISMATCH", "no trigger", "no receivers"):
        group = by_state.get(state, [])
        if not group: continue
        print(f"{len(group)} directors: {state}")
        for level, oid, name, _, detail in group:
            print(f"    {level:12s} {oid:5d}  {name:46s} {detail}")
        print()
    print("A director with no trigger may still be started by another scene: TriggerLinkedObjects is a script")
    print("command, and gpa11's untriggered HUB2_TO_HUB3 copy plays 2.5s after the Henchmania scene ends.")

if __name__ == "__main__":
    main()
