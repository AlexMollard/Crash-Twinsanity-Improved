---
id: executable
title: The executable
sidebar_position: 6
---

# The executable

`SLES_525.68` is a 2 MB PS2 ELF, loaded at virtual address `0x100000`.

```text
file offset = virtual address - 0x100000 + 0x1000
```

PCSX2 identifies a game by a CRC over the executable - a XOR of its words - so every change produces a new CRC and
needs a matching `.pnach`. The build works this out and writes the new patch file itself, deleting the stale one.

## The memory map

The shipped executable has exactly one loadable segment:

```text
PT_LOAD  file 0x1000  vaddr 0x100000  filesz 0x20A460  memsz 0x2DB200
```

| Range | Section | Comes from |
|---|---|---|
| `0x100000-0x2D9D88` | `.text` | the disc |
| `0x2D9D90-0x2E6ED0` | `.vutext` | the disc - VU microcode |
| `0x2E6F00-0x2EC348` | `.data` | the disc |
| `0x2EC400-0x309868` | `.rodata` | the disc |
| `0x309880-0x30A460` | `.sdata` | the disc (end of `filesz`) |
| `0x30A480-0x30ACD8` | `.sbss` | zeroed at boot |
| `0x30AD00-0x3DB200` | `.bss` | zeroed at boot |
| `0x3DB200-` | *(nothing)* | `_end`; everything above is the game's to allocate |

Three details at the top of that map matter, because together they decide what may live at `_end`:

**The boot-time clear overshoots.** `entry()` zeroes the bss with 128-bit `sq` stores in a loop that tests the
address *before* incrementing it, so it runs one store past `_end` and wipes `0x3DB200-0x3DB20F`:

```text
00100018  sq     $zero, 0($v0)        # Ghidra and Capstone both mis-read this - R5900 128-bit store
00100020  sltu   $at, $v0, $v1        # v1 = 0x3DB200
0010002C  bnez   $at, 0x100018
00100030  addiu  $v0, $v0, 0x10       # delay slot: the test used the *old* value
```

**`InitHeap` is not where the game's memory comes from.** `entry()` calls it with `_end` and a size of -1, but that
only sets the ceiling. The floor is `sbrk` (`0x2CFCB0`), whose break pointer is a single `.data` word at
**`0x2EABE4`**, sitting in the image initialised to `0x003DB200`:

```c
void *sbrk(int delta) {
    new = brk + delta;
    if (EndOfHeap() < new) { errno = ENOMEM; return -1; }   // the InitHeap ceiling
    old = brk; brk = new; return old;                       // the _end floor
}
```

The very first thing through it is the game's own 11.5 MB pool - `GetHeapManager_` at `0x181DB0` mallocs
`0xB7E890` bytes and builds its allocator on the result - so in the retail game the pool starts at `0x3DB210`,
sixteen bytes above `_end`, and every object in the game hangs off it.

**One bss array is bounded by `_end`.** `G_BLEND_SHAPE_FLOATS` (`0x3DA260`, `float[1000]`) is the last thing in
`.bss`, and its ring allocator wraps by comparing against the literal `0x3DB200` rather than the end of the array.
It never writes past it.

## How patches are stored

`mod/elf_patches.txt` is a plain list of `ADDRESS ORIGINAL PATCHED` in hex, grouped under `[headings]` with comments:

```text
[Cutscene skip - hold Triangle]
002F0B1C 0012C578 0012C568   # condition 571 check -> condition 570's identical stub, freeing 0x12C578
0012C578 44800000 8C820000   # lw   v0,0(a0)          condition word
0012C57C 03E00008 00021442   # srl  v0,v0,17          parameter = player index
0012C580 00000000 14400031   # bne  v0,zero,0x12C648  tail-call condition 575 (player N holds Triangle)
```

The build checks every `ORIGINAL` value against the disc before it writes anything, so a patch written against a
different build fails loudly instead of corrupting the executable.

## The code cave

Bigger changes need somewhere to put new instructions, and for a long time that meant an unused debug function at
**0x116EA8-0x116FE0** - it builds a human-readable name for an Aku Aku state and nothing calls it. That is 78
words, and cutscene skipping, loading, hurt flicker, movie pacing and movie skipping filled every one of them:

| Range | What lives there |
|---|---|
| `0x116EA8-0x116EDC` | Send queued disc reads immediately ([faster loading](loading)) |
| `0x116EE0-0x116F24` | End a hurt-flicker grace period properly when a cutscene takes control |
| `0x116F28-0x116F70` | Movie pacing: a 5/12 accumulator, 25 fps at 60 Hz ([movies](movies)) |
| `0x116F74-0x116FD8` | Movies answer a held Triangle |
| `0x116FDC` | One word of data: how long Triangle has been held |

### The cave at `_end`

The replacement is an 8 KB region at **`0x3DB200-0x3DD200`**, carved out of the gap the memory map leaves at
`_end`, loaded by a **second `PT_LOAD`** added to the executable. The header has room for it: the program header
table sits at file offset `0x34` and the first section does not start until `0x1000`, so a second 32-byte entry
goes straight after the first and `e_phnum` becomes 2.

Four changes make the region safe to use:

