---
id: scripts
title: Scripts - the language that isn't one
sidebar_position: 2
---

# Scripts: the language that isn't one

The first question everybody asks is "what language are the scripts written in?" The honest answer is **none**.

There is no Lua, no bytecode, no text on the disc. Every behaviour in Twinsanity - a door, a crate, a monkey, a boss,
a cutscene - is a **small state machine stored as data** inside the level file. The engine has one interpreter that
walks these state machines, and that interpreter is the entire scripting runtime.

The names that survive in the data (`COM_TIKI_MON_ACTIVATED`, `CRASH_CUTSCENE_H02B`) and the shape of it - states with
numbered conditions and numbered commands - point at an in-house authoring tool where these machines were laid out
visually.

That tool has a name: **AgentLab**. A developer interview names it as how gameplay behaviours were scripted, and the
retail disc still carries a `Language\AgentLab\` folder of text, while the executable references a file called
`Import\LevelAgents.axp`. It is also where this wiki's word *agent* comes from. The tool itself is not on the disc;
what shipped is its compiled output - which is what the rest of this page describes. See
[How the game got made](../history/development#agentlab-is-still-on-your-disc).

## The shape of it

```text
Script  "COM_TIKI_MON_ACTIVATED"
│
├─ state 0  ── flags ── optional sub-script
│   ├─ rule: condition(param) [interval, threshold]  ──► go to state N
│   │        └─ command, command, command …   (run on the way out)
│   └─ rule: …
├─ state 1
└─ state 13  ◄── the start state (not always 0)
```

![Anatomy of a script: a script holds numbered states; a state holds a flag word, an optional sub-script and a list of rules; a rule holds a condition with its parameter, interval and threshold, a target state, and the commands that run on the transition into that target](/img/script-anatomy.svg)

A **state** has:

- a **flag word** that says how it behaves (below),
- optionally a **sub-script**: another script that runs to completion while this state is active,
- a linked list of **rules**, called *bodies* in the file format.

A **rule** has:

- a **condition**, chosen by number, with one parameter, a re-check *interval* and a *threshold*,
- a **target state**,
- a linked list of **commands**, chosen by number, each with a fixed argument list.

When a rule's condition passes, its commands run and the machine moves to the target state. That is the whole model.

Here is a real one - the Iceberg Lab cutscene director - drawn out, and then as
[`twinsdump`](../modding/recipes) prints it:

![The Iceberg Lab cutscene director as a state machine: states 0, 1 and 2 run in sequence to the end state 4, a command hangs off the transition into 4, and state 5 holds the skip rule leading to the skip path in state 3 - but nothing reaches state 5](/img/script-state-machine.svg)

```text
=== script 6237 COM_ICELABINT_CUTSCENE_DIRECTOR_ACTIVATED
  state 0 [start] bits=0x8421 script=3487(COM_GENERIC_CUTSCENE_BEGIN)
    [0] if Next(p=0) int=0 thr=0.5 -> state 1  (bits=0x600)
  state 1 bits=0x8421 script=6239(COM_ICELABINT_CUTSCENE_H02B)
    [0] if Next(p=0) int=0 thr=0.5 -> state 2  (bits=0x600)
  state 2 bits=0x8421
    [0] if Next(p=0) int=0 thr=0.5 -> state 4  (bits=0x601)
          ToggleCutsceneCamera(3846706176, 0)
  state 3 bits=0x8421 script=6749(COM_ICELABINT_CUTSCENE_SKIP)
    [0] if Next(p=0) int=0 thr=0.5 -> state 2  (bits=0x600)
  state 4 bits=0x8000
  state 5 bits=0x0821
    [0] if Cond572(p=1) int=0 thr=0.25 -> state 3  (bits=0x600)
