"""Records focus-object acquisition on real hardware, from both ends of the branch that decides it.

`FUN_00113A18` searches for a nearest candidate and then goes one of two ways: it calls `FUN_001214E8` when
it found nothing, or `FUN_00121480` with the winner when it did. Hooking both turns "why has this agent no
focus object" into a four-way answer that needs no interpretation:

  only 0x1214E8 fires      the search ran and found no candidate - the gap is upstream, in the list searched
  0x121480 fires, value 0  something assigned a null focus, which leaves the gate shut and looks like success
  0x121480 fires, value!=0 it does acquire a focus object, so whatever fails next fails for a third reason
  neither fires            nothing ever tried to acquire focus for this agent - look at its script, not here

The per-hook counters in the control block answer that much on their own and cannot wrap, which is the point:
the ring is for detail and the counters are for the verdict.

`agent + 0x88` bit 0 is the gate that `Condition_GotFocusObject_Check` reads. Only `FUN_00121480` in mode 0
sets it, and only when the value is non-null; `FUN_001214E8` in mode 0 clears bits 0 and 1 together, so it
actively shuts the gate rather than merely failing to open it. Both functions pick their mode from
`cmd + 0x30 & 3` and modes 1 and 2 write different fields entirely, so the mode is recorded too - a run that
sees only modes 1 and 2 has found a different code path, not a failure.

Both hook sites are leaf functions with no stack prologue, and both begin with the identical instruction
`lw $v1, 0x30($a0)` (0x8C830030). The instruction after it, `addiu $v0, $zero, 1`, runs as our jump's delay
slot, so **$v0 must not be touched** - the comparison two instructions later depends on it. $v1 is free
because the replaced instruction reloads it on the way out.

    python tools/re/trace_focus.py arm [--filter 876]
    python tools/re/trace_focus.py dump
    python tools/re/trace_focus.py disarm

Needs the modded build booted (work/re/test_re.iso), because the cave is reserved memory only there.
Run a level where some actor demonstrably acquires a focus object first, as a control, before the one in
question - a tracer that reports "never fired" is indistinguishable from a tracer that is not working.
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
ENABLE, FILTER, COUNT = CTRL, CTRL + 4, CTRL + 8
SEEN_ASSIGN, SEEN_NONE, SEEN_NULL = CTRL + 12, CTRL + 16, CTRL + 20
CODE = 0x3DB400
RING = 0x3DB800                  # 128 records of 32 bytes, ends 0x3DC800, inside the 8K cave
CAP, RECORD = 128, 32

HOOK_A, RESUME_A = 0x121480, 0x121488       # FUN_00121480(cmd=$a0, value=$a1, agent=$a2)
HOOK_B, RESUME_B = 0x1214E8, 0x1214F0       # FUN_001214E8(cmd=$a0, agent=$a1)
HOOK_ORIGINAL = 0x8C830030                  # lw $v1, 0x30($a0) - the same in both

# Free here: $at, $v1, $a3, $t0-$t3, $t8, $t9. NOT $v0 (set by the delay slot and compared two instructions
# later), and not $a0-$a2, which both functions go on to use.
#
# Every literal carries 0x on purpose - Keystone reads a bare number as hex, so `0x7c($t1)` written as
# `124($t1)` would read offset 0x124. tools/mipsasm.py refuses bare numbers now, and refuses $t4-$t7, which
# are the same four registers as $t0-$t3 in this naming.
DRIVER = """
entryA:                                 # 0x121480: cmd $a0, value $a1, agent $a2
    ori   $t0, $zero, 0x0
    daddu $t1, $a2, $zero
    daddu $t2, $a1, $zero
    lui   $t3, 0x12
    ori   $t3, $t3, 0x1488
    beq   $zero, $zero, body
    nop

entryB:                                 # 0x1214e8: cmd $a0, agent $a1, no value
    ori   $t0, $zero, 0x1
    daddu $t1, $a1, $zero
    daddu $t2, $zero, $zero
    lui   $t3, 0x12
    ori   $t3, $t3, 0x14f0

