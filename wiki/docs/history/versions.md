---
id: versions
title: Versions and regional differences
sidebar_position: 3
---

# Versions and regional differences

Twinsanity shipped six times, and the versions are not cosmetic variants of each other. They differ in resolution, in
frame timing, in which bugs are present, in checkpoint placement, in enemy population, and in at least one case in
level geometry. The community has catalogued this in unusual detail.

This mod targets **PAL PS2 (SLES-52568 v1.01)**, so this page is partly context and partly a list of things you
already have - and a couple of things you do not.

## The six retail masters

| Version | Mastered | Released |
|---|---|---|
| NTSC PS2 1.0 | 5 Aug 2004 | 28 Sep 2004, North America |
| NTSC Xbox | 13 Aug 2004 | Sep 2004, North America |
| NTSC PS2 2.0 | 20 Aug 2004 | later; the *Crash Bandicoot Action Pack* build, 12 Jun 2007 |
| PAL Xbox | 28 Aug 2004 | Oct 2004, Europe |
| **PAL PS2** | **3 Sep 2004** | **8 Oct 2004, Europe** |
| NTSC-J PS2 | 3 Sep 2004 | 9 Dec 2004, Japan |

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
- The **Spyro trailer is missing from the disc entirely** - it is present but unreachable on the Japanese disc, and
  reachable nowhere.
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

:::caution Worth testing on this mod
This mod deliberately runs the PAL game at [480p / 60 Hz with matching frame timing](../modding/elf-patches). If the
deviation really is a function of the 60 Hz update rather than the region, that combination is exactly the one that
could reintroduce it - along with shorter slide jumps.

This has **not been tested here**, and it is a community explanation rather than a confirmed engine finding. It is a
good candidate for a [rig](../modding/rig) test: repeat a fixed slide jump from a save state and measure the landing
position at 50 Hz and at 60 Hz.
:::

## NTSC-U 1.0 quirks worth knowing

Useful mostly for reading other people's videos and speedruns, which are often NTSC:

- A **big tree next to the farm** which is not in any other version, and which lets players bypass Totem Hokum easily.
- Cortex's and Mecha-Bandicoot's plasma blasts are much larger.
- Skipping an FMV requires waiting a second first.
- Crates exist that no other version has.
- There is **no checkpoint outside the top lab's interior**, and Cortex starts far from the entrance inside it.
- An extra checkpoint next to the world checkpoint at the start of Rockslide Rumble.
- Enemies in the corridor just before the final boss, which PAL removed.
- Dying while triggering the first Boiler Room Doom cutscene locks Crash in place.

NTSC PS2 2.0, the *Action Pack* build, back-ports the PAL crash fixes onto the American version.

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
