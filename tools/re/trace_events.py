"""Records which instance receives which script event, on real hardware.

`ExecuteEvent` (0x2616C0) is how anything tells an object instance to run one of its scripts. A cutscene
director that no trigger targets can still be started by scene chaining, or by nothing at all, and the level
data cannot tell those apart: a trigger names its target by instance index, but nothing dumps an instance's
*incoming* links. Watching the events arrive settles it.

The signature is `ExecuteEvent(objInstCxt, eventIndex, instContext, arg4, arg5)`, and the event index is used
as a signed byte, so only its low 8 bits select a script slot.

**This fires constantly** - it is the general event dispatcher - so the ring would wrap in milliseconds if it
were left to. Two things deal with that. `--event` and `--object` filter at the hook, before anything is
stored; and the ring stops when full by default rather than wrapping, so what you capture is the *first* N
events after arming, which is what "does event 1 arrive after I pull the trigger" actually needs. `--wrap`
gives the last N instead. `SEEN` counts everything either way, so the traffic is always visible.

The object is identified twice over, and named. Route A is the instance's own `objectId` at +0x6. Route B
goes through `gameObject` at +0x8 to the `GameObject`'s own `objectId` at +0x4. Both offsets are read from
machine code rather than a struct listing - `lw $a0, 8($s1)` and `lbu $v0, 0xd($a0)` pin the GameObject
layout, and the caller that produced the first captured record passes `instNode->base_type.objInstCxt`, the
same pointer whose `objectId` at +0x6 resolved 876, 877 and 871 correctly elsewhere.

On top of that the dump reads `GameObject.name` (+0x14) straight out of memory, so a row says
`act_HENCHMANIA_BOSSFIGHT_DIRECTOR` rather than a number needing a lookup. That column is self-checking: a
printable name means the whole chain from instance to GameObject held, and garbage means it did not.

An earlier version logged the field at +0x16 as a candidate instance index. It is not one - it stayed -1 for
two instances whose numbers were known, so the column is gone rather than left in to be misread.

Registers: this is the n32 ABI, so r8-r11 are the argument registers $a4-$a7 rather than temporaries - which
Keystone names $t0-$t3 in *O32*, a different four (r12-r15). `ExecuteEvent` uses $a0-$a3 and r8, so the driver
touches only r12-r15, r24, r25 and $at. tools/mipsasm.py refuses the aliased names outright.

    python tools/re/trace_events.py arm [--event 1] [--object 877] [--wrap]
    python tools/re/trace_events.py dump
    python tools/re/trace_events.py disarm

Needs the modded build booted (work/re/test_re.iso). Arm *after* the last save-state load: a state restores
RAM over the cave and puts the original instruction back, which reads as "nothing fired".
"""
import argparse, os, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "rig"))
import addrname
import mipsasm
import rig

CTRL = 0x3DB240
ENABLE, F_EVENT, F_OBJ, SEEN, COUNT, MODE = CTRL, CTRL + 4, CTRL + 8, CTRL + 12, CTRL + 16, CTRL + 20
CODE = 0x3DB400
RING = 0x3DB800                  # 128 records of 32 bytes, ends 0x3DC800, inside the 8K cave
CAP, RECORD = 128, 32

HOOK, RESUME = 0x2616C4, 0x2616CC        # `sd $s1, 0x38($sp)`; 0x2616c8 runs as the delay slot
HOOK_ORIGINAL = 0xFFB10038