body:
    lui   $t8, 0x3d
    ori   $t8, $t8, 0xb240
    lw    $t9, 0x0($t8)
    beq   $t9, $zero, out
    nop

    beq   $t0, $zero, countassign       # the counters are kept before the filter, so they count everything
    nop
    lw    $t9, 0x10($t8)
    addiu $t9, $t9, 0x1
    sw    $t9, 0x10($t8)
    beq   $zero, $zero, counted
    nop
countassign:
    lw    $t9, 0xc($t8)
    addiu $t9, $t9, 0x1
    sw    $t9, 0xc($t8)
    bne   $t2, $zero, counted
    nop
    lw    $t9, 0x14($t8)                # assigned, but the value was null - the quiet failure
    addiu $t9, $t9, 0x1
    sw    $t9, 0x14($t8)
counted:                                # the record is written first and only committed at the end: the slot
    lw    $t9, 0x8($t8)                 # comes from COUNT, so a record that fails the filter is simply left
    andi  $a3, $t9, 0x7f                # to be overwritten. That keeps every value in a register only as
    sll   $a3, $a3, 0x5                 # long as it takes to store it, which is what makes this fit.
    lui   $v1, 0x3d
    ori   $v1, $v1, 0xb800
    addu  $v1, $v1, $a3                 # $v1 = this record
    sw    $ra, 0x0($v1)
    sw    $t1, 0x4($v1)
    sw    $t2, 0x8($v1)
    sw    $a0, 0xc($v1)
    sh    $t9, 0x1a($v1)

    lw    $a3, 0x30($a0)                # mode in the high byte, which-hook in the low
    andi  $a3, $a3, 0x3
    sll   $a3, $a3, 0x8
    or    $a3, $a3, $t0
    sh    $a3, 0x18($v1)

    ori   $at, $zero, 0xffff            # the node's own objId_, which is legitimately -1 when undefined
    daddu $a3, $zero, $zero
    beq   $t1, $zero, haveids
    nop
    lhu   $at, 0x7c($t1)
    lw    $a3, 0x84($t1)                # objInstCxt - the route real engine code uses
haveids:
    sh    $at, 0x10($v1)
    sw    $a3, 0x1c($v1)

    ori   $t9, $zero, 0xffff            # route A: objInstCxt->objectId, straight off the agent
    beq   $a3, $zero, haveobj
    nop
    lhu   $t9, 0x6($a3)
haveobj:
    sh    $t9, 0x12($v1)

    ori   $t2, $zero, 0xffff            # route B: agent -> instContext -> node 1 -> objInstCxt -> objectId,
    beq   $t1, $zero, haveb             # which is what FUN_00114048 does to identify a candidate. Reaching
    nop                                 # the same id two ways is the only thing that can settle whether the
    lw    $a3, 0x0($t1)                 # agent really is node index 1.
    beq   $a3, $zero, haveb
    nop
    lw    $a3, 0xdc($a3)                # nodesList_ at ctx+0xd4, nodes[] at +4, index 1 -> ctx+0xdc
    beq   $a3, $zero, haveb
    nop
    lw    $a3, 0x84($a3)
    beq   $a3, $zero, haveb
    nop
    lhu   $t2, 0x6($a3)
haveb:
    sh    $t2, 0x16($v1)

    daddu $a3, $zero, $zero
    beq   $t1, $zero, nogate
    nop
    lw    $a3, 0x88($t1)                # the gate bits as they were on entry
nogate:
    sh    $a3, 0x14($v1)

    lw    $a3, 0x4($t8)                 # the filter matches any of the three, so it works whichever turns
    beq   $a3, $zero, commit            # out to be the meaningful one
    nop
    beq   $a3, $t9, commit
    nop
    beq   $a3, $t2, commit
    nop
    bne   $a3, $at, out
    nop
commit:
    lw    $t9, 0x8($t8)
    addiu $t9, $t9, 0x1
    sw    $t9, 0x8($t8)

