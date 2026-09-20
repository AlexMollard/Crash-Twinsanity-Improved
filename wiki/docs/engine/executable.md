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

Bigger changes need somewhere to put new instructions. The game has an unused debug function at **0x116EA8-0x116FE0**
- it builds a human-readable name for an Aku Aku state and nothing calls it. That is 78 words of free space, and the
mod has now filled it:

| Range | What lives there |
|---|---|
| `0x116EA8-0x116EDC` | Send queued disc reads immediately ([faster loading](loading)) |
| `0x116EE0-0x116F24` | End a hurt-flicker grace period properly when a cutscene takes control |
| `0x116F28-0x116F70` | Movie pacing: a 5/12 accumulator, 25 fps at 60 Hz ([movies](movies)) |
| `0x116F74-0x116FD8` | Movies answer a held Triangle |
| `0x116FDC` | One word of data: how long Triangle has been held |

:::danger The cave is full
There is no free space left in it. The next executable patch needs a new home - another unreferenced function, or
padding at the end of a section.
:::

## Writing MIPS by hand

The patches are hand-assembled R5900 (MIPS III-ish) words. Three things go wrong every time:

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