DRIVER = """
    lui   $t0, 0x3d
    ori   $t0, $t0, 0xb240
    lw    $t1, 0x0($t0)
    beq   $t1, $zero, out
    nop

    lw    $t1, 0xc($t0)                 # SEEN counts every event, filtered or not, so traffic stays visible
    addiu $t1, $t1, 0x1
    sw    $t1, 0xc($t0)

    lw    $t2, 0x4($t0)                 # event filter, -1 means all. Event 0 is valid, hence -1 and not 0
    addiu $t3, $zero, -0x1
    beq   $t2, $t3, eventok
    nop
    andi  $t8, $a1, 0xff                # the function itself uses only the low byte
    bne   $t2, $t8, out
    nop
eventok:

    beq   $a0, $zero, out               # no instance, nothing worth recording
    nop
    andi  $t2, $a0, 0x3
    bne   $t2, $zero, out
    nop
    srl   $t2, $a0, 0x19
    bne   $t2, $zero, out
    nop

    lw    $t2, 0x8($t0)                 # object filter, 0 means all
    beq   $t2, $zero, objok
    nop
    lhu   $t8, 0x6($a0)
    bne   $t2, $t8, out
    nop
objok:

    lw    $t3, 0x10($t0)                # COUNT
    lw    $t2, 0x14($t0)
    beq   $t2, $zero, slot              # wrap mode: always store
    nop
    sltiu $t2, $t3, 0x80                # stop-when-full: keep the first CAP, keep counting SEEN
    beq   $t2, $zero, out
    nop
slot:
    andi  $t2, $t3, 0x7f
    sll   $t2, $t2, 0x5
    lui   $t1, 0x3d
    ori   $t1, $t1, 0xb800
    addu  $t1, $t1, $t2                 # $t1 = this record

    sw    $ra, 0x0($t1)                 # reached by j, not jal, so $ra is the real caller
    sw    $a0, 0x4($t1)
    sw    $a2, 0x8($t1)
    sh    $t3, 0x16($t1)
    andi  $t2, $a1, 0xff
    sh    $t2, 0x1e($t1)

    lhu   $t2, 0x6($a0)                 # route A: the instance's own objectId
    sh    $t2, 0x10($t1)
    lhu   $t2, 0x4($a0)                 # onSpawnScriptId
    sh    $t2, 0x12($t1)
    lhu   $t2, 0x14($a0)                # chunkIndex_
    sh    $t2, 0x14($t1)

    sw    $zero, 0xc($t1)               # defaults, so a gameObject we refuse to walk reports as absent
    sw    $zero, 0x18($t1)
    ori   $t2, $zero, 0xffff
    sh    $t2, 0x1c($t1)

    lw    $t2, 0x8($a0)                 # gameObject, which is a walked pointer and gets the full guard
    sw    $t2, 0xc($t1)
    beq   $t2, $zero, commit
    nop
    andi  $t8, $t2, 0x3
    bne   $t8, $zero, commit
    nop
    srl   $t8, $t2, 0x19
    bne   $t8, $zero, commit
    nop
    lhu   $t8, 0x4($t2)                 # route B: the GameObject's own objectId, an int at +0x4
    sh    $t8, 0x1c($t1)
    lw    $t8, 0x14($t2)                # GameObject.name.string - the reader pulls the text over PINE
    sw    $t8, 0x18($t1)

commit:
    addiu $t3, $t3, 0x1
    sw    $t3, 0x10($t0)

out:
    sd    $s1, 0x38($sp)                # the instruction the hook replaced
    j     0x2616cc
    nop
"""


def connect(tries=20):
    """PINE serves one client at a time, so the old socket has to be closed before a retry."""
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
        if self.r32(0x3DB210) != 0x53415243:
            raise SystemExit("no cave signature at 0x3DB210 - boot work/re/test_re.iso")


def still_armed(p):
    """A save state restores RAM over the cave and unhooks the site, which reads exactly like 'nothing fired'."""
    code, _ = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    problems = []
    if p.r32(CODE) != struct.unpack("<I", code[:4])[0]:
        problems.append(f"the driver is gone from {CODE:08x}")
    jump, _ = mipsasm.assemble(f"j {CODE:#x}", HOOK, {}, "hook")
    if p.r32(HOOK) != struct.unpack("<I", jump[:4])[0]:
        problems.append(f"{HOOK:08x} is not hooked")
    return problems


def cmd_arm(p, o):
    p.check_cave()
    code, _ = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    for i, w in enumerate(struct.unpack(f"<{len(code) // 4}I", code)):
        p.w32(CODE + 4 * i, w)
    print(f"driver: {len(code)} bytes at {CODE:08x}")

    for a in range(RING, RING + CAP * RECORD, 4):
        p.w32(a, 0)
    p.w32(SEEN, 0)
    p.w32(COUNT, 0)
    p.w32(F_EVENT, 0xFFFFFFFF if o.event is None else o.event & 0xFF)
    p.w32(F_OBJ, o.object or 0)
    p.w32(MODE, 0 if o.wrap else 1)

    present = p.r32(HOOK)
    jump, _ = mipsasm.assemble(f"j {CODE:#x}", HOOK, {}, "hook")
    want = struct.unpack("<I", jump[:4])[0]
    if present == HOOK_ORIGINAL:
        p.w32(HOOK, want)
        print(f"hooked {HOOK:08x} -> {CODE:08x}")
    elif present == want:
        print(f"hook already installed at {HOOK:08x}")
    else:
        raise SystemExit(f"{HOOK:08x} holds {present:08x}, neither the original {HOOK_ORIGINAL:08x} nor our "
                         f"jump {want:08x} - refusing to touch it")

    p.w32(ENABLE, 1)
    ev = "all" if o.event is None else o.event
    print(f"tracing on. event filter {ev}, object filter {o.object or 'all'}, "
          f"{'wrapping' if o.wrap else 'keeping the first %d' % CAP}")


