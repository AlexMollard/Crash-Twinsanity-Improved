"""Does an actor survive arriving in a level? Repeat the arrival and count.

Some reports are of the form "sometimes, on entry": the Iceberg Lab one says Cortex occasionally just dies as
the level loads, in one of two poses. A save state cannot test that - it replays one arrival, identically,
however many times you load it - so each sample has to be a real level load.

For each run this warps in fresh, locates the actor with findactor (its address moves every load), and reads
its health: the creation helper is at instance+0x10 and health is bits 6-13 of helper+20, which is the field
hurt_sweep tops Crash up through. A run that comes back 0 is the bug, and gets a screenshot; a run that
cannot find the actor at all is reported separately, because that is a different thing from finding it dead.

  python arrival_sweep.py Levels\\Ice\\Hub\\labint 74 --n 20
"""
import argparse, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig, findactor

HELPER_OFF, HEALTH_SHIFT, HEALTH_MASK = 0x10, 6, 0xFF

def health(p, inst):
    helper = p.r32(inst + HELPER_OFF)
    if helper not in findactor.HEAP:
        return None
    return (p.r32(helper + 20) >> HEALTH_SHIFT) & HEALTH_MASK

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help=r"level path, e.g. Levels\Ice\Hub\labint")
    ap.add_argument("objid", type=int, help="object id of the actor to watch (twinsdump <level> objects)")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--settle", type=float, default=2.0, help="seconds after arrival before reading")
    o = ap.parse_args()
    os.makedirs(o.out, exist_ok=True)
    name = "sweep_" + os.path.basename(o.path).lower()
    print("discarding one warp first: the first after a cold boot lands at a default spawn", flush=True)
    rig.level(name, o.path, fresh=True)                  # thrown away, never sampled
    tally = {}
    for run in range(1, o.n + 1):
        try:
            rig.level(name, o.path, fresh=True)
        except SystemExit as e:
            print(f"run {run}: warp failed - {e}", flush=True); tally["warp failed"] = tally.get("warp failed", 0) + 1
            break                                        # a failed warp poisons the ones after it
        time.sleep(o.settle)
        p = rig.Pine()
        hits = findactor.find(p, o.objid, rig.pos(p))
        if not hits:
            verdict = "not found"
        else:
            _, inst, pos = hits[0]
            hp = health(p, inst)
            verdict = "DEAD" if hp == 0 else ("no helper" if hp is None else f"alive hp={hp}")
            if hp == 0:
                rig.screenshot(os.path.join(o.out, f"{name}_{o.objid}_dead{run}.png"))
        tally[verdict.split(" hp=")[0]] = tally.get(verdict.split(" hp=")[0], 0) + 1
        print(f"run {run:3d}: {verdict}", flush=True)
    print("\n" + ", ".join(f"{k} x{v}" for k, v in sorted(tally.items(), key=lambda kv: -kv[1])), flush=True)

if __name__ == "__main__":
    main()
