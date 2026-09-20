"""TEST ONLY: a live hook on Command_SetFocusPosition_Run (0x213700), logging which agent struct just had a focus
position written and what its mode bits say.

The agent struct is `*(a2 + 4)` at the command's Run slot - the same one SetAgent reaches - and it holds:
    +0x30 .. +0x3C   Vector4, the focus position
    +0x88            mode bits: bit 0 = focus is an object, bit 1 = focus is a position

That second field is the pre-check that matters: if it reads 0, the actor has no focus at all, and anything you
measure about its steering is meaningless because it has nothing to steer towards.

  import focushook; focushook.install(rig.Pine())
  n, last = focushook.read(p)       # last = [(agent, mode), ...]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testhooks as th

I, Rt, J = th.I, th.Rt, th.J
CAVE, LOG = 0xFF800, 0xFF300
HOOK = 0x213700

def cave():
    return [I(9, "sp", "sp", -224),                 # addiu sp,sp,-224   (the original first instruction)
            I(15, "zero", "t1", 0x10),              # lui   t1,0x10
            I(35, "t1", "t2", -0xD00),              # lw    t2,count
            I(12, "t2", "t3", 15),                  # andi  t3,t2,15
            Rt(0, "zero", "t3", "t3", 3),           # sll   t3,t3,3       (8-byte entries)
            Rt(0x21, "t3", "t1", "t3"),             # addu  t3,t3,t1
            I(35, "a2", "t4", 4),                   # lw    t4,4(a2)      the agent struct
            I(43, "t3", "t4", -0xCF0),              # sw    t4,entry+0
            I(35, "t4", "t5", 0x88),                # lw    t5,0x88(t4)   mode bits
            I(43, "t3", "t5", -0xCEC),              # sw    t5,entry+4
            I(9, "t2", "t2", 1),                    # addiu t2,t2,1
            I(43, "t1", "t2", -0xD00),              # sw    t2,count
            J(HOOK + 4), 0]                         # j 0x213704 ; nop

def install(p):
    for k, word in enumerate(cave()): p.w32(CAVE + 4 * k, word)
    for k in range(0, 0x90, 4): p.w32(LOG + k, 0)
    p.w32(HOOK, J(CAVE))

def read(p, last=6):
    n = p.r32(LOG); out = []
    for k in range(max(0, n - last), n):
        e = LOG + 0x10 + (k & 15) * 8
        out.append((p.r32(e), p.r32(e + 4)))
    return n, out