def cmd_dump(p, o):
    p.check_cave()
    problems = still_armed(p)
    if problems:
        print("NOT ARMED: " + "; ".join(problems))
        print("A save state was loaded after arming - it restores RAM over the cave and unhooks the site, so")
        print("the numbers below mean nothing. Re-arm and re-run. Fresh warps do not do this.\n")

    seen, count = p.r32(SEEN), p.r32(COUNT)
    fe, fo, mode = p.r32(F_EVENT), p.r32(F_OBJ), p.r32(MODE)
    print(f"events seen {seen}   recorded {count}" +
          (f"   event filter {fe}" if fe != 0xFFFFFFFF else "") +
          (f"   object filter {fo}" if fo else ""))
    if mode and count >= CAP:
        print(f"the ring filled and stopped - these are the FIRST {CAP} of {seen} matching events")
    elif not mode and count > CAP:
        print(f"the ring wrapped - these are the LAST {CAP} of {count}")
    if seen and not count:
        print("events are arriving but none matched the filter")

    names = addrname.Names()
    shown = min(count, CAP)
    first = 0 if mode else count - shown

    def text(ptr, limit=64):
        """GameObject.name read straight out of the game's memory - self-checking, because a wrong chain
        gives unprintable bytes rather than a plausible-looking name."""
        if not ptr or ptr & 3 or ptr >= 0x02000000:
            return ""
        out = bytearray()
        for i in range(0, limit, 4):
            try:
                w = p.r32(ptr + i)
            except SystemExit:
                break
            chunk = struct.pack("<I", w)
            if b"\0" in chunk:
                out += chunk[:chunk.index(b"\0")]
                break
            out += chunk
        try:
            name = out.decode("ascii")
        except UnicodeDecodeError:
            return "<not text>"
        return name if all(32 <= ord(c) < 127 for c in name) else "<not text>"

    print()
    print(f"  {'seq':>5} {'caller':<38} {'instance':>9} {'ev':>3} {'idA':>5} {'idB':>5} "
          f"{'chunk':>5}  name")
    mismatch, ok = 0, 0
    for n in range(first, first + shown):
        b = RING + (n % CAP) * RECORD
        ra, inst, ctx, gobj = p.r32(b), p.r32(b + 4), p.r32(b + 8), p.r32(b + 12)
        ids, chunkseq, nameptr, idbev = p.r32(b + 16), p.r32(b + 20), p.r32(b + 24), p.r32(b + 28)
        ida, spawn = ids & 0xFFFF, ids >> 16
        chunk, seq = chunkseq & 0xFFFF, chunkseq >> 16
        idb, ev = idbev & 0xFFFF, idbev >> 16
        if seq != (n & 0xFFFF):
            print(f"  {n:>5} <slot overwritten while reading>")
            continue
        ok += 1
        if idb != 0xFFFF and ida != idb:
            mismatch += 1
        f = lambda v: "-" if v == 0xFFFF else str(v)
        print(f"  {n:>5} {names.describe(ra):<38} {inst:>9x} {ev:>3} {f(ida):>5} {f(idb):>5} "
              f"{f(chunk):>5}  {text(nameptr)}")
    if ok:
        if mismatch:
            print()
            print(f"  *** idA and idB disagree on {mismatch} of {shown} rows - the instance's objectId and")
            print("      its GameObject's objectId are not the same object, so neither should be trusted.")
        else:
            print()
            print("  idA and idB agree on every row, by two different paths through memory, and the names")
            print("  read as text - so the instance, its GameObject and both id fields all line up.")
    elif shown:
        print()
        print("  No row could be read: every slot failed its sequence check. That happens when the ring was")
        print("  written by a different version of the driver, so re-arm before reading anything into this.")


def cmd_disarm(p, o):
    p.w32(ENABLE, 0)
    if p.r32(HOOK) == HOOK_ORIGINAL:
        print(f"{HOOK:08x} was not hooked")
    else:
        p.w32(HOOK, HOOK_ORIGINAL)
        print(f"unhooked {HOOK:08x}, original {HOOK_ORIGINAL:08x} restored")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("arm", help="install the hook, clear the records, start tracing")
    a.add_argument("--event", type=int, default=None, help="record only this event index (default: all)")
    a.add_argument("--object", type=int, default=0, help="record only this objectId (default: all)")
    a.add_argument("--wrap", action="store_true", help="keep the last N instead of the first N")
    a.set_defaults(fn=cmd_arm)
    d = sub.add_parser("dump", help="read the records back")
    d.set_defaults(fn=cmd_dump)
    r = sub.add_parser("disarm", help="stop tracing and restore the instruction")
    r.set_defaults(fn=cmd_disarm)
    o = ap.parse_args()
    o.fn(Link(), o)


if __name__ == "__main__":
    main()
