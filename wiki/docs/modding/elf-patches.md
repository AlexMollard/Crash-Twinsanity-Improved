---
id: elf-patches
title: Executable patches
sidebar_position: 3
---

# Executable patches

There are two ways to change the game's code, and they end up in the same place.

`mod/elf_patches.txt` is the original one, one word per line:

```text
ADDRESS  ORIGINAL  PATCHED   # comment
```

Addresses are virtual (the ELF loads at `0x100000`). The build refuses to write a word whose `ORIGINAL` does not
match, so a patch written against a different build fails instead of corrupting anything.

`mod/asm/*.s` is the newer one, and is what new work should use: MIPS assembly, assembled at build time.

```asm
.cave movie_skip                      # goes in the code cave, address assigned by the build
    lui    $a0, 0x30
    lw     $a0, -0x6774($a0)          # G_GameController
    jal    GetButtonPressure          # a name out of the symbol database
    li     $a1, 4                     # ... in the delay slot, where you put it

.patch 0x2AFA6C 0x0C0ABE56            # replace one word, checking what is there first
    jal    movie_skip
```

Names resolve from labels in any `.s` file and then from `tools/re/db/symbols.tsv`, so a hook can call
`GetButtonPressure` rather than `0x2B2250`. A `.patch` block must assemble to exactly as many words as it lists
originals for, which is what stops it running over the instruction after it.

Both mechanisms are applied by `tools/build_mod.py` in one pass over an in-memory copy of the executable, so a
word claimed twice is caught at build time.

## What is patched today

| Group | What it does |
|---|---|
| 480p / 60 Hz output | Two words in `sceGsResetGraph` (patch by PeterDelta) |
| Cutscene skip | Re-points script condition 572 at a new function that tail-calls condition 575, "player N holds Triangle" |
| Aku Aku invincibility | Makes invincibility also block damage flagged as an explosion |
| Faster loading | A stub that flushes queued disc reads before each loader step |
| Hurt flicker | Ends a running grace period properly when a cutscene takes or returns control |
| Game clock | 50 → 60, so the loader's frame budget matches the output |
| Movie pacing | A 5/12 accumulator: 25 fps at 60 Hz |
| Movie skip | Movies answer a held Triangle as well as ✕ |

## How a fix gets made

The pattern is the same every time:

1. **Reproduce it in the rig** and find the moment it happens.
2. **Find the code.** `tools/re/ghidra.py` answers `xref:`, `decomp:` and `callers:` against the
   [twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed) database; there is also a whole-program
   decompile to grep, which is often faster because gp-relative globals do not show up as cross-references.
3. **Confirm the mechanism live.** PINE can write RAM, so the theory can be tested before a single instruction is
   assembled - clearing one flag bit and watching the damage stop, for instance.
4. **Write the patch**, into the [code cave](../engine/executable#the-code-cave) if it needs more than a word or two.
5. **Disassemble the built ELF and read it back.** Hand-assembled MIPS gets branch offsets and delay slots wrong.
6. **Test from a fresh boot** - save states restore the old code with the rest of RAM.
7. **Re-run the regression suite**, because an executable change touches every level at once.

## Live hooks

For investigation you do not need a build at all. Write a small cave into scratch RAM over PINE and replace one
instruction with a jump to it:

```python
p.w32(CAVE + 0, first_original_instruction)
...                                   # log whatever you want into a ring buffer
p.w32(CAVE + 4 * n, J(HOOK + 8))      # jump back past the instruction you replaced
p.w32(HOOK, J(CAVE))                  # the delay slot keeps the hook site's second instruction
```

`tools/rig/hurthook.py` is a worked example: it logs every contact-damage call with the attacker and its flags.

:::warning Do not write through a stale pointer
Player and object pointers move when a level reloads or a cutscene runs. Re-read the global every time. Writing
through a pointer captured before a cutscene corrupted memory and took the emulated CPU down with it - that mistake
cost an afternoon and looked exactly like a mod bug.
:::
