"""Where is an actor actually standing, as opposed to where the level data spawns it?

An instance position from `twinsdump instances` is where an actor is *placed*, not where it is. Cortex in the
Cavern is listed at (-100.23, 100.11) and stands at (-101.00, 92.48) a second after the level loads - eight
units out, which is enough to make "walk over and spin into him" miss three times running. Every attempt to
find him by guessing from the level data failed; this found him on the first try.

Character contexts carry their object id as a u16 at +0x6 and a position at +0xD0, the same fields the player
object uses, so a RAM dump can simply be searched for them. Ids are game-wide (see tools/re/objindex.py), so
the id to pass is the one `twinsdump <level> objects` prints, and it means the same thing in every level.

**This finds characters, not every instance.** The field is confirmed on the two that were checked directly -
the player object reads 0 at +0x6, which is act_CRASH, and Cortex reads 74 - and a checkpoint crate, a lever
switch and an extra-life crate placed within 13 units of Crash were all searched for and none was found, so
props evidently use a different layout. Use it for characters (Cortex, Nina, Evil Crash) and expect nothing
for scenery. A zero-candidate result is therefore not evidence that an object is absent.

The filter is deliberately loose - a finite position, within RADIUS of Crash, not the origin - and every
candidate is printed with its live position read back afterwards rather than one being picked. A stale copy
of a structure reads the same twice while the live one is being stepped, and there is usually only one hit
anyway; where there are several, the caller is the one who knows which it wants.

  python findactor.py 74                 # act_CORTEX, in whichever level is loaded
  python findactor.py 74 --radius 200    # widen the search
  python findactor.py 610 818 --watch 5  # several ids, re-read for 5s to see which are moving
"""
import argparse, array, math, os, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig

ID_OFF, POS_OFF = 0x6, 0xD0

HEAP = range(0x00100000, 0x02000000)

def find(p, want, crash, radius=60.0, dy=25.0):
    """Every instance context in RAM whose object id is `want` and whose position is plausibly in play.

    The id alone is two bytes and matches a great deal of unrelated data: searching labint for Cortex on the
    id and a nearby position gave 42 candidates, 41 of them direction vectors and other small values sitting
    near the origin, because Crash himself is near the origin there. Two structural checks separate them, both
    read off the real ones rather than guessed - the u16 *below* the id, at +0x4, is 0xFFFF on Crash and on
    Cortex and on none of the 41, and the creation-helper pointer at +0x10 points into the heap. Together they
    leave exactly one hit. Being empirical they may also exclude some genuine actor, so an empty result still
    is not proof that an object is absent.

    Object id 0 stays noisy whatever you filter on, because 0 is also what an unset id looks like - 33 hits in
    labint. That one costs nothing: id 0 is Crash, and `rig.pos()` already answers for him."""
    dump = os.path.join(rig.TEST, "actor_ram.bin")
    rig.run(["ram", dump])
    raw = open(dump, "rb").read()
    f = array.array("f"); f.frombytes(raw)
    out = []
    for a in range(0, len(raw) - POS_OFF - 16, 4):
        if struct.unpack_from("<H", raw, a + ID_OFF)[0] != want:
            continue
        if struct.unpack_from("<H", raw, a + 4)[0] != 0xFFFF:
            continue
        if struct.unpack_from("<I", raw, a + 0x10)[0] not in HEAP:
            continue
        i = (a + POS_OFF) // 4
        x, y, z = f[i], f[i + 1], f[i + 2]
        if not all(math.isfinite(v) for v in (x, y, z)) or abs(x) + abs(y) + abs(z) < 1e-4:
            continue
        d = math.hypot(x - crash[0], z - crash[2])
        if d < radius and abs(y - crash[1]) < dy:
            out.append((d, a, (x, y, z)))
    out.sort()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+", type=int, help="object ids, as twinsdump <level> objects prints them")
    ap.add_argument("--radius", type=float, default=60.0, help="how far from Crash to look (default 60)")
    ap.add_argument("--watch", type=float, default=0.0, help="seconds to re-read each hit, to see what moves")
    o = ap.parse_args()
    p = rig.Pine()
    crash = rig.pos(p)
    print(f"crash at ({crash[0]:.2f}, {crash[1]:.2f}, {crash[2]:.2f})", flush=True)
    for want in o.ids:
        hits = find(p, want, crash, o.radius)
        print(f"object {want}: {len(hits)} candidate(s)", flush=True)
        for d, a, pos in hits[:8]:
            line = f"  0x{a:08X}  ({pos[0]:8.2f},{pos[1]:8.2f},{pos[2]:8.2f})  {d:5.1f} from Crash"
            if o.watch:
                time.sleep(o.watch)
                live = [rig.fl(p, a + POS_OFF + 4 * k) for k in range(3)]
                moved = math.dist(live, pos)
                line += f"   after {o.watch:g}s ({live[0]:8.2f},{live[1]:8.2f},{live[2]:8.2f})  moved {moved:.2f}"
            print(line, flush=True)

if __name__ == "__main__":
    main()
