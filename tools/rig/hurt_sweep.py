"""Contact-damage sweep: for every level in levels.txt, teleport Crash onto each object instance in turn and record
the ones that hit him. Reads the instance list from the level's .rm2 (twinsdump instances) and hooks the engine's
contact-damage call (0x13E1C8) to count hits, topping Crash's health up between tests so a hit never kills him.

The point is to spot things that hurt although they look harmless; enemies and hazards are expected in the output.

  python hurt_sweep.py [--out FILE] [LEVEL ...]"""
import os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
import rig, hurthook

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted", "Levels")
PLAYER = 0x309908
INST = re.compile(r"^inst\s+(\d+).*?pos=\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)\s+obj \d+ (.*)$")

def instances(level_path):
    rm2 = os.path.join(EXTRACTED, level_path.split("Levels" + os.sep, 1)[-1].replace("\\", os.sep) + ".rm2")
    if not os.path.exists(rm2): return []
    out = subprocess.run([TWINSDUMP, rm2, "instances"], capture_output=True, text=True).stdout
    return [(int(m[1]), (float(m[2]), float(m[3]), float(m[4])), m[5].strip())
            for m in (INST.match(l) for l in out.splitlines()) if m]

def wait_for_player(p, secs=30.0):
    """Wait for a player object to exist and the game to be playing again after a death reload."""
    end = time.time() + secs
    while time.time() < end:
        if rig.player_obj(p) is not None and rig.flow_state(p) == rig.STATE_PLAYING:
            time.sleep(1.0)                       # let the reload settle before trusting the address
            return rig.player_obj(p) is not None
        time.sleep(0.5)
    return False

def sweep(state, level_path, log):
    items = instances(level_path)
    if not items: print(f"{state}: no instance list", flush=True); return
    rig.level(state); p = rig.Pine(); hurthook.install(p)
    def heal():                                   # re-read the player each time: it moves when a level reloads
        ps = p.r32(PLAYER)
        if ps: w = p.r32(ps + 20); p.w32(ps + 20, (w & ~(0xFF << 6)) | (3 << 6))
    hits, skipped, mirrors = {}, [], None
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
        got = p.r32(hurthook.LOG) - before
        if got: hits[name] = hits.get(name, 0) + got
        if rig.player_obj(p) is None: mirrors = None                 # a reload moves the structures
    heal()
    note = f", {len(skipped)} skipped" if skipped else ""
    line = f"{state} ({len(items)} instances, {time.time() - t0:.0f}s{note}): " + (
        ", ".join(f"{k} x{v}" for k, v in sorted(hits.items(), key=lambda kv: -kv[1])) or "nothing hurt Crash")
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
