"""Runs the engine's own segment-triangle test on real hardware and checks the C rewrite against it.

There is no way to call a function in the emulated game directly, so this builds a small driver in the code
cave, hooks it into the per-frame loader, and drives it over PINE: write the inputs, set a trigger word, wait
for the done word, read the results back. The cave is reserved memory, so nothing the game owns is touched,
and the hook is removed afterwards.

The hook goes on the loader's *second* instruction rather than its first. Patching the first would leave the
instruction after it running as the branch's delay slot before the prologue has adjusted the stack pointer,
and the `sd $s0, 0x10($sp)` there would then write into the caller's frame.

  python tools/decomp/collision_test.py [--cases N]
"""
import argparse, os, random, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "rig"))
import mipsasm
import rig

P1, P2, TRI = 0x3DB300, 0x3DB310, 0x3DB320
DIST, EDGES = 0x3DB360, 0x3DB370
SAVED, TRIGGER, DONE, CODE = 0x3DB3D0, 0x3DB3F0, 0x3DB3F4, 0x3DB400

# MainRender's second instruction. The background loader looked like the obvious per-frame hook and is not:
# it only runs while something is streaming, so at the title screen it is never called at all.
HOOK = 0x17DC6C                  # MainRender's `sd $s0, ($sp)`, after the prologue has moved the stack pointer
HOOK_ORIGINAL = 0xFFB00000
RESUME = HOOK + 8                # the instruction after it already ran, as our jump's delay slot

DRIVER = """
    lui   $t0, 0x3d
    ori   $t0, $t0, 0xb3f0
    lw    $t1, 0($t0)
    beqz  $t1, skip
    nop
    sw    $zero, 0($t0)

    lui   $t2, 0x3d                 # park the registers we are about to use, in the cave not on the stack
    ori   $t2, $t2, 0xb3d0
    sw    $ra, 0($t2)
    sw    $a0, 4($t2)
    sw    $a1, 8($t2)
    sw    $a2, 12($t2)
    sw    $a3, 16($t2)

    lui   $a0, 0x3d                 # SegmentTriangleDistances(p1, p2, tri, distances)
    ori   $a0, $a0, 0xb300
    lui   $a1, 0x3d
    ori   $a1, $a1, 0xb310
    lui   $a2, 0x3d
    ori   $a2, $a2, 0xb320
    lui   $a3, 0x3d
    ori   $a3, $a3, 0xb360
    jal   0x293340
    nop

    lui   $a0, 0x3d                 # ReadEdgeTestsFromVu0(edges) - nothing may touch VU0 in between
    ori   $a0, $a0, 0xb370
    jal   0x2933e4
    nop

    lui   $t2, 0x3d
    ori   $t2, $t2, 0xb3d0
    lw    $ra, 0($t2)
    lw    $a0, 4($t2)
    lw    $a1, 8($t2)
    lw    $a2, 12($t2)
    lw    $a3, 16($t2)

    lui   $t0, 0x3d
    ori   $t0, $t0, 0xb3f4
    li    $t1, 1
    sw    $t1, 0($t0)
skip:
    sd    $s0, 0($sp)               # the instruction the hook replaced
    j     0x17dc74
    nop
"""


def connect(tries=20):
    """PCSX2's PINE server serves one client at a time, so the old socket has to be closed before a retry -
    leaking them wedges the server for everything, including later runs."""
    for _ in range(tries):
        try:
            if rig._conn is not None:
                try: rig._conn.s.close()
                except Exception: pass
            rig._conn = None
            p = rig.Pine(timeout=20)
            p.status()
            return p
        except Exception:
            time.sleep(2)
    raise SystemExit("PINE never answered - is the rig running? (rig.py start --iso re)")


class Link:
    """PINE over a long run drops the odd call, so every access retries and reconnects if it has to."""

    def __init__(self):
        self.p = connect()

    def _retry(self, fn):
        for attempt in range(6):
            try:
                return fn(self.p)
            except Exception:
                time.sleep(0.5 + attempt)
                self.p = connect(5)
        raise SystemExit("PINE stopped answering")

    def r32(self, a):
        return self._retry(lambda p: p.r32(a))

    def w32(self, a, v):
        return self._retry(lambda p: p.w32(a, v))


def write_words(p, addr, words):
    for i, w in enumerate(words):
        p.w32(addr + 4 * i, w)


def read_words(p, addr, n):
    return [p.r32(addr + 4 * i) for i in range(n)]