out:
    jr    $t3
    lw    $v1, 0x30($a0)                # the replaced instruction, run in the jump's delay slot
"""


def connect(tries=20):
    """PINE serves one client at a time, so the old socket has to be closed before a retry - leaking them
    wedges the server for everything, including whatever else is using the rig."""
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
        sig = self.r32(0x3DB210)
        if sig != 0x53415243:
            raise SystemExit(f"cave signature at 0x3DB210 is {sig:08x}, not 'CRAS' - boot work/re/test_re.iso")




def cmd_arm(p, o):
    p.check_cave()
    code, labels = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    for i, w in enumerate(struct.unpack(f"<{len(code) // 4}I", code)):
        p.w32(CODE + 4 * i, w)
    print(f"driver: {len(code)} bytes at {CODE:08x}, entryB at {labels['entryB']:08x}")

    for a in range(RING, RING + CAP * RECORD, 4):
        p.w32(a, 0)
    for a in (COUNT, SEEN_ASSIGN, SEEN_NONE, SEEN_NULL):
        p.w32(a, 0)
    p.w32(FILTER, o.filter or 0)

    for site, target, tag in ((HOOK_A, CODE, "0x121480 assign"), (HOOK_B, labels["entryB"], "0x1214E8 none")):
        present = p.r32(site)
        jump, _ = mipsasm.assemble(f"j {target:#x}", site, {}, "hook")
        want = struct.unpack("<I", jump[:4])[0]
        if present == HOOK_ORIGINAL:
            p.w32(site, want)
            print(f"hooked {site:08x} ({tag}) -> {target:08x}")
        elif present == want:
            print(f"hook already installed at {site:08x} ({tag})")
        else:
            raise SystemExit(f"{site:08x} holds {present:08x}, neither the original {HOOK_ORIGINAL:08x} nor "
                             f"our jump {want:08x} - refusing to touch it")

    p.w32(ENABLE, 1)
    print(f"tracing on, filter = {o.filter if o.filter else 'none (all agents)'}")


def still_armed(p):
    """Is the driver still in the cave and are both sites still hooked?

    Loading a save state restores RAM over the whole cave, driver and counters alike, and puts the original
    instructions back at both sites - so everything reads zero and the run looks like "neither hook fired",
    which is a real answer to a different question. Fresh warps are fine, because those load a level in
    place. Arm after the last state load, never before."""
    code, labels = mipsasm.assemble(DRIVER, CODE, {}, "driver")
    first = struct.unpack("<I", code[:4])[0]
    problems = []
    if p.r32(CODE) != first:
        problems.append(f"the driver is gone from {CODE:08x}")
    for site, target in ((HOOK_A, CODE), (HOOK_B, labels["entryB"])):
        jump, _ = mipsasm.assemble(f"j {target:#x}", site, {}, "hook")
        if p.r32(site) != struct.unpack("<I", jump[:4])[0]:
            problems.append(f"{site:08x} is not hooked")
    return problems


def cmd_dump(p, o):
    p.check_cave()
    problems = still_armed(p)
    if problems:
        print("NOT ARMED: " + "; ".join(problems))
        print("A save state was almost certainly loaded after arming - that restores RAM over the cave and")
        print("puts the original instructions back, so the counters below mean nothing. Re-arm and re-run.")
        print("Fresh warps do not do this; only state loads.\n")
    count = p.r32(COUNT)
    assign, none, null = p.r32(SEEN_ASSIGN), p.r32(SEEN_NONE), p.r32(SEEN_NULL)
    filt = p.r32(FILTER)

    print(f"0x121480 assign fired {assign}  (of which null value {null})")
    print(f"0x1214E8 none   fired {none}")
    print(f"records stored {count}" + (f", filtered to objId {filt}" if filt else ""))
    print()
    if assign == 0 and none == 0:
        print("VERDICT: neither fired - nothing tried to acquire focus at all. If the control level did")
        print("         produce hits, the gap is in this agent's script rather than in the engine.")
    elif assign == 0:
        print("VERDICT: only the not-found path fired - the search ran and found no candidate, so the gap")
        print("         is upstream in whatever list it searches.")
    elif assign > null:
        print("VERDICT: a non-null focus object was assigned, so the gate should have opened. Whatever")
        print("         fails next fails for a reason that is not focus acquisition.")
    else:
        print("VERDICT: every assignment carried a null value, which leaves the gate shut while nothing")
        print("         looks like it failed.")
    if count > CAP:
        print(f"\nthe ring wrapped - showing the last {CAP} of {count}; the counters above are still exact")

    names = addrname.Names()
    shown = min(count, CAP)
    print(f"\nlast {shown} entries, oldest first:")
    print(f"  {'seq':>5} {'hook':<7} {'caller':<32} {'agent':>9} {'value':>9} "
          f"{'objCxt':>9} {'idA':>5} {'idB':>5} {'own':>5} {'mode':>4} {'gate':>4}")
    disagree = 0
    for n in range(count - shown, count):
        b = RING + (n % CAP) * RECORD
        ra, agent, value, cmd = p.r32(b), p.r32(b + 4), p.r32(b + 8), p.r32(b + 12)
        ids, gb, whoseq, objcxt = p.r32(b + 16), p.r32(b + 20), p.r32(b + 24), p.r32(b + 28)
        own, ida = ids & 0xFFFF, ids >> 16
        gate, idb = gb & 0xFFFF, gb >> 16
        which, mode, seq = whoseq & 0xFF, (whoseq >> 8) & 0xFF, whoseq >> 16
        if seq != (n & 0xFFFF):
            print(f"  {n:>5} <slot overwritten while reading>")
            continue
        if ida != idb:
            disagree += 1
        tag = "assign" if which == 0 else "none"
        fmt = lambda v: "undef" if v == 0xFFFF else str(v)
        print(f"  {n:>5} {tag:<7} {names.describe(ra):<32} {agent:>9x} {value:>9x} "
              f"{objcxt:>9x} {fmt(ida):>5} {fmt(idb):>5} {fmt(own):>5} {mode:>4} {gate & 3:>4}")
    if shown:
        print("\nidA is agent + 0x84 -> objInstCxt -> +0x6. idB goes the long way the engine's own candidate")
        print("filter goes: agent + 0 -> instContext -> node 1 -> +0x84 -> +0x6. Both offsets are read from")
        print("machine code, not from a struct listing. 'own' is the node's objId_ at +0x7c, where `undef`")
        print("is a real value - the engine writes -1 to mean 'no object id'.")
        if disagree:
            print(f"\n  *** idA and idB disagree on {disagree} of {shown} entries. The agent is then not node")
            print("      index 1, and idB is the one to believe - it is the route FUN_00114048 uses.")
        else:
            print("\n  idA and idB agree on every entry, by two different routes through memory. The id is")
            print("  what the engine thinks it is; if it is absent from the level files, it came from")
            print("  somewhere else rather than from a bad read.")


def cmd_disarm(p, o):
    p.w32(ENABLE, 0)
    for site in (HOOK_A, HOOK_B):
        if p.r32(site) == HOOK_ORIGINAL:
            print(f"{site:08x} was not hooked")
        else:
            p.w32(site, HOOK_ORIGINAL)
            print(f"unhooked {site:08x}, original {HOOK_ORIGINAL:08x} restored")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("arm", help="install both hooks, clear the records, start tracing")
    a.add_argument("--filter", type=int, default=0, help="record only this agent objId (0 = all)")
    a.set_defaults(fn=cmd_arm)
    d = sub.add_parser("dump", help="read the counters and the ring back")
    d.set_defaults(fn=cmd_dump)
    r = sub.add_parser("disarm", help="stop tracing and restore both instructions")
    r.set_defaults(fn=cmd_disarm)
    o = ap.parse_args()
    o.fn(Link(), o)


if __name__ == "__main__":
    main()