```

Read it as: *play the generic "a cutscene is starting" script, then play the scene, then turn the cutscene camera off
and stop.* State 3 is the skip path, and state 5 is the rule that would jump to it when the player holds Triangle -
except nothing reaches state 5, which is exactly the kind of damage this mod repairs. See [Cutscenes](cutscenes).

## State flags

The flag word decides when the rules are looked at. The two that matter in practice:

| Bit | Meaning |
|---|---|
| `0x0400` | **Instant.** The state's rules are evaluated once as it is entered and it steps straight on. |
| `0x0800` | **Polled.** The rules are re-checked every frame until one passes. |
| `0x4000` | The state keeps player control alive while it runs (`+control` in the dumps). |
| `0x8000` | Another state follows this one in the file - the last state has it clear. |
| low bits | How many rules the state has (stored twice, in two nibble-ish fields). |

So `0x8421` is an instant state and `0x8821` is a polled one, and `0xC421` is an instant state that leaves control
alone.

:::danger The trap that costs an afternoon
Adding a polled rule to an **instant** state stops the state from stepping on, and the scene hangs. When you add a
"hold Triangle" rule to a cutscene, only put it in states that already wait - polled states, `+control` states, or a
state that is running a sub-script.
:::

## Conditions

A condition is an engine function picked by number. `Next` (0) means "the state is finished" - the sub-script ended,
or there was nothing to wait for. The ones that come up constantly:

Just enough to read the dump above:

| Id | Name | Means |
|---|---|---|
| 0 | `Next` | done with this state |
| 2 | `Else` | always true; the fall-through rule |
| 572 | `CutsceneSkipped` | **stubbed to always return 0 in the retail build** - see [Cutscenes](cutscenes) |
| 575 | *Triangle held* | reads the pad's Triangle pressure for player *param* |

The *threshold* is compared against the value the condition returns, so the same condition id does different work with
different thresholds - `TimeInUnit` with `thr=0.3` is "wait 0.3 s", and a distance condition with `thr=150` is "within
150 units".

The full list of ids the engine knows is a jump table in the executable. Every id identified so far - timers,
animation waits, message conditions, boss counters, distances - is tabulated in
[Reference → script ids](../reference/script-ids), which is the page to keep open while reading a dump.

## Commands

Commands are the verbs: `DoAnim`, `PosWarp`, `SetFocusToPlayer`, `SendUserMessage`, `PlayMovie`, `SetAgent`,
`BottomTextDisplay`. Each has a fixed argument list, and the arguments are raw 32-bit words - `twinsdump` prints them
as integers or floats depending on what they look like, which is why you see things like `PosWarp(40.75f, 0, 0, 2f, 1f)`
next to `MessageLinkedObject(67043625, 14681116, 0, 0)`. Several of those "big integers" are packed fields; the message
commands, for instance, pack a target and a message number into one word - see [Cutscenes](cutscenes).

Commands live on a **rule**, not on a state, so they run *on the transition*. That matters when you edit: to make
something happen when a state is entered, attach the commands to the rule that leads into it.

## Who runs a script

A script does not run on its own. It runs **on an object instance**, and the commands act on that instance: `DoAnim`
animates it, `PosWarp` moves it, `SetAgent` changes its flags. An object type has numbered **script slots**, and the
engine switches between them:

```text
object 1034 |LabInt|H02B_Cutscene|act_ICELABINT_CUTSCENE_DIRECTOR
   scripts: 0:6234(ICELABINT_CUTSCENE_DIRECTOR_DEFAULT)
            11:6242(CORTEX_CUTSCENE_H02B)  12:6244(CRASH_CUTSCENE_H02B)
            13:6246(UKA_UKA_CUTSCENE_H02B) 14:6250(AKU_AKU_CUTSCENE_H02B)
```

Slot 0 is what the object does normally. Most objects come in a `_DEFAULT` / `_ACTIVATED` pair, and a trigger volume
or another script's `TriggerLinkedObjects` command switches the object from one to the other. The higher slots here
hold the scripts the director hands to its actors while a scene plays.

:::tip Finding an actor's script
Actor scripts hang off the director object's slots, so searching the script list by name can miss them. Ask for the
object instead: `twinsdump level.rm2 objects DIRECTOR_NAME` prints its slots.
:::

## Messages

Objects talk to each other with **user messages**: a number, sent to a target. `SendUserMessage`, `MessageLinkedObject`
and `BroadcastUserMessage` all pack the target and the number into one argument word, and the receiver waits on
`GotUserMessageEquals(p=N)` and then calls `ClearUserMessage`. A message stays pending until it is cleared, which is
useful - but a character switch tears down the other character's script, so a message sent in the same frame as a
switch is simply lost.

The two numbers this mod uses constantly: **207** ("carry on") and **244** ("the scene was skipped").

## Reading and editing

- `twinsdump <level>.rm2 scripts` dumps every script the way it is quoted above.
- `twinsdump <level>.rm2 objects [regex]`, `instances`, `triggers`, `refs`, `msg` answer the "who does what" questions.
- `twinsdump <level>.rm2 edit ops.txt outdir` applies a text recipe - add a rule, copy a rule, retarget one, change an
  argument, delete a command.

Recipes are how every level change in this mod is stored. [Level recipes](../modding/recipes) is the cookbook.
