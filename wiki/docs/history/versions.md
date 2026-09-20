---
id: versions
title: Versions and regional differences
sidebar_position: 3
---

# Versions and regional differences

Twinsanity shipped six times, plus a Russian localisation, and the versions are not cosmetic variants of each other.
They differ in resolution, in frame timing, in which bugs are present, in checkpoint placement, in enemy population,
and in at least one case in level geometry. The community has catalogued this in unusual detail.

This mod targets **PAL PS2 (SLES-52568 v1.01)**, so this page is partly context and partly a list of things you
already have - and a couple of things you do not.

## The six retail masters

| Version | Mastered | Released |
|---|---|---|
| NTSC PS2 1.0 | 5 Aug 2004 | 28 Sep 2004, North America |
| NTSC Xbox | 13 Aug 2004 | Sep 2004, North America |
| NTSC PS2 2.0 | 20 Aug 2004 | 12 Jun 2007, in the *Crash Bandicoot Action Pack* |
| PAL Xbox | 28 Aug 2004 | Oct 2004, Europe |
| **PAL PS2** | **3 Sep 2004** | **8 Oct 2004, Europe** |
| NTSC-J PS2 | 3 Sep 2004 | 9 Dec 2004, Japan |

![Family tree: NTSC PS2 1.0 and NTSC Xbox come first, the PAL builds add the crash fixes, and those fixes are then back-ported into NTSC PS2 2.0 and the Japanese release](/img/version-tree.svg)

A Russian release also exists: NTSC-U 1.0 with a localised font and text. The PAL Platinum re-release is identical to
the original PAL version.

## PAL PS2 is the best-behaved build

The PAL disc is, by a clear margin, the most fixed version - which is a large part of why it is worth modding.

**Fixed or improved in PAL:**

- The **Dingodile crash** is gone. On NTSC-U the game could crash after the Dingodile fight, specifically when his
  model travelled too far after being beaten.
- **Less gameplay lag** overall.
- **No slide deviation bug** - see below.
- Body-slamming onto higher surfaces snaps less.
- A **stunned Coco no longer damages Crash**.
- Resetting Nina's wall-jumping tutorial is fixed.
- A save-cancelling confirmation was added.
- Lives are deducted and shown immediately when the death animation starts, rather than after the fade.

**Regressions and oddities in PAL:**

- The **menus are very slow**.
- **Evil Crash has pathing problems in Bandicoot Pursuit**, running in circles in some places.
- Walking near the fence at Farmer Ernest's farm **detaches Cortex from Crash**.
- The room before the last classroom has no enemies.
- The **Spyro trailer is missing from the disc entirely**. It is the only version of which that is true: the Japanese
  disc still carries the file, it just cannot be reached from any menu.
- The font is smaller, because it has to carry five languages' worth of letters in one texture.

The 100% completion reward also differs by region: NTSC-U gets the therapy session FMV, PAL and NTSC-J get a short
animation montage.

## Resolution

| Version | Output |
|---|---|
| PAL PS2 | 512 x 512 |
| NTSC-U PS2 / NTSC-J PS2 | 512 x 448 |
| Xbox, both regions | 640 x 480 |

The PAL PS2 build renders **512 x 512** - a taller framebuffer than either NTSC PS2 build, which is what you would
expect from a 50 Hz PAL target.

## The slide deviation bug, and why this mod should care

The single most notorious gameplay bug in the game: on NTSC-U and NTSC-J, **a slide or slide jump will sometimes throw
Crash in a direction he was not pointed in**. Speedrunners describe optimising movement as "more or less just praying
not to get thrown into wonky directions", and it is bad enough on Xbox 360 back-compat to make that platform
unattractive.

The community's explanation is that it is tied to the **60 Hz refresh rate**, not to the region as such: the PAL disc
does not show it because PAL runs at 50 Hz, and the same sources note that slide jumps at 60 Hz are shorter, and
possibly slower, than at 50 Hz.

This mod deliberately runs the PAL game at [480p / 60 Hz with matching frame timing](../modding/elf-patches), which
is exactly the combination that would reintroduce the bug if the community's explanation is right. So it was worth
measuring rather than assuming.

### Measured on the rig

One fixed slide jump in the Earth hub, driven frame-by-frame off the game's own frame counter at `0x309B68` so both
builds receive an identical number of updates of identical input. Each build was measured from two clean cold boots,
four trials each; every trial in a boot replayed to the same three decimals.

| | original disc, 49.99 Hz | this mod, 59.97 Hz |
|---|---:|---:|
| Slide-jump distance | **9.848** | **9.746** |
| Deviation from the run-up heading | +0.65° | +1.02° |
| Peak height | 1.841 | 1.862 |
| Airtime | 0.820 s | 0.818 s |

