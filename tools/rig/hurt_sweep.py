"""Contact-damage sweep: for every level in levels.txt, teleport Crash onto each object instance in turn and see
what touches him. Reads the instance list from the level's .rm2 (twinsdump instances) and hooks the engine's
contact-damage call (0x13E1C8), topping Crash's health up between tests so a hit never kills him.

The point is to spot things that hurt although they look harmless; enemies and hazards are expected.

What it does NOT do any more is assume the thing that touched Crash is the thing he was teleported onto. That
is what the first working version reported, and it was wrong: on the beach it named act_GEM_BLUE 28 times, but
the hook entries all carry the same attacker, act_TRAINING_EXPLODING_IDOL_HEAD_CROWN, firing about 45 times a
second in every window regardless of where Crash was standing. Gems were simply what he happened to be
standing on while something else kept touching him.

So each entry is attributed to its own logged attacker, resolved through the object id at attacker+0x6 (the
same field that reads 0 = act_CRASH on the player, which is how it was checked). An attacker that shows up at
nearly every spot is in permanent contact rather than reacting to the teleport, and is marked (everywhere)
instead of being counted as a discovery.

The call fires per frame of contact, not once per touch, so the useful number is how many distinct spots an
attacker turned up at, not how many entries it produced.

  python hurt_sweep.py [--out FILE] [LEVEL ...]"""
import os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
import rig, hurthook

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted", "Levels")
PLAYER = 0x309908
RING = 16                                     # hurthook's log is a 16-entry ring; a busy window overruns it
INST = re.compile(r"^inst\s+(\d+).*?pos=\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)\s+obj \d+ (.*)$")

def rm2_for(level_path):
    rm2 = os.path.join(EXTRACTED, level_path.split("Levels" + os.sep, 1)[-1].replace("\\", os.sep) + ".rm2")
    return rm2 if os.path.exists(rm2) else None

def instances(rm2):
    out = subprocess.run([TWINSDUMP, rm2, "instances"], capture_output=True, text=True).stdout
    return [(int(m[1]), (float(m[2]), float(m[3]), float(m[4])), m[5].strip())
            for m in (INST.match(l) for l in out.splitlines()) if m]

def object_names(rm2):
    """object id -> short name, for turning a logged attacker address into something readable."""
    out = subprocess.run([TWINSDUMP, rm2, "objects", "."], capture_output=True, text=True).stdout
    names = {}
    for l in out.splitlines():
        m = re.match(r"^object (\d+) (.*)", l)
        if m: names[int(m.group(1))] = m.group(2).split("|")[-1].strip()
    return names

def attacker_of(p, addr, names):
    oid = (p.r32(addr + 4) >> 16) & 0xFFFF     # object id is the u16 at +0x6
    return names.get(oid, f"obj{oid}")

def wait_for_player(p, secs=30.0):
    """Wait for a player object to exist and the game to be playing again after a death reload."""
    end = time.time() + secs
    while time.time() < end:
        if rig.player_obj(p) is not None and rig.flow_state(p) == rig.STATE_PLAYING:
            time.sleep(1.0)                    # let the reload settle before trusting the address
            return rig.player_obj(p) is not None
        time.sleep(0.5)
    return False

def sweep(state, level_path, log):
    rm2 = rm2_for(level_path)
    if not rm2: print(f"{state}: no instance list", flush=True); return
    items, names = instances(rm2), object_names(rm2)
    if not items: print(f"{state}: no instance list", flush=True); return
    rig.level(state); p = rig.Pine(); hurthook.install(p)
    def heal():                                # re-read the player each time: it moves when a level reloads
        ps = p.r32(PLAYER)
        if ps: w = p.r32(ps + 20); p.w32(ps + 20, (w & ~(0xFF << 6)) | (3 << 6))
    who = {}                                   # attacker name -> [spots seen at, entries, entries with bit 8]
    skipped, mirrors, visited = [], None, 0
    t0 = time.time()
    for n, (x, y, z), name in items:
        # Topping his health up does not make him immortal: a bottomless drop, a crusher or simply landing
        # inside geometry still kills him, and then the level reloads and there is no player object at all
        # for several seconds. That used to end the whole sweep on an unpack error; wait it out instead.
        if rig.player_obj(p) is None and not wait_for_player(p):
            skipped.append(name); continue
        heal()
        before = p.r32(hurthook.LOG)
        try:
            mirrors = rig.teleport(x, y + 1.0, z, mirrors=mirrors)   # reuse: a dump per instance is the whole cost
        except SystemExit:
            skipped.append(name); mirrors = None; continue
        time.sleep(0.7)
        visited += 1
        got = p.r32(hurthook.LOG) - before
        if got:
            _, entries = hurthook.read(p, RING)
            for e in entries[-min(got, RING):]:
                rec = who.setdefault(attacker_of(p, int(e[0], 16), names), [set(), 0, 0])
                rec[0].add(n); rec[1] += 1; rec[2] += 1 if int(e[2], 16) & 0x100 else 0
        if rig.player_obj(p) is None: mirrors = None                 # a reload moves the structures
    heal()
    parts = []
    for nm, (spots, hits, hurt) in sorted(who.items(), key=lambda kv: -len(kv[1][0])):
        # Something present at essentially every spot is permanently in contact, not something the teleport
        # found. Saying so is the whole difference between this run and the one that blamed the gems.
        tag = " (everywhere)" if visited and len(spots) >= visited * 0.9 else ""
        parts.append(f"{nm} at {len(spots)} spot(s){tag}" + (f", {hurt}/{hits} flagged damaging" if hurt else ""))
    note = f", {len(skipped)} skipped" if skipped else ""
    line = (f"{state} ({len(items)} instances, {time.time() - t0:.0f}s{note}): "
            + ("; ".join(parts) or "nothing touched Crash"))
    print(line, flush=True); log.write(line + "\n"); log.flush()

def main():
    args = sys.argv[1:]
    out = os.path.join(HERE, "results", "hurt_sweep.txt")
    if "--out" in args: out = args.pop(args.index("--out") + 1); args.remove("--out")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    seen = set()
    with open(out, "a", encoding="utf-8") as log:
        log.write(f"\n=== sweep {time.strftime('%Y-%m-%d %H:%M')}\n")
        for line in open(os.path.join(HERE, "levels.txt"), encoding="utf-8"):
            s = line.split("#", 1)[0].split()
            if len(s) < 2 or (args and s[0] not in args) or s[1] in seen: continue
            seen.add(s[1])
            if not os.path.exists(os.path.join(rig.STATES_DIR, s[0] + ".p2s")):
                print(f"{s[0]}: no state", flush=True); continue
            try: sweep(s[0], s[1], log)
            except SystemExit as e: print(f"{s[0]}: FAILED {e}", flush=True); rig.pine_reset()

if __name__ == "__main__":
    main()
