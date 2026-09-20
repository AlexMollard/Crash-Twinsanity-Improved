---
id: reverse-engineering
title: Reverse engineering
sidebar_position: 5
---

# Reverse engineering

Everything the mod knows about the executable comes out of a Ghidra project: Smartkin's
[twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed), restored from the `.gar` archive in that
repository. That project is a binary blob, it is not in version control here, and it is re-restored whenever
upstream updates it - so anything learned inside it is lost unless it is written down somewhere else.

`tools/re/db/` is that somewhere else. Three text files, all in git, all diffable:

| File | What |
|---|---|
| `symbols.tsv` | every named function and global - address, kind, name, prototype |
| `comments.tsv` | every comment in the database |
| `types.h` | the structs, unions and enums, as a C header |

```bash
python tools/re/ghidra.py export      # Ghidra project -> tools/re/db
python tools/re/ghidra.py import      # tools/re/db -> Ghidra project
python tools/re/ghidra.py import dry  # what would change, without changing it
```

Import never overwrites a name a human gave the program; the files fill in gaps and restore what was lost. So
the safe order after an upstream update is: restore the new `.gar`, then `import`.

:::tip Grep the files, not the database
A headless Ghidra query costs about eight seconds. `grep tools/re/db/symbols.tsv` costs nothing, and the whole
program decompiled to one file (`tools/ghidra/SLES_525.68.c`, regenerated with
`python tools/re/ghidra.py decompile`) is usually faster still - especially for gp-relative globals, which do
not show up as cross-references at all.
:::

## Names the engine gives away

Scripts pick engine behaviour by number - condition 572, command 619 - and the executable turns those numbers
into objects through two jump tables, found by reading the `sltiu` bound out of each dispatch:

| Table | Entries | Indexed by | Builder |
|---|---|---|---|
| `0x2EC530` | 663 | command id | `BuildScriptCommand` `0x101720`, entered with `a2 == -10` |
| `0x2ECF90` | 646 | condition id **+ 1** | `BuildScriptCondition` `0x106C40`, `a2 == -11` |

Both counts are the `sltiu` bound in the dispatch, so they are the engine's own numbers rather than a guess.

Each entry is a builder: allocate 0x14 bytes, store a pointer to a static methods table, store the id. And the
Twinsanity Editor already knows what most of those numbers are called, in `DefaultEnums.cs` (`CommandID`,
`ConditionID`). Joining the two names 990 things at once:

```bash
python tools/re/autoname.py          # -> tools/re/db/generated.tsv
```

:::warning Scan past the branch
Most builders end with `b <shared tail>` and complete the methods-table pointer in the **delay slot**, which
still runs. A scan that stops at the branch finds only a third of the command tables - which is exactly what
the first version of `autoname.py` did, and why `Command_NowMoveForwards_Run` was missing from it.
:::

The methods tables are the interesting half, because they hold the functions that do the work. All 240 have the
same shape:

| Slot | Condition | Command |
|---|---|---|
| `+0x0C` | reads the condition out of the level data | |
| `+0x14` | **the check** - what a script evaluates | reads the command out of the level data |
| `+0x1C` | a destructor, the same one in all 118 | **the action** - what the command does |

Both of those are confirmed against things already known independently: the mod re-points condition 572's check
at `0x2F0AB8 + 0x14`, and the function at `Command_BottomTextDisplay_Methods + 0x1C` is the one that writes a
string, a position and a duration into the renderer.

So `Condition_GotUserMessageEquals_Check` is `0x22A708` and `Command_BottomTextDisplay_Run` is `0x120E98` -
and those names work in `mod/asm/*.s` directly, because the assembler resolves against the same file.

### How much this is worth trusting

Where a generated name landed on an address Ghidra had already named by hand, all ten agreed about what the
function does; two of the generated ones are better. `AnimationProgressCondition` is condition 5, `TimeInUnit` -
its check returns elapsed ticks times `G_TIME_TO_TICKS`, which is what the wiki already said about its
threshold being in seconds. `DistanceFromPlayerCondition` is `MeToFocusSqrDist`: the focus, not the player, and
squared.

A generated name is only emitted when it is unambiguous. An id whose builder is shared with another id is the
"not implemented" stub and is skipped; so is a methods-table slot whose function is shared between commands.

## Script command arguments

A command's arguments each carry a **3-bit tag** in their first word, and once all three readers are named the
encoding is plain:

| Bit | Meaning |
|---|---|
| 0 | the value is an *instance property index*, not a literal |
| 1-2 | the type: **0** int, **1** angle, **2** float |

