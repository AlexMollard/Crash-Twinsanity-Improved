"""Records who calls ActivateObjectInstance, on real hardware, while the game runs.

ActivateObjectInstance (0x263390) is reached through vtable slot 6, so there is nothing static that separates
its 49 call sites - the slot offset +0x34 appears in dozens of unrelated classes. This answers the question by
measurement instead: a small driver in the code cave logs every entry, and the return address names the caller.

Two records are kept, because they answer different questions.

  A bitmap, one bit per object id.  It cannot overflow and it cannot wrap, so "was id 877 ever activated at
  all" has a definite answer no matter how much traffic a level load produces. This is the question that
  actually matters: if the bit is clear he is never activated and the caller list tells us who should have
  done it; if it is set he is activated and dies later, which would overturn a conclusion we have been
  treating as settled.

  A ring of the last 256 entries, with the caller, the instance pointer, the object id, the chunk index and
  the spawn script id. This is the detail, and being a ring it does wrap - COUNT says how many entries were
  stored in total, so a dump reports honestly whether anything was lost. Use --filter to record only one
  object id, which in practice cannot wrap at all.

The hook goes on the function's *second* instruction. Patching the first would leave the second running as
the jump's delay slot before the prologue finished, and more importantly $a0 is consumed at +0xc, so the
instance pointer has to be read before then:

    00263390  addiu $sp, $sp, -0x20
    00263394  sd    $s0, 0($sp)      <- hooked; $a0 and $ra both still live here
    00263398  sd    $s1, 8($sp)      <- runs as our jump's delay slot, harmless
    0026339c  daddu $s0, $a0         <- $a0 consumed

Needs the modded build booted (work/re/test_re.iso) because the cave is reserved memory there. Nothing the
game owns is written, and `disarm` puts the original instruction back.

    python tools/re/trace_activate.py arm [--filter 877]
    python tools/re/trace_activate.py dump [--all-ids]
    python tools/re/trace_activate.py disarm
"""
import argparse, bisect, os, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "rig"))
import mipsasm
import rig

CTRL = 0x3DB240                  # enable, filter, count, seen, nulls, out-of-range
ENABLE, FILTER, COUNT, SEEN, NULLS, OOR = CTRL, CTRL + 4, CTRL + 8, CTRL + 12, CTRL + 16, CTRL + 20
CODE = 0x3DB400                  # driver, ~200 bytes of the 1K budget
BITMAP = 0x3DB800                # 1024 bytes, one bit per id, covers 0..8191
BITMAP_BYTES = 1024
RING = 0x3DBC00                  # 256 records of 16 bytes, ends at 0x3DCC00, inside the 8K cave
CAP = 256
RECORD = 16

HOOK = 0x263394                  # ActivateObjectInstance's `sd $s0, 0($sp)`
HOOK_ORIGINAL = 0xFFB00000
RESUME = HOOK + 8                # the instruction between them already ran, as our jump's delay slot

