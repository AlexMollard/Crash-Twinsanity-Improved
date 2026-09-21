---
id: what-changed
title: What the mod changes
sidebar_position: 5
---

# What the mod changes

Every change in the mod, what it does and the measurement that proved it. This is the detail that used to live in the
repository's README; the README now links here instead, so the project's front page does not open with a list of every
cutscene in the game.

:::warning Spoilers
This page names scenes, bosses and late-game locations. If you have not played Twinsanity, the
[README](https://github.com/AlexMollard/Crash-Twinsanity-Improved) has the feature list without them.
:::

## Cutscene skip status

Hold **△** during a cutscene to skip it, and every skippable scene shows *HOLD △ TO SKIP* in the bottom letterbox bar.

![Crash on N. Sanity Beach with HOLD TRIANGLE TO SKIP drawn in the letterbox bar](/img/shots/skip-prompt-beach.png)

Each level edit below is tested on the [rig](rig): the scene is played in full, then skipped from the same save state,
and the rig checks that gameplay comes back sooner and that the player ends in the same situation. Why this needed
fixing at all is on [Cutscenes](../engine/cutscenes); the executable side is on
[Executable patches](elf-patches).

| Status | Cutscene | Full → skipped¹ | What the skip also does |
|:-:|---|:-:|---|
| ✅ | Wired-in skips: Aku Aku training, Totem Hokum, Dingodile, Uka Uka, Henchmania, … | — | Executable patch only |
| ✅ | Beach: Aku Aku crate (mask) | — | Hides the crate's Aku Aku |
| ✅ | Beach training | 6.1 s → 4.6 s | |
| ✅ | Angry skunk | 11.4 s → 4.6 s | |
| ✅ | Rooftop Rampage | 13.2 s → 4.4 s | Both level files: the director is in `roof01` and `roofcor2`, and the second was missed |
| ✅ | Rooftop Rampage, second copy | 6.3 s → 4.0 s | Found by `tools/skip_survey.py` - it was the one skip still unreachable in the built mod |
| ✅ | Academy hub | 16.1 s → 4.5 s | |
| ✅ | Treasure room | 22.9 s → 4.4 s | |
| ✅ | Slip Slide Icecapades | 30.7 s → 4.8 s | Crash and Cortex go to their end marks |
| ✅ | Iceberg Lab | 34.5 s → 4.5 s | |
| ✅ | Classroom Chaos | 10.8 s → 4.2 s | Switches you to Cortex, as the scene does |
| ✅ | Core intro | 21.0 s → 4.1 s | Cortex and Nina leave, as they do in the full scene |
| ✅ | Bell tower (Madame Amberly) | 21.4 s → 4.0 s | Cortex gets control and the fight starts, as in the full scene |
| ✅ | Psychetron room, Coco | 50.0 s → 9.7 s | Crash, Cortex and Coco all go to their end marks |
| ✅ | Psychetron room, Cortex and Nina | 22.9 s → 9.8 s | Still plays the FMV and the scene that follow (both times include the FMV) |
| ✅ | Dorm room | 28.4 s → 4.0 s | Switches you to Nina, as the scene does |
| ✅ | Walrus chase | 10.8 s → 4.1 s | Starts the chase music. The developers' unfinished skip warped the walrus onto Crash, killing him as control returned; it now stays behind him as in the full scene |
| ✅ | Rockslide Rumble | 25.3 s → 4.0 s | Crash and Cortex go to the top of the slide, the music starts and Crash mounts the Humiliskate |
| ⛔ | Totem falling | — | **Left unskippable.** Skipping drops Crash into the totem chase before it is set up, and he dies. |
| 🚧 | Party arena | — | Work in progress (`mod/levels-wip`): the scene is switched on by beating the Mechabandicoot, which the rig cannot do yet |

<sub>¹ Time from the start of the scene until the player has control again. The skipped times include about 2.5 s of the
rig's own wait and button hold.</sub>

:::note Cutscenes that are movies
Some of what the game calls a cutscene is a pre-rendered movie rather than an in-engine scene - the Iceberg Lab
interior plays 53 seconds of `H02_B.PSS` every time you walk in. Those are not in the table: they already stopped for
✕ in the retail game, and now answer △ as well. See [The movie player](../engine/movies).
:::

:::note Known differences after a skip
A few level hints do not appear: "Clear a path for Cortex!", "Use ◯ to crouch", "Tap □ to rapid fire". In Iceberg Lab
and Classroom Chaos the character stands a few steps from where the full scene would leave them.
:::

## Aku Aku invincibility

Collecting a third mask sets Crash's invincible flag for eight seconds, but the damage handler lets any hit of 50 or
more through - and every explosion (TNT, Nitro, bombs) deals 100. So an invincible Crash still died to TNT.

The patch in `mod/elf_patches.txt` makes invincibility also block damage flagged as an explosion. Other instant deaths
still go through. The same flag covers the two-second grace period after a hit, so explosions no longer kill you
during it either.

Rig-tested: TNT while invincible leaves Crash at full health; without invincibility it still kills. Enemy hits are
unchanged. The addresses are on [Addresses](../reference/addresses) - `0x137510` is the damage handler, whose info
struct carries the flags at `+0x10`, and `0x13F9A0` is the third-mask pickup.

## Invisible Crash after a cutscene

After a hit, Crash flickers for two seconds: the grace-period code hides him for the last fifth of every 0.2 s while
he cannot be hurt again.

When a cutscene takes control of the player - and again when it hands control back - the game resets that state
machine without ending it, so whatever the flicker last set sticks. One time in five that is "hidden": Crash is
missing from the whole cutscene, and stays invisible in gameplay afterwards until something else shows him.

The reset now goes through a stub that ends a running grace period properly, making the character visible again and
clearing the grace invincibility.

Rig-tested with a worm hit followed by the Aku Aku crate tutorial: without the fix Crash is gone from the scene and
from gameplay after it; with it he is visible in both, and a normal hit still flickers for exactly two seconds.

:::tip The same family of bug
This is the same shape as the [Dimension Skip](../history/speedrunning) speedrunners use: a cutscene assumes the
player arrives in a known state, and misbehaves when they do not.
:::

## The rest, in their own pages

The other shipped changes are documented where the machinery is explained:

| Change | Page |
|---|---|
| Shadows on crates | [Graphics](../engine/graphics) |
| A beaten boss stays beaten (Tiki Mon contact damage) | [Objects, instances and agents](../engine/objects) |
| Faster loading, and the 60 Hz frame budget | [Loading and streaming](../engine/loading) |
| Movies at their real speed, and movies answering △ | [The movie player](../engine/movies) |
| How the skip prompt is drawn | [How a cutscene is made](../engine/cutscenes) |
| How the ISO is built and verified | [Building the ISO](build) |
