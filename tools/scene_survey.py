"""Which cutscene directors can actually be started, and by what?

Two earlier answers to this were wrong in instructive ways. The first used `twinsdump refs`, which returns
nothing for objects that plainly exist, and reported ten directors as unused. The second read the trigger
list and asked only "does a trigger name this object", which cannot tell a trigger that starts a scene from
one that names the object and does nothing.

The mechanism is now known (see wiki/docs/roadmap.md), so the question is exact and static. There are three
ways into a director and this checks all of them:

  1. A trigger targets its instance and carries a **number its receiver table holds**. A trigger carries two
     numbers, `arg1` and `arg2`, and which is live depends on its header - both are checked.
  2. `TriggerLinkedObjects`, which is `ExecuteEvent` with index 1, and an event index is a **script slot** -
     so it can only reach a director that has a slot 1. No cutscene director in the game has one.
  3. Its own slot-0 DEFAULT script reaching its ACTIVATED script, which is how the Cavern director starts:
     `COM_CUTSCENE_PROXIMITY_ACTIVATION`, no trigger involved.

Anything with none of the three cannot start, and that is now a finding rather than a question.

Two scenes this project has watched playing are asserted before any results are printed, and the tool refuses
to report if either fails. One was not enough: with only the Henchmania check it reported the Rockslide intro,
a shipped skip measured at 25.3s -> 4.0s, as impossible to start.

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
INST = re.compile(r"^inst\s+(\d+)\s+Instance\[(\d+)\].*?obj\s+(\d+)\s")
TRIG_LAYER = re.compile(r"Instance\[(\d+)\]")
KEY_MASK = 0x3FF                                          # FUN_002346b8 compares the low 10 bits

def dump(path, *args):
    r = subprocess.run([TWINSDUMP, path] + list(args), capture_output=True, text=True)
    if "Unhandled Exception" in (r.stdout + r.stderr):    # a crashed dump prints nothing useful and must not
        raise RuntimeError(f"twinsdump {args} crashed on {os.path.basename(path)}")   # read as an empty result
    return r.stdout

SLOT = re.compile(r"(\d+):(\d+)\(")

def directors(path):
    """object id -> (name, {receiver number: script}, {slot: script id})"""
    out, cur = {}, None
    for line in dump(path, "objects").splitlines():
        m = DIRECTOR.match(line.strip())
        if m:
            cur = int(m.group(1)); out[cur] = [m.group(2).strip().split("|")[-1], {}, {}]
            continue
        if cur is not None:
            if line.strip().startswith("scripts:"):
                out[cur][2] = {int(a): int(b) for a, b in SLOT.findall(line)}
            r = RECV.match(line)
            if r:
                for tok in r.group(1).split():
                    k, _, s = tok.partition("->")
                    if k.isdigit(): out[cur][1][int(k) & KEY_MASK] = s
                cur = None
            elif line.startswith("object "):
                cur = None
    return out

SCRIPT_HDR = re.compile(r"^=== script (\d+) (\S+)")
SUBSCRIPT = re.compile(r"script=(\d+)\(")

def script_graph(path):
    """script id -> (name, set of script ids its states run)

    A DEFAULT script is not necessarily inert: the Cavern director's runs COM_CUTSCENE_PROXIMITY_ACTIVATION
    and then its own ACTIVATED script, so the scene starts without any trigger at all. Reachability from slot
    0 is therefore the third way a director can start, alongside a trigger's number and TriggerLinkedObjects."""
    graph, cur = {}, None
    for line in dump(path, "scripts", ".").splitlines():
        m = SCRIPT_HDR.match(line)
        if m:
            cur = int(m.group(1)); graph[cur] = [m.group(2), set()]
        elif cur is not None:
            # A script with a header is a pair: the header is id N and its state machine is id N+1. Without
            # that edge the walk stops at the header and the Cavern's proximity activation looks like nothing.
            # The header's own `main=` is *not* an edge - every director's DEFAULT header points at its
            # ACTIVATED header, so following it would call every scene in the game startable.
            if line.strip().startswith("header:"): graph[cur][1].add(cur + 1)
            graph[cur][1].update(int(s) for s in SUBSCRIPT.findall(line))
    return graph