# $at, $v0, $v1, $t0-$t3, $t8 and $t9 are caller-saved, so at a function's entry they are all dead and free.
# $sp is never touched, which keeps this independent of the frame the prologue is halfway through building.
# $a0 and $a1 are the live arguments and are only read.
#
# Every offset is written in hex on purpose: Keystone reads an unprefixed number as hexadecimal, so `12($t0)`
# would assemble as offset 18. tools/mipsasm.py now refuses bare numbers rather than let that through, and
# it also refuses $t4-$t7, which in this register naming are r12-r15 - the same four as $t0-$t3.
DRIVER = """
    lui   $t0, 0x3d
    ori   $t0, $t0, 0xb240          # $t0 = control block
    lw    $t1, 0x0($t0)
    beq   $t1, $zero, out           # tracing switched off - fall straight through
    nop

    lw    $t1, 0xc($t0)             # every activation counts toward SEEN, even a filtered-out one
    addiu $t1, $t1, 0x1
    sw    $t1, 0xc($t0)

    beq   $a0, $zero, nullinst
    nop

    lhu   $t2, 0x6($a0)             # objectId
    lhu   $t3, 0x14($a0)            # chunkIndex
    lhu   $t9, 0x4($a0)             # onSpawnScriptId

    lw    $t8, 0x4($t0)             # FILTER, zero means record everything
    beq   $t8, $zero, bitmap
    nop
    bne   $t8, $t2, out
    nop

bitmap:
    sltiu $at, $t2, 0x2000          # an id past the bitmap still gets a ring record, just no bit
    beq   $at, $zero, outofrange
    nop
    srl   $v0, $t2, 0x3
    lui   $v1, 0x3d
    ori   $v1, $v1, 0xb800
    addu  $v0, $v0, $v1             # $v0 = the byte holding this id's bit
    lbu   $v1, 0x0($v0)
    andi  $t8, $t2, 0x7
    ori   $at, $zero, 0x1
    sllv  $at, $at, $t8
    or    $v1, $v1, $at
    sb    $v1, 0x0($v0)

record:
    lw    $t1, 0x8($t0)             # COUNT is monotonic; the slot is COUNT mod 256
    andi  $v1, $t1, 0xff
    sll   $v0, $v1, 0x4
    lui   $v1, 0x3d
    ori   $v1, $v1, 0xbc00
    addu  $v0, $v0, $v1
    sw    $ra, 0x0($v0)             # reached by j, not jal, so $ra is still the real caller
    sw    $a0, 0x4($v0)
    sh    $t2, 0x8($v0)
    sh    $t3, 0xa($v0)
    sh    $t1, 0xc($v0)
    sh    $t9, 0xe($v0)
    addiu $t1, $t1, 0x1
    sw    $t1, 0x8($t0)
    beq   $zero, $zero, out
    nop

outofrange:
    lw    $t1, 0x14($t0)
    addiu $t1, $t1, 0x1
    sw    $t1, 0x14($t0)
    beq   $zero, $zero, record      # no bit for it, but still worth a ring record
    nop

nullinst:
    lw    $t1, 0x10($t0)
    addiu $t1, $t1, 0x1
    sw    $t1, 0x10($t0)

out:
    sd    $s0, 0x0($sp)             # the instruction the hook replaced
    j     0x26339c
    nop
"""


def connect(tries=20):
    """PCSX2's PINE server serves one client at a time, so the old socket has to be closed before a retry -
    leaking them wedges the server for everything, including whatever else is using the rig."""
    for _ in range(tries):
        try:
            if rig._conn is not None:
                try:
                    rig._conn.s.close()
                except Exception:
                    pass
            rig._conn = None
            p = rig.Pine(timeout=20)
            p.status()
            return p
        except Exception:
            time.sleep(2)
    raise SystemExit("PINE never answered - is the rig running? (rig.py start --iso re)")


class Link:
    """PINE drops the odd call over a long run, so every access retries and reconnects if it has to."""

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

    def check_cave(self):
        sig = self.r32(0x3DB210)
        if sig != 0x53415243:
            raise SystemExit(f"cave signature at 0x3DB210 is {sig:08x}, not 'CRAS' - boot work/re/test_re.iso")


def load_symbols():
    """Function starts, so a return address can be reported as a name plus an offset into it."""
    path = os.path.join(HERE, "db", "symbols.tsv")
    funcs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            col = line.rstrip("\n").split("\t")
            if len(col) >= 3 and col[1] == "F":
                try:
                    funcs.append((int(col[0], 16), col[2]))
                except ValueError:
                    pass
    funcs.sort()
    return [a for a, _ in funcs], [n for _, n in funcs]


def describe(addr, starts, names):
    if not starts:
        return f"{addr:08x}"
    i = bisect.bisect_right(starts, addr) - 1
    if i < 0 or addr - starts[i] > 0x4000:
        return f"{addr:08x}"
    delta = addr - starts[i]
    return f"{names[i]}+0x{delta:x}" if delta else names[i]


def cmd_arm(p, o):
    p.check_cave()
    code, _ = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    words = struct.unpack(f"<{len(code) // 4}I", code)
    for i, w in enumerate(words):
        p.w32(CODE + 4 * i, w)
    print(f"driver: {len(code)} bytes at {CODE:08x}")

    for a in range(BITMAP, BITMAP + BITMAP_BYTES, 4):
        p.w32(a, 0)
    for a in (COUNT, SEEN, NULLS, OOR):
        p.w32(a, 0)
    p.w32(FILTER, o.filter or 0)

    present = p.r32(HOOK)
    if present == HOOK_ORIGINAL:
        jump, _ = mipsasm.assemble(f"j {CODE:#x}", HOOK, {}, "hook")
        p.w32(HOOK, struct.unpack("<I", jump[:4])[0])
        print(f"hooked {HOOK:08x} -> {CODE:08x}")
    else:
        expect, _ = mipsasm.assemble(f"j {CODE:#x}", HOOK, {}, "hook")
        if present != struct.unpack("<I", expect[:4])[0]:
            raise SystemExit(f"hook site {HOOK:08x} holds {present:08x}, which is neither the original "
                             f"{HOOK_ORIGINAL:08x} nor our jump - refusing to touch it")
        print(f"hook already installed at {HOOK:08x}")

    p.w32(ENABLE, 1)
    print(f"tracing on, filter = {o.filter if o.filter else 'none (all ids)'}")