| Change | Why |
|---|---|
| Code starts at `0x3DB210`, not `0x3DB200` | the boot-time bss clear overshoots by one 16-byte store |
| `.data` word at `0x2EABE4`: `0x003DB200` → `0x003DD200` | moves `sbrk`'s break, so the game's pool lands above the cave instead of on top of it |
| `0x1000A0`: `addiu a0, a0, -0x4E00` → `-0x2E00` | moves the `InitHeap` ceiling to match |
| `0x181EA0` and `0x181EC0`: `ori …, 0x3D70` → `0x1D70` | **pays for the cave** - see below |

The `InitHeap` change alone does nothing; patching it and leaving `sbrk` alone was the first attempt, and the
pool landed on the cave anyway. But the fourth row is the one that matters most, and it is not obvious at all.

### There is no spare RAM

The game makes exactly two large allocations, and together they fill the console:

| | Size | |
|---|---|---|
| `GetHeapManager_` `0x181DB0` | `0x00B7E890` — 11.5 MB | the general pool, everything the game allocates |
| `GetDiskManager_` `0x181E58` | `0x010A3D70` — 16.6 MB | the streaming buffer |

Measured on the retail disc at the title screen:

```text
pool                0x003DB210 .. 0x00F59AA0
streaming buffer    0x00F59AB0 .. 0x01FFD820
sbrk break          0x01FFE000
top of RAM          0x02000000
```

**8 KB of headroom in 32 MB**, and the kernel keeps that for itself. So moving `sbrk` up by a cave's worth does
not take memory from nowhere - it pushes the *second* of those two allocations past the ceiling `sbrk` checks
against. `sbrk` returns -1, `malloc` returns null, and the graphics init at `0x1AF150` cheerfully writes a
structure through the null pointer, field by field from `+0` to `+0xD4`. Fifty TLB misses and a black screen.

:::danger The cave costs something, and you have to say what
`tools/elfpatch.py` shrinks the streaming buffer by exactly the cave size, so total memory use is unchanged and
`sbrk`'s break lands back on `0x01FFE000` to the byte. 8 KB out of 16.6 MB is 0.05% of one buffer - but it is
not free, and growing the cave means taking more. Any change to `CAVE_SIZE` needs the loading benchmarks re-run,
not just a boot test.
:::

Verified on the rig: boots and renders, the signature word is at `0x3DB210`, the pool has moved to `0x3DD210`,
and the streaming buffer allocation succeeds.

```bash
python tools/rig/rig.py read 0x3DB210 2      # 53415243 ("CRAS"), 00002000
```

:::warning Check the screen, not just the memory
The first version of this cave was reported working on the strength of memory reads alone - the signature was
present, the pool had moved, and 511 markers written across the region were untouched after "play". The markers
were untouched because the game had crashed in graphics init before it could allocate anything. A dead game
leaves memory alone beautifully. Take a screenshot.
:::

:::note The disc has to make room too
The image is packed solid - there is not one spare sector between files. A bigger executable pushes the music
bank, the archive header and CRASH.BD along, which `isotools.write_elf` does; only the 221 MB of music is
actually copied, because CRASH.BD is streamed in from the source disc afterwards anyway.
:::

## Writing MIPS

New patches are written as assembly in `mod/asm/*.s` and assembled by `tools/mipsasm.py` (Keystone underneath).
It is not a general assembler, and the reasons are worth knowing, because each one silently changes code:

- **Delay slots get filled for you.** LLVM inserts a `nop` after every branch unless `.set noreorder` is in force,
  so a hand-written delay slot becomes two instructions. The prelude always sets it.
- **"Macro" forms expand.** `lw $v0, 0x9908($v0)` - an offset that does not fit in a signed 16 bits - quietly
  becomes three instructions using a scratch register. `.set nomacro` does *not* stop this one. Write
  `lw $v0, -0x66F8($v0)`, or an explicit `lui`/`ori` pair.
- **`la` does not work** in MIPS64 mode at all ("la used to load 64-bit address"). Use `lui` + `ori`.
- **Branch targets from the symbol resolver land one instruction too far.** Keystone measures them from the branch
  rather than from the delay slot after it. Absolute `j`/`jal` are fine. `mipsasm` subtracts 4 for anything whose
  mnemonic starts with `b` (every MIPS `b*` is a branch except `break`).
- **The R5900's 128-bit instructions are not supported** - `lq`, `sq`, `pextlw`, `mflo1` and friends. Write them as
  `.word`. Capstone cannot disassemble them either, which is why the bss clear at `0x100018` reads as nonsense.

Because macro expansion is invisible, the assembler measures every source line on a first pass and checks it comes
out the same size on the second, and errors naming the line if it does not.

### Doing it by hand

`mod/elf_patches.txt` is still hand-assembled R5900 words. Three things go wrong every time:

1. **Branch delay slots.** The instruction after a branch or jump always runs. Putting a `j` in a delay slot does not
   do what you want.
2. **Branch offsets** are counted in words from *the instruction after the branch*. Recompute them whenever you insert
   a line.
3. **`beql` / `bnel`** ("branch likely") only execute their delay slot when the branch is taken.

Always disassemble the built ELF and read it back before testing - it is far cheaper than a rig run. There is a small
disassembler used for exactly this in the session scratch notes, and `tools/re/ghidra.py` runs queries against the
[twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed) Ghidra database:

```bash
python tools/re/ghidra.py xref:0x309908 decomp:0x13e010 callers:0x116ea8
```
