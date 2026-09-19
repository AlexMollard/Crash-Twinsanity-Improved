"""Generates the TEST-ONLY PCSX2 patch section for the rig (never shipped in the mod):
  - virtual pad: hook after padRead in the controller update (0x2b324c) that, when enabled, overwrites
    port 0's raw pad bytes (controller+1398..1415) with 18 bytes the rig writes over PINE
  - level warp (done at runtime by rig.py, no patch needed): the start-level global START_LEVEL holds a char*
    that New Game reads; the rig writes a path to WARP_STR and points START_LEVEL at it
Memory used (EE kernel-area gap below the ELF, verified unused at runtime by the rig):
  0x000FF000  vpad enable (u32)      0x000FF004  vpad raw bytes (18)
  0x000FF100  hook code              0x000FF200  warp level path (NUL-terminated)"""
import struct

VPAD_EN, VPAD_RAW, CAVE, WARP_STR = 0x000FF000, 0x000FF004, 0x000FF100, 0x000FF200
START_LEVEL = 0x0030BE80
HOOK_AT, HOOK_RET = 0x2B324C, 0x2B3260
R = {n: i for i, n in enumerate("zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split())}

def I(op, rs, rt, imm): return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xFFFF)
def Rt(fn, rs, rt, rd, sa=0): return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | fn
def J(addr): return (2 << 26) | ((addr >> 2) & 0x3FFFFFF)

def assemble_cave():
    code, labels, fixups = [], {}, []
    def emit(x): code.append(x)
    def br(op, rs, rt, label): fixups.append((len(code), label)); emit(I(op, rs, rt, 0))
    br(7, "v0", "zero", "L1")                 # bgtz v0, L1   (pad read ok -> keep bytes)
    emit(0)
    emit(I(40, "s0", "zero", 1398))           # sb zero,1398(s0)   (read failed: original clears)
    emit(I(40, "s0", "zero", 1399))           # sb zero,1399(s0)
    labels["L1"] = len(code)
    emit(I(35, "s0", "t0", 1280))             # lw t0,1280(s0)     port
    br(5, "t0", "zero", "L2")                 # bne t0,zero,L2     only port 0
    emit(I(15, "zero", "t1", 0x0010))         # lui t1,0x10        (delay)
    emit(I(35, "t1", "t2", VPAD_EN - 0x100000))   # lw t2,-0x1000(t1)
    br(4, "t2", "zero", "L2")                 # beq t2,zero,L2
    emit(I(9, "zero", "t3", 0))               # addiu t3,zero,0    (delay) i=0
    labels["LOOP"] = len(code)
    emit(Rt(0x21, "t1", "t3", "t4"))          # addu t4,t1,t3
    emit(I(36, "t4", "t5", VPAD_RAW - 0x100000))  # lbu t5,-0xffc(t4)
    emit(Rt(0x21, "s0", "t3", "t6"))          # addu t6,s0,t3
    emit(I(40, "t6", "t5", 1398))             # sb t5,1398(t6)
    emit(I(9, "t3", "t3", 1))                 # addiu t3,t3,1
    emit(I(10, "t3", "t7", 18))               # slti t7,t3,18
    br(5, "t7", "zero", "LOOP")               # bne t7,zero,LOOP
    emit(0)
    labels["L2"] = len(code)
    emit(I(36, "s0", "v1", 1398))             # lbu v1,1398(s0)    (what the original delay slot loaded)
    emit(J(HOOK_RET))                         # j 0x2b3260
    emit(0)
    for at, label in fixups:
        code[at] |= (labels[label] - (at + 1)) & 0xFFFF
    return code

def pnach_section():
    lines = ["[Test Rig]", "author=CrashModded test rig",
             "description=TEST ONLY - virtual pad over PINE + New Game level warp. Never enable in normal play."]
    for k, word in enumerate(assemble_cave()):
        lines.append(f"patch=1,EE,2{CAVE + 4*k:07X},word,{word:08X}")
    lines.append(f"patch=1,EE,2{HOOK_AT:07X},word,{J(CAVE):08X}")      # j cave
    lines.append(f"patch=1,EE,2{HOOK_AT + 4:07X},word,00000000")       # nop (was lbu v1,1398(s0))
    return "\n".join(lines)

if __name__ == "__main__":
    print(pnach_section())