def cmd_dump(p, o):
    p.check_cave()
    count, seen = p.r32(COUNT), p.r32(SEEN)
    nulls, oor, filt = p.r32(NULLS), p.r32(OOR), p.r32(FILTER)
    print(f"activations seen {seen}   recorded {count}   null instance {nulls}   id past bitmap {oor}")
    if filt:
        print(f"filter: only object id {filt}")
    if count > CAP:
        print(f"the ring wrapped - showing the last {CAP} of {count}; use --filter to stop losing entries")

    ids = []
    for i in range(BITMAP_BYTES // 4):
        w = p.r32(BITMAP + 4 * i)
        if not w:
            continue
        for b in range(32):
            if w >> b & 1:
                ids.append((i * 4 + b // 8) * 8 + (b % 8))
    print(f"\ndistinct object ids activated: {len(ids)}")
    if o.all_ids:
        print("  " + " ".join(str(i) for i in sorted(ids)))
    for want in o.look_for:
        print(f"  id {want}: {'ACTIVATED' if want in ids else 'never activated'}")

    starts, names = load_symbols()
    shown = min(count, CAP)
    print(f"\nlast {shown} entries, oldest first:")
    print(f"  {'seq':>6}  {'caller':<44} {'instance':>10} {'id':>6} {'chunk':>6} {'spawn':>6}")
    first = count - shown
    for n in range(first, count):
        base = RING + (n % CAP) * RECORD
        ra, ptr = p.r32(base), p.r32(base + 4)
        packed_a, packed_b = p.r32(base + 8), p.r32(base + 12)
        oid, chunk = packed_a & 0xFFFF, packed_a >> 16
        seq, spawn = packed_b & 0xFFFF, packed_b >> 16
        if seq != (n & 0xFFFF):
            print(f"  {n:>6}  <slot overwritten while reading>")
            continue
        print(f"  {n:>6}  {describe(ra, starts, names):<44} {ptr:>10x} {oid:>6} {chunk:>6} {spawn:>6}")

    callers = {}
    for n in range(first, count):
        base = RING + (n % CAP) * RECORD
        callers.setdefault(describe(p.r32(base), starts, names), []).append(p.r32(base + 8) & 0xFFFF)
    print("\ncallers, by how many entries each accounts for:")
    for name, seq in sorted(callers.items(), key=lambda kv: -len(kv[1])):
        uniq = sorted(set(seq))
        tail = "" if len(uniq) <= 12 else f" ... ({len(uniq)} ids)"
        print(f"  {len(seq):>5}  {name:<44} ids {' '.join(str(i) for i in uniq[:12])}{tail}")


def cmd_disarm(p, o):
    p.w32(ENABLE, 0)
    present = p.r32(HOOK)
    if present == HOOK_ORIGINAL:
        print("hook was not installed")
    else:
        p.w32(HOOK, HOOK_ORIGINAL)
        print(f"unhooked {HOOK:08x}, original {HOOK_ORIGINAL:08x} restored")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("arm", help="install the hook, clear the records, start tracing")
    a.add_argument("--filter", type=int, default=0, help="record only this object id (0 = all)")
    a.set_defaults(fn=cmd_arm)

    d = sub.add_parser("dump", help="read the records back")
    d.add_argument("--all-ids", action="store_true", help="list every object id that was activated")
    d.add_argument("--look-for", type=int, nargs="*", default=[877],
                   help="report yes/no for these ids (default: 877, Evil Crash)")
    d.set_defaults(fn=cmd_dump)

    r = sub.add_parser("disarm", help="stop tracing and put the original instruction back")
    r.set_defaults(fn=cmd_disarm)

    o = ap.parse_args()
    o.fn(Link(), o)


if __name__ == "__main__":
    main()
