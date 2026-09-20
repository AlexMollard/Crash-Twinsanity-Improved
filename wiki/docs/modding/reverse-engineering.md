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
| `0x2EC530` | 663 | command id | `0x1016F0`, entered with `a2 == -10` |
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

## What is named, and what is not

| | Functions |
|---|---|
| Named | 1,704 |
| Still `FUN_xxxxxxxx` | ~5,200 |
| Total | 6,902 |

It was 962 before any of this. Of the unnamed remainder, roughly 275 are trivial (eight lines or fewer), 4,100
are small or mid-sized helpers, and 1,900 are substantial.

Two shortcuts that people usually reach for do not work on this binary, so they are worth not trying twice.

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

## How a name gets worked out

`tools/re/ghidra.py query` answers three things against the database:

```bash
python tools/re/ghidra.py query xref:0x2EABE4 callers:0x2CFCB0 decomp:0x22A020
```

`xref:` is the one that pays off most often, because it turns "what is this address" into "who touches it".
Finding that the game's memory starts at `_end` rather than where `InitHeap` was told took exactly one query:
four references to a `.data` word, all four inside a function Ghidra had already named `sbrk`.
