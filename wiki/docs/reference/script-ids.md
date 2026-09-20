---
id: script-ids
title: Script ids
sidebar_position: 1
---

# Script ids

Conditions and commands are engine functions picked by number. These are the ones that have been identified while
working on this mod - a small slice of what the engine knows, but the slice that comes up.

## Conditions

| Id | Name | Notes |
|:-:|---|---|
| 0 | `Next` | The state is finished: its sub-script ended, or there was nothing to wait for |
| 2 | `Else` | Always true - the fall-through rule |
| 5 | `TimeInUnit` | Threshold is seconds spent in this state |
| 7 | `AnimationFinished` | |
| 51 | `GotUserMessageEquals` | Parameter is the message number; pair with `ClearUserMessage` |
| 91, 92 | boss hit counters | Used by boss scripts with a threshold |
| 122 | dialogue busy | |
| 155 | distance-ish | Threshold is a distance |
| 176 | | Used by doors |
| 571 | (identical "return 0" stub) | Re-pointed by the mod to free `0x12C578` |
| **572** | `CutsceneSkipped` | **Stubbed to return 0.0 in retail.** The mod makes it "player *param* holds Triangle" |
| 575 | Triangle held | Reads the pad's Triangle pressure for player *param* |
| 596 | | Vehicle tricks |
| 639 | story progress | |
| 641 | movie playing | Scripts wait on `NOT Cond641` after `PlayMovie` |

Parameters and thresholds matter as much as the id: the same condition is "wait 0.3 seconds" or "wait 3 seconds"
depending on the threshold, and message conditions take the message number as the parameter.

## Commands

Named by the editor library where it knows them, `CmdN` where it does not.

| Id | Name | Notes |
|:-:|---|---|
| 515 | `SetAgent` | Packed mask/value - see [Objects](../engine/objects) |
| | `DoAnim`, `DoSound`, `DoParticle` | |
| | `PosWarp`, `PosWarp2`, `RotWarp` | Placement; only meaningful while the owning scene runs |
| | `SetFocusToPlayer`, `SetFocusToKey`, `RequestFocus`, `ClearFocus` | "Focus" is the thing the script is acting on |
| | `SendUserMessage`, `MessageLinkedObject`, `BroadcastUserMessage`, `ClearUserMessage` | Target and message packed into one word |
| | `TriggerLinkedObjects` | Switches linked objects to their `_ACTIVATED` script |
| | `PlayMovie(id, x)` | Starts a pre-rendered movie |
| | `ToggleCutsceneCamera`, `CutsceneStart`, `CutsceneEnd`, `FadeoutScreen` | |
| | `BottomTextDisplay(index, x, y, r, g, b, 0)`, `BottomTextClear`, `BottomTextShow`, `BottomTextHide` | Command ids 603, 608, 619, 620 |
| | `BossModeEnable`, `BossModeDamage`, `BossModeExit` | The boss health bar |
| | `SetPlayerInput`, `SetPlayerMode`, `SwitchCharacter`, `UnlinkCharacters` | |
| | `DestroyMe` | Removes the instance |
| | `SetCollisions`, `SetState`, `SetObject`, `SetCounter`, `ModifyCounter` | |

## User messages

| Number | Meaning |
|:-:|---|
| 207 | "carry on" - the scene's step is done |
| 243, 244 | 244 is "the scene was skipped"; actors answer it by going to their end marks |
| 87, 88, 105, 106, 156, 188 | Level and boss plumbing |

Messages are packed with their target into a single argument word - for example `0x03FB00CF` is message 207 and
`0x03FB00F4` is 244 to the same target. The quickest way to get the packing right is to copy an existing command and
`setarg` the number.

## Where the tables live

The command factory jump table is at `0x2EC530`, indexed by command id; each entry allocates the command object and
points it at a vtable whose slots are "read arguments", "execute" and so on. Conditions are built by
`BuildScriptCondition` at `0x106C40`, and the condition check functions live in a table around `0x2F0AB8`.

All three, and every other address this wiki quotes, are collected on [Addresses](addresses).