```text
GetScriptIntArg    0x209A68    (arg & 6) == 0   value is arg >> 3, or property arg >> 3
GetScriptAngleArg  0x209AB0    (arg & 6) == 2   converted through AngleToFixed
GetScriptFloatArg  0x209A00    (arg & 6) == 4
```

Which is why `NowTurn`'s rate arrives as a **fixed-point angle** rather than a float, and why
`Command_NowTurn_Run` feeds it to `AngleToQuaternion` (`0x18DDB0`), whose constant is 2π/65536 halved for the
half-angle. Turn rates in scripts are in 65536ths of a revolution per second, not radians.

## What is named, and what is not

| | Functions |
|---|---|
| Named | **1,851** |
| Still `FUN_xxxxxxxx` | ~5,050 |
| Total | 6,902 |

It was 962 before any of this. Of the unnamed remainder, roughly 590 are short enough to read off their machine
code, 3,500 are small or mid-sized helpers, and 1,900 are substantial.

Three shortcuts that people usually reach for do not work on this binary, so they are worth not trying twice.

:::note Instruction shapes give almost nothing
`tools/re/shapes.py` classifies every function short enough to read off its machine code - about 590 of them.
The result is **one** thunk worth naming, 99 that return a constant and 27 that return nothing. Not a single
nameable field accessor, because an unnamed function has no parameter types to work an offset against.
:::

:::note There are no debug symbols to mine
Naming functions after the assert or printf strings they reference does not work here. The retail executable
contains **267 printable strings in total**, and they are save-game prompts, the copyright line and SDK version
tags. No source file names, no function names, no asserts - not even the engine's own name. Whatever else gets
named has to be worked out from what the code does.
:::

:::note The PS2 SDK signatures are already applied
`twinsanity-reversed` ships `ps2_sdk_3.0.3.fidb` and `PS2_SDK_3.0.3_libs.fidb`, and it is tempting to assume
nobody ran them, because only 148 `sce*` names exist. They were run. Attaching both databases and re-running
the Function ID analyzer (`tools/re/ApplyFid.java`) names **zero** additional functions. 148 is all the SDK
signatures match.
:::

## How close is the toolchain to authoring new content?

Closer than the executable's 25%-named figure suggests, because the executable is not where level content
lives. The Twinsanity Editor library already has matched `Load`/`Save` pairs for **46 item types** - collision,
scenery, dynamic scenery, models, skins, blend skins, materials, textures, skydome, terrain, particles, AI
paths, and the whole script and instance layer - and `build_mod.py` can rebuild the disc around a CRASH.BD of
any size. What has been missing is confidence that a level survives a round trip.

`tools/roundtrip_check.py` answers that for every file in the archive, and `--explain` traces each differing
byte back to the section and the offset within the item that holds it - which turns "this level loses 42
bytes" into "field +24 of every collision surface", i.e. something fixable. Two bugs came out of it.

### The texture field

Loading `beach.rm2` and saving it gave a file of **exactly the same size** differing in **134 bytes**, all of
them at `section 11 (graphics) / subsection 0 (textures) / offset +88`, across 94 textures. `Texture.cs` reads
three fields it does not keep:

```csharp
reader.ReadInt32(); // Reserved, in game's code refers to an index of vifCodeBlock
reader.ReadInt32(); // Reserved, in game's code refers to an unknown pointer
reader.ReadBytes(2); // Reserved, unknown
```

and `Save` writes zeros in their place. Only the first is ever non-zero on the disc, which is why the damage is
134 bytes and not thousands. Preserving them took one field each.

### The collision surface overrun

The second is worse, because it is not a dropped value but a corrupted layout. `CollisionSurface.cs`:

| | |
|---|---|
| `Load` | reads a `ushort` at +24 and discards it |
| `GetSize()` | returns **114** |
| `Save` | writes `writer.Write(65535)` - an `int` literal, so **four bytes** |

So `Save` emits 116 bytes into a 114-byte slot. Every surface overruns the next by two, the whole subsection
shifts, and the file comes out the same size with scrambled tails - 18 bytes on `huba`, 452 on `labext`.

:::danger Saving a level through the editor damages its collision
This is upstream behaviour, not something this mod introduced, and it applies to anyone editing surfaces in
the GUI. The mod has never been exposed to it because `build_mod` splices single items with
`tools/rig/rm2splice.py` and never takes the library's full-file save path.
:::

### The particle name tails

The third is the same shape as the first. Particle names live in a fixed 16-byte field, and the reader stops at
the terminator:

```csharp
char namechar = reader.ReadChar();
if (namechar == '\0')
{
    reader.ReadBytes(0x0F - tempName.Length);   // skipped, and not kept
    break;
}
```

while the writer pads back out to 16 with zeros. In a fixed-size name field the bytes after the terminator are
the tail of whatever longer name was there before, and the game never reads them - but they are on the disc, so
zeroing them is a difference. In `huba` that is the ASCII `"1B"` left over at a 68-byte stride through the
particle records.

### Where it stands

| | Files round-tripping byte-for-byte |
|---|---|
| Before any fix | **1** of 135 |
| After the texture fix | **98** of 135 |
| After the collision fix | 98 of 135, and `Startup\Default.rm2` stops changing size (2127 bytes and +56 → 170 and +0) |
| After the particle fix | **135 of 135** |

The collision fix does not change the file count on its own, because it repairs *layout* damage rather than a
dropped value - the other files were already losing bytes to the particle names.

So every file in the archive now survives a load and save through the library unchanged. Three fixes, all the
same mistake in different clothes: a field read and not kept, written back as zeros. The patches live in the
repository and `build_mod` applies them to the submodule, so a fresh clone gets them and they stay easy to send
upstream to [twinsanity-editor](https://github.com/Smartkin/twinsanity-editor):

```text
tools/patches/texture-preserve-reserved.patch
tools/patches/collisionsurface-padding-size.patch
tools/patches/particledata-name-tail.patch
```

:::tip What this unlocks
Whole-file authoring. Anything the library models - collision, scenery, models, skins, materials, textures,
terrain, particles, AI paths, scripts, instances - can now be changed and written back with the confidence that
nothing else in the file moved. Splicing with `rm2splice.py` remains the safer path for a one-field change, but
it is no longer the *only* safe path.
:::

## Naming what is left

Nothing mechanical remains, so the rest is read one function at a time. `tools/re/batch.py` pulls them out of
the decompile with the two things the decompile does not put beside a body - **who calls this** and **what it
calls** - and two switches decide which ones are worth your attention:

```bash
python tools/re/batch.py --min 19 --max 60 --count 8 --by-callers --named-callers
```

- `--by-callers` puts the most-called first. Naming a function used at two hundred call sites improves two
  hundred call sites; naming a leaf improves one.
- `--named-callers` keeps only functions with at least one already-named caller. Measured over a dozen
  batches, that roughly triples the hit rate: about 18% of leaf functions can be named confidently from their
  body alone, against 40-50% when the caller says what the thing is for.

It compounds. Every name makes its callees eligible, so the frontier refills as you work it - 210 to 289
in a single pass. Names learned since the last decompile count too, so you do not have to spend forty minutes
regenerating it to keep moving.

:::tip Write down what you refuse
`tools/re/db/declined.txt` records the functions that were read and deliberately *not* named, one reason each:
a two-level lookup through a global nobody has identified, a generic `return field == 0`, a destructor for a
class with no name. It keeps them out of the next batch without pretending they are understood, and stops the
next person re-reading them hoping for better luck. A blank is a fact; a guess is a liability, especially in a
database other people are building on.
:::

## How a name gets worked out

`tools/re/ghidra.py query` answers three things against the database:

```bash
python tools/re/ghidra.py query xref:0x2EABE4 callers:0x2CFCB0 decomp:0x22A020
```

`xref:` is the one that pays off most often, because it turns "what is this address" into "who touches it".
Finding that the game's memory starts at `_end` rather than where `InitHeap` was told took exactly one query:
four references to a `.data` word, all four inside a function Ghidra had already named `sbrk`.

## The game state lives in six bits

`G_GameController + 0x8` is a 64-bit word packed with several fields. Bits 40-45 - mask `0x3f00000000000` -
hold a **6-bit game state enum**, and it is read all over the executable: thirteen sites compare against it
directly, and the values seen so far are 8, 9, 0xa, 0xc, 0xe, 0xf, 0x10 and 0x12. State 0xc is the most
compared-against.

This is worth knowing before reading anything in the `0x17xxxx` range, because a comparison written as

```c
if ((*(ulong *)&G_GameController->field2_0x8 & 0x3f00000000000) == 0xc00000000000)
```

is just `state == 0xc`, and decompiled code full of 13-digit hex constants is far more forbidding than what it
actually says. Bits 50-55 of the same word are a separate *request* field: `RequestGameOver` writes 0x48 there
while leaving the state alone, so transitions are asked for on one frame and applied on another.

Two of the values are pinned. `RequestGameOver` refuses to do anything when the state already reads **0x12**,
which makes 0x12 the game-over state or something indistinguishable from it. The rest are still unknown, and
the cheapest way to fill them in would be a rig run that samples the field once a frame and prints it against
what is happening on screen, rather than any amount of further reading.

## Asking the running game instead of reading it

Some questions cannot be answered by reading. "Which of these 49 call sites actually runs" is one: they are all
reachable, and *reachable* and *reached* are different questions. The code cave makes the other kind of answer
cheap, and two tools now share the same shape - `trace_activate.py` and `trace_focus.py`
in `tools/re/`.

The pattern is: put a small driver in the cave, overwrite one instruction at the site with a jump to it, let the
driver record what it wants into cave memory, then execute the instruction it replaced and jump back. No
handshake and no trigger word, so it runs at full speed. `disarm` puts the original instruction back.

Four things decide whether it works, and three of them have bitten us:

- **The instruction after the hook runs first**, as the jump's delay slot. So the driver must re-execute the
  instruction it *replaced* and resume two instructions later, never one.
- **Hook where the arguments are still live.** `ActivateObjectInstance` consumes `$a0` at its fourth
  instruction, so the read has to happen before then. Where a function has a stack prologue, hooking its second
  instruction is usually right; where it is a leaf with no prologue there is no prologue to wait for, but the
  delay-slot instruction may still be load-bearing - both focus functions set `$v0` there and compare it two
  instructions later, so `$v0` is untouchable.
- **Only caller-saved registers are free**, and which ones hold what differs per site. The two focus hooks take
  the agent in different registers, which is why that tool has two entry stubs feeding one body.
- **Resolve addresses against every function, not every *named* function.** `symbols.tsv` holds only the
  quarter that have names, so the nearest preceding name can be thousands of bytes back and in a different
  function. A return address of `0x113fdc` reported as `Command_PlayMovie_Read+0x1594` sent someone reading
  movie code; it is really `FUN_00113a18+0x5c4`, in the focus resolver. A wrong name is worse than a raw
  address, because a raw address invites a lookup and a wrong name does not. `db/funcs.tsv` lists all 7,627
  starts so the answer is exact, and `tools/re/addrname.py` is the one place that does the lookup.
- **The record that carries the verdict must not be the record that can overflow.** A ring buffer wraps. Put
  the actual answer in something that cannot - a bitmap with one bit per id, or a set of counters - and let the
  ring carry detail only.

### A save state wipes the hooks

The driver lives in RAM, so loading a save state restores the whole cave over it - driver, counters and all -
and puts the original instructions back at every hook site. Everything then reads zero and the run reports
"neither hook fired", which is a real answer to a different question. Fresh *warps* are fine, because those
load a level in place.

Arm after the last state load, never before. `trace_focus.py dump` checks that the driver and both jumps are
still present and says so loudly if they are not, because this failure is silent and looks exactly like a
finding.

### Run the control first

A tracer that reports "never fired" and a tracer that is not working produce identical output, and no amount of
care in the driver distinguishes them. The only thing that does is a run where the answer is known in advance.

This is not hypothetical. The activation tracer's headline result - that object 877 *is* activated, overturning
a premise most of that investigation rested on - is only trustworthy because a beach level was traced first,
where 877 and 876 must both be absent: 429 activations, 69 distinct ids, both bits clear. That single run rules
out a clobbered base, stale memory and a bit carried over from an earlier session, all at once.

Run it **before** the interesting level, not after. The temptation to skip it is strongest once there is already
a result worth having, which is exactly when instinct is least worth trusting - and a wrong answer that
overturns a settled belief is the hardest kind to catch, because surprise reads as signal.

### -1 is a value, not a failure

`objId_` at `InstanceNode_type1 + 0x7c` reads `0xffff` for plenty of live agents, and that is the engine's own
"undefined" marker: `SetUndefinedID_` writes `-1` there and code all over checks `objId_ == -1` before using
it. A tracer reporting `0xffff` has not failed to read anything.

This cuts both ways, which is why it is worth stating. A sentinel that looks like a bad read invites you to
discard a real finding; a bad read that looks like a sentinel invites you to keep a fake one. The way out is
a second, independent route to the same fact - `agent + 0x84` is `objInstCxt`, and `objInstCxt + 0x6` is the
same `objectId` that `ActivateObjectInstance` takes. That path is used by engine code rather than derived from
a struct listing, so logging both and comparing them settles which of the two you are looking at.
