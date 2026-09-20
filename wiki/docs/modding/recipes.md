---
id: recipes
title: Level recipes
sidebar_position: 2
---

# Level recipes

A recipe is a text file of edits applied to a level's scripts by `twinsdump edit`. They live in `mod/levels/*.ops`
(built into the ISO), `mod/levels-wip/*.ops` (written but not yet proven) and `tools/rig/testops/*.ops` (test-only
scaffolding, never shipped).

A recipe starts with a `file` line and then lists operations:

```text
# Iceberg Lab exterior (L04A); skip runs COM_ICELAB_CUTSCENE_SKIP
file Levels\Ice\Hub\labext.rm2
copybody 5495 1 9 0 4 572 1 0   # state 1 plays the scene: add the developers' Triangle rule -> state 4
clearbodies 5495 9              # drop the unreachable original in state 9
```

One recipe may cover several levels: each `file` line starts a new section.

## Reading a level first

```bash
twinsdump level.rm2 scripts            # every script, state by state
twinsdump level.rm2 scripts NAME       # filtered by name
twinsdump level.rm2 objects [regex]    # object types and their script slots
twinsdump level.rm2 instances [-v]     # placements, with positions
twinsdump level.rm2 triggers           # trigger boxes and what they point at
twinsdump level.rm2 refs 1234          # what refers to a script
twinsdump level.rm2 msg 244            # who sends and who handles a user message
```

## The operations

| Op | What it does |
|---|---|
| `addbody SCRIPT STATE COND PARAM TARGET [INTERVAL [THRESHOLD]]` | Add a rule with no commands |
| `copybody SCRIPT TOSTATE FROMSTATE BODYIDX TARGET COND PARAM INTERVAL [THRESHOLD]` | Copy a rule's commands into another state, with a new condition and target |
| `clearbodies SCRIPT STATE` | Remove every rule from a state |
| `appendcmds SCRIPT STATE BODYIDX FROMSCRIPT FROMSTATE FROMBODYIDX` | Append a copy of another rule's commands |
| `delcmd SCRIPT STATE BODYIDX CMDIDX` | Remove one command |
| `movebody SCRIPT FROMSTATE BODYIDX TOSTATE` | Move a rule between states |
| `settarget SCRIPT STATE BODYIDX TARGET` | Re-point a rule (size-neutral) |
| `setarg SCRIPT STATE BODYIDX CMDIDX ARGIDX VALUE` | Change one command argument |
| `skipprompt auto` or `skipprompt SCRIPT STATE[,STATE] [TEXT]` | Add the "hold △ to skip" hint to states that can be skipped |

`addbody` and `copybody` set the state's poll flag, because a rule that is only checked once is no use for "is the
player holding a button". That is also why they must not be used on an instant state - see
[Scripts](../engine/scripts).

## Adding a command out of thin air

There is no "add command" op, because every command has its own argument layout. Instead, copy a rule that already
has the command you want and trim it:

```text
appendcmds 4015 8 0 1511 7 0   # COM_EARTH_WORM_START state 7 body 0 is a lone SetAgent(64)
```

If the source rule has extra commands, `delcmd` them afterwards and `setarg` the survivor into shape. Finding a clean
source is usually a grep away - `SetAgent(64)` on its own appears in hundreds of places.

## Size changes and the state library

Most ops change the size of the level file. That invalidates the rig's save states, because a state contains the
archive's file table - so after a recipe change, rebuild them:

```bash
python tools/rig/rebuild.py            # ~18 minutes: builds test.iso and all 34 states
```

`settarget` and `setarg` are size-neutral, which makes them useful for quick experiments: the existing states stay
valid, so a test is two minutes instead of twenty.

## Test-only recipes

Some things cannot be reached in the rig without help. `tools/rig/testops/tiki_defeat.ops` sends the Totem Hokum boss
straight to his defeat cutscene when the fight starts, so the beaten-boss state can be tested without fighting him:

```text
file Levels\Earth\Hub\hubd.rm2
settarget 4015 13 0 5
```

Those are built only with `--include tools/rig/testops`, and never ship.
