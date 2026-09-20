---
id: speedrunning
title: Speedrunning and glitches
sidebar_position: 4
---

# Speedrunning and glitches

Speedrunners have been the most thorough testers this game ever had. Two decades of people trying to break it have
produced a map of the engine's weak points that is worth reading even if you never intend to run it - several of the
bugs this mod fixes were first described properly by runners.

There is also a direct link between the two communities: **Smartkin**, author of the
[Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) that this project depends on to read level files,
is a leaderboard moderator with runs in both main categories.

## The leaderboard

As of September 2026, on [speedrun.com/twinsanity](https://www.speedrun.com/twinsanity) - 575 runs from 89 players:

| Category | Record | Holder |
|---|---|---|
| Any% | **9m 30s** | Gpro (Xbox, HDD) |
| Any% (No Dimension Skip) | **24m 17s** | Gpro (HDD) |
| 100% | **1h 02m 32s** | Gpro (Xbox, HDD) |

The gap between the two Any% categories is the measure of a single trick. Roughly **fifteen minutes of the game
disappear** into one glitch, which is why the leaderboard splits on it.

## Dimension Skip

The big one. It takes you **from Iceberg Lab straight to the 10th dimension lab, skipping six levels**.

![Diagram: an arc leaps from Iceberg Lab over six levels straight to the 10th dimension lab, with the two speedrun categories compared as bars, 24:17 without the skip against 9:30 with it](/img/dimension-skip.svg)

The mechanism is a cutscene flag. Entering the 10th dimension normally sets a flag via the "hug" cutscene, and that
cutscene is what stops you ending up underground. Reach the 10th dimension by an unintended route and the game never
checks whether the flag should be set - so the trick is to set the flag early, out of bounds, and then walk in through
a load wall.

Doing that without cheats needs Cortex as a physical prop: carry him along, clip him through the floor into position
above a corridor, then walk into him while a cutscene trigger fires, which sets the flag.

Gpro found it in **August 2018** using the levitation cheat; **Joester98** performed it cheat-free in **September
2018** after community work on the route.

:::note Why this is interesting from the modding side
It is a missing precondition check, not a physics exploit. The scene that establishes the state is treated as
guaranteed to have run. That is the same class of assumption behind several of this mod's fixes: a
[cutscene](../engine/cutscenes) that quietly relies on the player arriving in exactly one state, and misbehaves when
they do not.
:::

## The other major skips

**Mecha-Bandicoot Skip** - long-jump around an invisible wall, climb a set of vertical stairs, and hit the underside
of the hoverboard, bypassing the first boss. Performed slightly wrong it softlocks instead.

**Hover Skip** - builds on the above and skips the whole of N. Sanity Island, requiring careful hovering through the
level's upper areas while avoiding a crash zone on the middle path.

**Iceberg Lab Skip** - get out of bounds at the entrance to Ice Climb, then slide-jump along the solid parts of the
mountain and follow thin ledges to reach N. Gin's boat directly.

**Take Cortex Everywhere** - manipulate Cortex's attachment during specific scenes and he can be dragged through the
rest of the game. He is a solid, movable object with his own scripts, so having him somewhere he was never meant to be
is the foundation for a lot of other tricks, Dimension Skip included.

## Movement tech

Routing is built almost entirely on two things:

- The **rigid slide jump**, which covers more ground than intended.
- The **long jump glitch**.

Both are faster than walking, which is why runs look like a continuous chain of slides rather than a platformer.

Note the frame rate interaction documented on the [versions page](versions): at 60 Hz, slide jumps are **shorter and
possibly slower** than at 50 Hz, and on NTSC builds a slide can throw Crash in a random direction entirely. The PAL
builds, running at 50 Hz, therefore have the longest and most reliable slide jumps.

## Bugs that are not skips

- **Cannon rapid fire** - a low body slam on the edge of a cannon's button makes it fire bombs excessively, sometimes
  hurting you.
- **Slide deviation** - NTSC only; covered on the [versions page](versions).
- **Rusty Walrus pathing** - broken on the Japanese version.
- **Evil Crash circling** - PAL and NTSC-J, in Bandicoot Pursuit.
- **Hardlocks** - several of the out-of-bounds setups lock the console completely when the conditions are not met
  exactly.

## What this mod does to a run

This is not a speedrun-legal build and is not trying to be - the leaderboards run retail discs. But two of its changes
are the kind of thing runners would notice:

- **Restored cutscene skipping** removes a large amount of forced waiting that runs currently sit through or skip with
  glitches.
- **Faster loading** and **60 Hz output** change the timing of everything, including the slide-jump behaviour above.

If you are comparing this mod's behaviour against a video, check which version the video is: an NTSC run will have
different checkpoints, different plasma sizes, a tree next to the farm, and enemies in a corridor that your PAL disc
leaves empty.

## Sources

- [Crash Twinsanity - Speedrun.com](https://www.speedrun.com/twinsanity)
- [Dimension Skip - Twinsanity speedrunning wiki](https://twins.miraheze.org/wiki/Dimension_Skip)
- [Crash Twinsanity (Consoles) Glitches - The Crash Bandi-pedia](https://thecrashbandipedia.miraheze.org/wiki/Crash_Twinsanity_(Consoles)_Glitches)
- [Crash Twinsanity exploits - Crash Mania](https://www.crashmania.net/en/games/crash-twinsanity/cheats/exploits/)
