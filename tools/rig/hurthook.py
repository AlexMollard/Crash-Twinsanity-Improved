"""TEST ONLY: a live hook on the engine's contact-damage call (0x13E1C8, "this actor just touched the player, hurt
him"), logging the attacker into a ring buffer at 0xFF400. Used to tell what actually hit Crash and whether an object
still carries contact damage (its creation helper's flags, bit 8).

  import hurthook; hurthook.install(rig.Pine())
  n, last = hurthook.read(p)      # n = total hits since install; last = (attacker, helper, flags, player)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testhooks as th

I, Rt, J = th.I, th.Rt, th.J
CAVE, LOG = 0xFF700, 0xFF400
HOOK = 0x13E1C8

def cave():
    return [I(9, "sp", "sp", -64),                 # addiu sp,sp,-64  (the original first instruction)
            I(15, "zero", "t1", 0x10),             # lui   t1,0x10
            I(35, "t1", "t2", -0xC00),             # lw    t2,count
            I(12, "t2", "t3", 15),                 # andi  t3,t2,15
            Rt(0, "zero", "t3", "t3", 4),          # sll   t3,t3,4
            Rt(0x21, "t3", "t1", "t3"),            # addu  t3,t3,t1
            I(43, "t3", "a0", -0xBF0),             # sw    a0,entry+0    the attacking instance
            I(35, "a0", "t4", 16),                 # lw    t4,16(a0)     its creation helper
            I(43, "t3", "t4", -0xBEC),             # sw    t4,entry+4
            I(35, "t4", "t5", 16),                 # lw    t5,16(t4)     the helper's flags (bit 8 = hurts on contact)
            I(43, "t3", "t5", -0xBE8),             # sw    t5,entry+8
            I(43, "t3", "a1", -0xBE4),             # sw    a1,entry+12   the player
            I(9, "t2", "t2", 1),                   # addiu t2,t2,1
            I(43, "t1", "t2", -0xC00),             # sw    t2,count
            J(HOOK + 8), 0]                        # j 0x13E1D0 ; nop   (the delay slot keeps sd s0,48(sp))

def install(p):
    for k, word in enumerate(cave()): p.w32(CAVE + 4 * k, word)
    for k in range(0, 0x120, 4): p.w32(LOG + k, 0)
    p.w32(HOOK, J(CAVE))

def read(p, last=4):
    n = p.r32(LOG); out = []
    for k in range(max(0, n - last), n):
        e = LOG + 0x10 + (k & 15) * 16
        out.append(tuple(hex(p.r32(e + i)) for i in (0, 4, 8, 12)))
    return n, out