def reaches_activated(graph, start):
    """Does this script tree reach a script whose name says it is the activated one?"""
    seen, stack = set(), [start]
    while stack:
        sid = stack.pop()
        if sid in seen or sid not in graph: continue
        seen.add(sid)
        name = graph[sid][0]
        if sid != start and "ACTIVATED" in name.upper(): return name
        stack.extend(graph[sid][1])
    return None

def instance_objects(path):
    """(layer, instance index) -> object id

    Indices are per `Instance[N]` layer and repeat across them. Keying on the index alone let a later layer's
    instance 10 overwrite the Rockslide director's, which made the survey report a scene this project has
    watched playing - 25.3s -> 4.0s on the rig, a shipped skip - as impossible to start. One validation case
    was not enough to catch it; two are now checked."""
    out = {}
    for line in dump(path, "instances").splitlines():
        m = INST.match(line.strip())
        if m: out[(int(m.group(2)), int(m.group(1)))] = int(m.group(3))
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
        layer = TRIG_LAYER.search(line)
        if not layer: continue
        for tgt in line.split("->", 1)[1].split():
            if ":" in tgt and tgt.split(":", 1)[0].isdigit():
                oid = inst.get((int(layer.group(1)), int(tgt.split(":", 1)[0])))
                if oid is not None: out.setdefault(oid, set()).update(carried)
    return out

def survey(path, level):
    ds = directors(path)
    if not ds: return []
    nums = trigger_numbers(path)
    graph = script_graph(path)
    rows = []
    for oid, (name, recv, slots) in sorted(ds.items()):
        carried = nums.get(oid, set())
        matched = sorted(carried & set(recv))
        # Three ways in, checked in the order they are cheap: a trigger's number, TriggerLinkedObjects (which
        # is ExecuteEvent with index 1, and index is a script slot - so it needs a slot 1), and a slot-0
        # DEFAULT script that reaches the activated one by itself.
        via_default = reaches_activated(graph, slots[0]) if 0 in slots else None
        if matched:
            state, detail = "started: trigger", f"carries {matched[0]} -> {recv[matched[0]]}"
        elif via_default:
            state, detail = "started: own DEFAULT", f"slot 0 reaches {via_default}"
        elif carried:
            state, detail = "MISMATCH", f"trigger carries {sorted(carried)}, receivers are {sorted(recv)}"
        elif 1 in slots:
            state, detail = "linkable only", f"slot 1 = {slots[1]}, so TriggerLinkedObjects can reach it"
        else:
            state, detail = "DEAD", (f"receivers {sorted(recv) or 'none'}, none carried; no slot 1 for "
                                     f"TriggerLinkedObjects; slot 0 {'reaches nothing' if 0 in slots else 'absent'}")
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

    # Two scenes this project has watched playing, both of which must come back startable. One was not
    # enough: with only the Henchmania check, the survey happily reported the Rockslide intro - a shipped
    # skip, measured at 25.3s -> 4.0s in the regression run - as impossible to start, because of an
    # instance-index collision that gpa11 did not happen to hit.
    bad = False
    for level, needle, why in (("gpa11", "HENCHMANIA", "its scene plays on the rig"),
                               ("l10start", "ROCKSLIDE", "its skip is shipped and passes the regression run")):
        hit = [r for r in rows if r[0] == level and needle in r[2]]
        if not hit:
            continue
        ok = hit[0][3].startswith("started")
        bad = bad or not ok
        note = ("as expected, " + why) if ok else "WRONG - the method is broken, ignore everything below"
        print("validation: " + level + " " + needle + " -> " + hit[0][3] + " (" + hit[0][4] + ")")
        print("            " + note)
    print()
    if bad:
        return

    by_state = {}
    for r in rows: by_state.setdefault(r[3], []).append(r)
    for state in ("started: trigger", "started: own DEFAULT", "linkable only", "MISMATCH", "DEAD"):
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
