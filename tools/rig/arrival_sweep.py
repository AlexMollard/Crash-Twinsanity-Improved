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
BURN = r"Levels\Earth\Hub\beach"   # a level to spend the cold-boot warp on; not the one being sampled

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
    tally = {}
    # Two of the rig's traps meet here and the sample has to dodge both.
    #
    # A level can be warped to **once per emulator session**: warping back to one already visited leaves the
    # game at flow 14, which never settles, and the next warp is refused - measured as labint(12) ->
    # labext(12) -> labint(14). This sweep is repeat warps to one level, which is why it never once produced
    # more than a single sample. So every sample needs a fresh emulator.
    #
    # But the first warp after a cold boot lands at a *default* spawn rather than the level's own, so with a
    # restart per sample every warp becomes a first warp: Crash arrives at (4.79, -0.22, -38.02) instead of
    # labint's (-16.74, -2.83, -11.69), and the actor being watched is nowhere near him. That is what turned
    # the first working version of this into three straight "not found".
    #
    # Restart, throw one warp away somewhere else, then warp to the target. About 55s a sample.
    for run in range(1, o.n + 1):
        try:
            rig.stop(); time.sleep(2)
            rig.start(r"Levels\Earth\Hub\Beach", "test", "1")
            rig.level(name + "_burn", BURN, fresh=True)   # soaks up the cold-boot spawn, never sampled
            rig.level(name, o.path, fresh=True)
        except SystemExit as e:
            print(f"run {run}: warp failed - {e}", flush=True); tally["warp failed"] = tally.get("warp failed", 0) + 1
            continue                                     # a fresh emulator next time, so this one is recoverable
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