**Slide jumps at 60 Hz are about 1% shorter.** That is real and it reproduces exactly, so the community is right
about the direction of the effect - but a tenth of a unit on a ten-unit jump is not what runners are describing when
they talk about praying not to be thrown into wonky directions.

**The deviation did not reproduce.** About one degree at both rates, which is the jump's own fixed bias rather than
anything random, and the difference between the two is well under what a player could perceive.

That is evidence against the community's explanation, and it narrows where the cause can be. What was tested is the
**PAL build** at 60 Hz - and the PAL and NTSC builds differ in far more than their refresh rate. So if the rate alone
does not produce the deviation, the likelier home for it is something in the NTSC builds themselves, or a trigger
this test cannot reach. "It is the 60 Hz" is the one explanation these numbers make less likely.

:::note What this test cannot show
The bug is reported as *intermittent* - "sometimes". Every run here is deterministic: the same save state and the
same frame-exact input give bit-identical results, which is what makes the 1% figure trustworthy and is also exactly
why this cannot rule the deviation out. A replay that never varies cannot sample variation. What this shows is that
60 Hz alone does not *force* the deviation, not that the deviation cannot happen.

Two measurement traps worth recording for anyone repeating it. The player object's position at `+0xD0` is
ground-projected and its `y` does not move at all while Crash is airborne, so the height has to come from `+0x284`
(height above ground) or `+0x064` (vertical velocity). And Crash clips scenery around frames 32-56 of a straight run
in the hub, deflecting his heading by 17°; a run-up that ends inside that window measures the collision rather than
the jump.
:::

## NTSC-U 1.0 quirks worth knowing

Useful mostly for reading other people's videos and speedruns, which are often NTSC:

- A **big tree next to the farm** which is not in any other version, and which lets players bypass Totem Hokum easily.
- Cortex's and Mecha-Bandicoot's plasma blasts are much larger.
- Crates exist that no other version has.
- There is **no checkpoint outside the top lab's interior**, and Cortex starts far from the entrance inside it.
- An extra checkpoint next to the world checkpoint at the start of Rockslide Rumble.
- Enemies in the corridor just before the final boss, which PAL removed.
- Dying while triggering the first Boiler Room Doom cutscene locks Crash in place.

NTSC PS2 2.0, the *Action Pack* build, back-ports the PAL crash fixes onto the American version.

:::note One source claim left out
Beyond Twinsanity lists "skipping FMVs requires waiting a second" as exclusive to NTSC-U 1.0. It is not repeated
above, because this project measured the same roughly one-second delay before ✕ takes effect on the PAL disc - see
[The movie player](../engine/movies), where ✕ ends a movie in 6.8 s against 7.0 s untouched. Whatever the difference
between the versions is, "PAL skips instantly" is not it.
:::

## Japanese version

- Many menu actions and **cutscene skipping use circle instead of cross**, per Japanese convention.
- TNT and Nitro crate textures were changed, as in every Japanese Crash release.
- **Rusty Walrus's pathing is broken.**
- Sliding is as tight as PAL, but the random deviation from NTSC-U is still present.
- Characters in the galleries have **more fingers** than in other versions.

## Xbox versus PS2

- Textures are better; lighting on characters and some environments is different and generally **darker**.
- Particles are sparser and shorter-lived, and are not cleaned up immediately after a death.
- Cutscene transitions show the game's logo in the bottom-left corner.
- Some cutscenes **desync from their audio** because of in-game lag.
- Getting an extra life at 100 Wumpa plays no sound.
- The Extras menu calls the movies "FMV" rather than "Movie".
- PAL Xbox is **missing the ':' character from its font**, which affects save-file times, the sound options and the
  worm minigame timer. It also has no Spanish localisation.
- NTSC Xbox is region-free; nothing else is. The Xbox version runs on Xbox 360 with heavy slowdown. The PS2 version
  runs on early PS3s, but PAL has game-breaking issues there.

## Sources

- [Version differences - Beyond Twinsanity](https://beyondtwinsanity.com/evolution/versions)
- [Regional, console and version differences - The Crash Bandi-pedia](https://thecrashbandipedia.miraheze.org/wiki/Crash_Twinsanity_(Consoles)_Regional,_Console,_and_Version_Differences)
- [NTSC vs PAL - Crash Twinsanity forums, Speedrun.com](https://www.speedrun.com/twinsanity/forums/08eok)
- [Crash Twinsanity - Wikipedia](https://en.wikipedia.org/wiki/Crash_Twinsanity)
