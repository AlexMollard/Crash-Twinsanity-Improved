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
| `setcond SCRIPT STATE BODYIDX COND PARAM [INTERVAL [THRESHOLD]]` | Rewrite a rule's condition, keeping its commands and target (size-neutral) |
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

`settarget`, `setcond` and `setarg` are size-neutral, which makes them the tools of choice for experiments: the
existing save states stay valid, so a test is two minutes instead of twenty. `setcond` in particular can force a
script down a path the rig cannot otherwise reach - swap a "wait for message 269" for a "wait three seconds" and the
rest of the machine runs unchanged.

## What is left to restore

`python tools/skip_survey.py` answers that, and it reads the **built** mod rather than the original disc, so a
skip a recipe has already restored comes back LIVE and only the genuinely unreachable ones are listed. It
refuses to report at all unless a known-restored skip reads LIVE - pointed at the original disc by mistake,
every restored skip looks orphaned again and the output reads like a pile of new work.

It also reports skips that are reachable but have **no `HOLD △ TO SKIP` prompt**, because restoring a skip
and prompting for it are two separate recipes and `mod/skip_prompt.ops` names its levels by hand. That is not
theoretical: covering `roofcor2` in `rooftop.ops` gave that scene a working skip with no prompt on screen,
and the player would never have found out.

Two cautions are built into how it reports. A condition-572 rule in an ordinary behaviour script is an
alternative transition, not a cutscene, so only states that actually play one are counted - the same rule
`skipprompt auto` uses. And results are grouped by **script**, not by level: a script sitting in dozens of
level files is global boilerplate linked everywhere rather than dozens of missing prompts.
`COM_CORTEX_DOCAMOK_EARTH_PHASE2` is in 38 files and its scene only plays in the Doc Amok levels, which are
prompted already - they are precisely the three that do *not* appear in its list. Presence in a level file
says nothing about whether the thing runs there.

## Does a recipe reach every copy of what it edits?

Script ids are game-wide and the same script sits in as many `.rm2` files as need it, but a recipe only edits
the files its `file` lines name. Miss one and the fix silently does not apply there - which is exactly how the
Rooftop skip came to be missing from `roofcor2`, the Nina route through that level.

`python tools/recipe_reach.py` checks every recipe against every level that holds the scripts it edits. It
also asserts that at least one edited script really does live in more than one level, because otherwise "no
gaps" would only mean the lookup found nothing. Current answer: 17 recipes, 42 scripts, **no gaps** - the
Rooftop one was the only case and it is fixed.

## Test-only recipes

Some things cannot be reached in the rig without help. `tools/rig/testops/tiki_defeat.ops` sends the Totem Hokum boss
straight to his defeat cutscene when the fight starts, so the beaten-boss state can be tested without fighting him:

```text
file Levels\Earth\Hub\hubd.rm2
settarget 4015 13 0 5
```

Those are built only with `--include tools/rig/testops`, and never ship.