def f2i(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def random_case(rng):
    """A segment and a triangle, sized like real level geometry and often actually crossing."""
    def pt(scale=40.0):
        return [rng.uniform(-scale, scale) for _ in range(3)] + [1.0]
    tri = [pt(), pt(), pt()]
    if rng.random() < 0.6:                      # aim a good share of cases through the triangle
        cx = [(tri[0][i] + tri[1][i] + tri[2][i]) / 3.0 for i in range(3)]
        d = [rng.uniform(-1, 1) for _ in range(3)]
        t = rng.uniform(2.0, 20.0)
        a = [cx[i] - d[i] * t for i in range(3)] + [1.0]
        b = [cx[i] + d[i] * t for i in range(3)] + [1.0]
    else:
        a, b = pt(), pt()
    return a, b, tri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=250)
    ap.add_argument("--seed", type=int, default=1)
    o = ap.parse_args()

    exe = os.path.join(HERE, "collision.exe")
    if not os.path.exists(exe):
        raise SystemExit("build the C first: clang -O2 -ffp-contract=off -o collision.exe collision.c")

    p = Link()
    sig = p.r32(0x3DB210)
    if sig != 0x53415243:
        raise SystemExit(f"cave signature at 0x3DB210 is {sig:08x}, not 'CRAS' - boot work/re/test_re.iso")

    code, _ = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    print(f"driver: {len(code)} bytes at {CODE:08x}")
    write_words(p, CODE, list(struct.unpack(f"<{len(code)//4}I", code)))
    p.w32(TRIGGER, 0)
    p.w32(DONE, 0)

    present = p.r32(HOOK)
    if present != HOOK_ORIGINAL:
        raise SystemExit(f"hook site {HOOK:08x} holds {present:08x}, expected {HOOK_ORIGINAL:08x}")
    jump, _ = mipsasm.assemble(f"j {CODE:#x}", HOOK, {}, "hook")
    p.w32(HOOK, struct.unpack("<I", jump[:4])[0])
    print(f"hooked {HOOK:08x} -> {CODE:08x}")

    rng = random.Random(o.seed)
    cases, ran = [], 0
    try:
        for _ in range(o.cases):
            a, b, tri = random_case(rng)
            words = [f2i(x) for x in a] + [f2i(x) for x in b]
            for v in tri: words += [f2i(x) for x in v]
            write_words(p, P1, words)
            p.w32(DONE, 0)
            p.w32(TRIGGER, 1)
            # The driver only runs when MainRender next does, so the poll has to span at least a frame.
            # Without the sleep, two hundred PINE reads finish inside one, and the trigger looks ignored.
            for _ in range(120):
                if p.r32(DONE): break
                time.sleep(0.02)
            else:
                raise SystemExit("the driver never ran - is the game actually running?")
            out = read_words(p, DIST, 2) + read_words(p, EDGES, 6)
            cases.append((words, out))
            ran += 1
    finally:
        p.w32(HOOK, HOOK_ORIGINAL)
        print(f"unhooked after {ran} case(s)")

    stdin = "\n".join(" ".join(f"{w:08x}" for w in words) for words, _ in cases) + "\n"
    got = subprocess.run([exe], input=stdin, capture_output=True, text=True).stdout.split("\n")

    exact = near = wrong = 0
    worst = None
    for (words, hw), line in zip(cases, got):
        c = [int(x, 16) for x in line.split()[:8]]
        if c == hw:
            exact += 1
            continue
        diffs = [abs(struct.unpack("<f", struct.pack("<I", x))[0] -
                     struct.unpack("<f", struct.pack("<I", y))[0]) for x, y in zip(c, hw)]
        rel = max(d / max(1e-30, abs(struct.unpack("<f", struct.pack("<I", y))[0])) for d, y in zip(diffs, hw))
        if rel < 1e-6:
            near += 1
            if worst is None or rel > worst[0]: worst = (rel, words, hw, c)
        else:
            wrong += 1
            if worst is None or rel > worst[0]: worst = (rel, words, hw, c)

    print(f"\ncases {len(cases)}   bit-identical {exact}   within 1e-6 {near}   diverged {wrong}")
    if worst:
        rel, words, hw, c = worst
        print(f"\nworst relative difference {rel:.3e}")
        print("  hardware " + " ".join(f"{w:08x}" for w in hw))
        print("  C        " + " ".join(f"{w:08x}" for w in c))
    return 0 if wrong == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
