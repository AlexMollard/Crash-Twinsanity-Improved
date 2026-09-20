<div align="center">

<img src="wiki/static/img/logo.svg" alt="" width="112" height="112">

# Crash Twinsanity Improved

**A fix-and-polish mod for the PAL release of *Crash Twinsanity* (PS2), built for PCSX2.**
Restores the cutscene skipping the developers cut, loads levels faster, adds 480p/60 Hz output, and ships widescreen,
HD texture and graphics presets. One script turns your own disc image into a patched ISO.

[![Platform](https://img.shields.io/badge/platform-PlayStation%202-003791?logo=playstation&logoColor=white)](#requirements)
[![Emulator](https://img.shields.io/badge/emulator-PCSX2%202.x-1f6feb)](https://pcsx2.net)
[![Region](https://img.shields.io/badge/region-PAL%20%C2%B7%20SLES--52568%20v1.01-555)](#requirements)
[![Cutscene skips](https://img.shields.io/badge/cutscene%20skips%20restored-16-2ea44f)](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/what-changed)
[![Python](https://img.shields.io/badge/python-3-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![.NET](https://img.shields.io/badge/.NET%20Framework-4.8-512BD4?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com)
[![Last commit](https://img.shields.io/github/last-commit/AlexMollard/Crash-Twinsanity-Improved)](https://github.com/AlexMollard/Crash-Twinsanity-Improved/commits/main)

[Features](#features) · [Quick start](#quick-start) · [What it changes](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/what-changed) · [Roadmap](#roadmap) · [Wiki](https://alexmollard.github.io/Crash-Twinsanity-Improved/) · [Credits](#credits)

</div>

> [!IMPORTANT]
> This repository contains **no game files**. You need your own copy of the PAL disc
> (*Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It)*, SLES-52568 v1.01, PCSX2 CRC `1510E1D1`).
> The build never modifies it and writes a separate `[Modded]` ISO next to it.

## Features

| | Feature | Where | Notes |
|:-:|---|---|---|
| ⏭️ | **Cutscene skip: hold △** | ISO | Brings back the skip the developers disabled, and wires it back into the scenes where it was cut out of the level data. |
| 💬 | **"Hold △ to skip" prompt** | ISO | Appears in the letterbox's bottom bar during every skippable cutscene, in all five languages. |
| 🎬 | **Movies answer △ too** | ISO | The pre-rendered movies only ever stopped for ✕, and only after a moment. They now take the same hold-△ as everything else. |
| 🛡️ | **Aku Aku invincibility that works** | ISO | With three masks Crash no longer dies to TNT, Nitro or bomb explosions. |
| 🌑 | **Shadows on crates** | ISO | Crash's shadow now falls on crates too, so you can see where you'll land. |
| 🗿 | **A beaten boss stays beaten** | ISO | A defeated boss still hurt anything that touched it, costing a mask or the whole fight. |
| 👻 | **No more invisible Crash** | ISO | Getting hurt just before a cutscene could leave Crash invisible through the scene and after it. |
| ⏱️ | **Faster loading** | ISO + PCSX2 | Level loads take 25–35% less time from the ISO changes alone, and 40–50% less with PCSX2's Fast CDVD (on in the preset). |
| 📺 | **480p / 60 Hz output** | ISO | Progressive output instead of 50 Hz PAL interlaced (patch by PeterDelta), with the game's frame timing set to match: a steady 60 fps, and movies at their real speed. |
| 🖥️ | **Widescreen 16:9 or 21:9 ultrawide** | PCSX2 | 21:9 is enabled by default. Use one or the other, never both. |
| 🎨 | **HD textures** | PCSX2 | CRASHARKI's *ctwin-tp* pack (616 PNGs, English level cards). |
| ⚙️ | **Graphics preset** | PCSX2 | 6× resolution, 16× anisotropic filtering, High blending, CAS sharpening, no dithering. |
| 🌐 | **English by default** | PCSX2 | The PAL disc follows the BIOS language, so the BIOS `.NVM` is switched to English. |

<p align="center">
<img src="wiki/static/img/shots/skip-prompt-beach.png" alt="Crash on the beach with HOLD TRIANGLE TO SKIP shown in the letterbox" width="520">
<br>
<sub>The prompt the retail game never shows you, because the skip behind it was disabled before release.</sub>
</p>

## Quick start

### Requirements

- PCSX2 2.x with a PS2 BIOS
- Python 3
- The .NET SDK and Visual Studio's MSBuild. These are only needed the first time, to build the level tool.
- Your own PAL ISO (see the note above)

### Build and play

1. **Drop your ISO** into the repository folder. Any file name works, because it's recognised by its PCSX2 CRC.
2. **Run `Build Modded ISO.bat`.** It writes `<name> [Modded].iso` and then installs the matching PCSX2 settings.
3. **Boot the `[Modded]` ISO** in PCSX2 and press <kbd>Alt</kbd>+<kbd>Enter</kbd> for fullscreen.

> [!TIP]
> If PCSX2 resets its settings, run `Apply CrashMod Settings.bat` with PCSX2 closed. It restores the patches, the
> graphics preset with Fast CDVD, the texture pack and the English BIOS language, and it's safe to run any time.

> [!NOTE]
> On a real PS2, 480p needs a 480p-capable connection such as component cables or an HDMI adapter. Over SCART or
> composite to a PAL TV you get no picture, so use the original disc there.

<details>
<summary><b>Command-line build</b></summary>

<br>

```bash
python tools/build_mod.py                      # finds the original ISO by CRC, writes "<name> [Modded].iso"
python tools/build_mod.py --src my.iso --out out.iso
python tools/verify_iso.py original.iso "original [Modded].iso"   # sanity-check a build
```

</details>

## What it actually changes

Eighteen cutscenes are skippable that weren't, plus six gameplay fixes and the loading and timing work. Nothing ships
until the automated rig has played it: each scene is played in full and then skipped from the same save state, and the
rig checks that gameplay comes back sooner and the player ends up in the same situation.

**➤ [What the mod changes](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/what-changed)** — the
scene-by-scene status with before/after timings, and how each fix was found and proved.

> [!WARNING]
> That page names scenes, bosses and late-game locations. The feature table above is spoiler-free; the wiki is not.

## The wiki

How the engine actually works — the scripting system, how a cutscene is put together, objects and their agent flags,
the archive and disc layout, the movie player, the lighting rig, and the addresses everything lives at — plus who
built the game, what got cut, and how the six retail versions differ:

**➤ [alexmollard.github.io/Crash-Twinsanity-Improved](https://alexmollard.github.io/Crash-Twinsanity-Improved/)**

```bash
cd wiki && npm install && npm start      # live preview on http://localhost:3000
```

## Development

```text
mod/
├── elf_patches.txt      executable patches (address, original word, new word)
├── levels/*.ops         level script recipes built into the ISO
├── levels-wip/*.ops     recipes still being tested (not built by default)
└── pcsx2/modded.pnach   PCSX2 patch template (widescreen / ultrawide)
tools/
├── build_mod.py         builds the [Modded] ISO
├── isotools.py          ISO9660 + UDF, CRASH.BD/BH archive and executable helpers
├── verify_iso.py        checks a build against the original
├── materials.py         material fixes (crates receive shadows)
├── twinsdump/           level inspection and editing CLI
├── re/                  headless Ghidra scripts for twinsanity-reversed
├── rig/                 automated test rig driving an isolated PCSX2 over PINE
└── *-editor, *-reversed submodules
wiki/                    the engine wiki (Docusaurus)
```

Writing a level recipe, patching the executable and driving the rig are all documented on the wiki:
[Level recipes](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/recipes) ·
[Executable patches](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/elf-patches) ·
[The test rig](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/rig)

## Roadmap

<div align="center">

| ✅ Shipped | 🔭 Next up | 🧱 Bigger projects | 🔬 Investigating | ✔️ Checked, fine here | ⛔ Not doing |
|:-:|:-:|:-:|:-:|:-:|:-:|
| **11** | **4** | **4** | **5** | **2** | **2** |

*Nothing ships until the automated rig has played it. Most of the open list comes from bugs the community has
documented for the PAL release, or from surveys of the level data; each line says where it stands and what is in the
way. The [wiki](https://alexmollard.github.io/Crash-Twinsanity-Improved/) explains the machinery behind all of it.*

</div>

<details>
<summary><b>✅ Shipped</b></summary>

<br>


| | Fix | What you notice |
|:-:|---|---|
| ⏭️ | **Cutscene skip** | Hold △ and the scene ends. 16 scenes needed their cut branch rebuilt in the level data; the rest came back with the executable patch. [Status](https://alexmollard.github.io/Crash-Twinsanity-Improved/modding/what-changed) |
| 💬 | **Skip prompt** | *HOLD △ TO SKIP* in the letterbox, in all five languages, only while a scene can actually be skipped. |
| 🎬 | **Movies answer △** | They only stopped for ✕ before; now they take the same hold-△ as everything else, logos included. |
| 🛡️ | **Invincibility that works** | Three masks now survive TNT, Nitro and bombs instead of dying to them. |
| 🗿 | **A beaten boss stays beaten** | The defeated Tiki Mon no longer hits you when you walk into it - a [long-standing report](https://crashtwinsanity.fandom.com/wiki/Tikimon). |
| 👻 | **Visible Crash** | Getting hurt just before a cutscene no longer leaves him invisible for the rest of the level ([reported here](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity/Cutscene_Glitches_List)). |
| 🌑 | **Shadows on crates** | Crash's shadow falls on crates, so you can see where you will land. |
| ⏱️ | **Faster loading** | Level loads 25-35% shorter from the ISO alone, 40-50% with Fast CDVD. |
| 📺 | **Steady 60 fps** | 480p / 60 Hz output with the game's own frame timing matched to it - no more hub judder. |
| 🎞️ | **Movies at their real speed** | 25 fps instead of 30, so they no longer run a fifth too fast. |
| 📦 | **One-step build** | `Build Modded ISO.bat` turns your own disc image into a patched one and sets PCSX2 up to match. |

</details>

<details>
<summary><b>🔭 Next up</b></summary>

<br>


| | Item | Where it stands |
|:-:|---|---|
| 🧭 | **Evil Crash runs in circles (Bandicoot Pursuit)** | The famous PAL one, and the cause is now pinned to the engine: his move script has no facing condition and no turn command at all - it sets a focus position and the engine steers him - so there is nothing in the script data to tune. **The blocker is reproduction.** The chase gate is known exactly: Evil Crash waits for user message **269**, then branches on **counter 26** (1/2/3 = the three phases), and the summoner only sends 269 once it has a focus object, otherwise it runs `COM_GENERIC_CREATURE_ERROR`. Neither teleporting into the trigger box nor moving inside it starts any of that. A test recipe that rewrites his conditions to enter PHASE1 on a timer does not start him either. His instance context is **not** disabled (the engine's ignore-all-events bit is clear, checked against objects that are demonstrably alive in the same level), and his object has only one script slot, so nothing can reach him with the "activated" event - his script has to be started at spawn. So he is wakeable but never woken, and the next question is what calls `ActivateObjectInstance` for the others and skips him. |
| 🦭 | **Rusty Walrus runs in circles** | [Reported for PAL](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity), and the walrus uses the same route-node steering as Evil Crash - very likely one bug behind two chases. It did not reproduce standing still (the walrus arrived and killed Crash 220 times in 32 s), so the repro needs the player actually running the route. |
| 🔒 | **Softlock after the Rusty Walrus chase** | Mashing jump through the cutscene skips the Brio/Tropy scene and strands Crash on the boss iceberg with no music. Squarely this mod's territory - the same family as the invisible-Crash fix. |
| 🗿 | **The rest of the contact-damage reports** | The Tiki Mon was the first. `tools/rig/hurthook.py` names whatever hit you, so the remaining reports get checked one at a time. |

</details>

<details>
<summary><b>🧱 Bigger projects</b></summary>

<br>


These are features rather than fixes, and each needs new tooling before it can even be attempted.

| | Item | What it would take |
|:-:|---|---|
| 🚩 | **Checkpoints in the long stretches** | A survey of every level file found 22 of the 93 substantial ones with no checkpoint crate placed at all, among them the biggest in the game - the Earth hub, the 10th-dimension lab exterior, the Rockslide start, the Academy hub. Some of those respawn you another way, so each needs checking by playing it. Adding one means adding an *instance* to a level, which `twinsdump` cannot do yet; that tooling is the actual work, and placements have to be chosen in-game rather than guessed from coordinates. |
| 🎥 | **Scenes that never play** | Ten cutscene directors are placed in levels with nothing pointing at them - among them `UKAUKA_DEFEATED`, `BR_CORTEX_PIPE`, `CAVERN`, `EARTH_HUB` and `HUB2_TO_HUB3`. Some are started another way (the Iceberg Lab's turned out to be a movie), so each has to be checked before claiming anything. Any that genuinely never run are scenes sitting unused on the retail disc, and restoring one is the same kind of edit as restoring a skip. |
| 💡 | **Lighting** | The levels have a real runtime lighting rig, and it is in the `.sm2` scenery files this mod has never opened: 140 ambient, 432 directional, 103 point and 11 negative lights across the game, evaluated per vertex. The Earth hub alone has a grey ambient, a warm key, a cool fill and four wide point lights. All of it is editable data that costs nothing at runtime, which makes it the one real lever for "better lit" - unlike Phong, which the PS2's hardware cannot do at all ([why](https://alexmollard.github.io/Crash-Twinsanity-Improved/engine/lighting)). |
| 🎨 | **The rest of the rendering** | A survey of all 10,464 material shaders says the easy levers are already pulled: every one is gouraud-shaded with linear magnification and a slight sharpening LOD bias. Two findings came out of it - **no material in the game enables GS fog at all**, so the fog line is draw distance or vertex shading rather than a fog register; and the shadow-receiver set is finished, since a test build making all 3,218 remaining opaque materials receivers was indistinguishable from the shipped 580. What is left is code: draw distance and the shadow pass. The rig can A/B a rendering change with the framing locked (`RIG_GS`, plus a save state so only the rendering differs). |

</details>

<details>
<summary><b>🔬 Investigating</b></summary>

<br>


| | Item | Where it stands |
|:-:|---|---|
| 🌫️ | **The fog line** | A visible seam where the fog starts. Needs a level and a spot to reproduce before anything can be measured. |
| 🐌 | **Slow menus** | [Documented as a PAL trait](https://beyondtwinsanity.com/evolution/versions/), and measured: on the retail disc a menu button takes about **0.82 s** to produce any visible response. The modded build's figure is still missing - those runs were made against a test ISO another session had rebuilt with a different executable, so they measured nothing. The harness is `tools/rig/menu_time.py`. |
| 🧷 | **Cortex detaches from Crash at Farmer Ernest's fence** | [Reported for PAL](https://beyondtwinsanity.com/evolution/versions/). Not yet reproduced. |
| 🎭 | **Leftovers after being hurt into a cutscene** | The floating mask and Cortex's floating ray gun are the same family as the invisible-Crash bug, which is fixed; these are separate objects whose state is not reset. **Did not reproduce** on the rig: taking the mask from the Aku Aku crate, losing it to a worm and running straight into the beach training scene left nothing floating, at 0.15 s and 0.2 s between the hit and the scene. Either the window is tighter than that or the teleport-driven repro is not close enough to how it happens in play. |
| 🐜 | **Enemies that freeze solid** | The "undefeatable ant" in Cavern Catastrophe stays frozen until you lose a life. Sounds like a script state machine that stops stepping - the same shape as several things already fixed. |

</details>

<details>
<summary><b>✔️ Checked, fine here</b></summary>

<br>


| | Item | Finding |
|:-:|---|---|
| ✔️ | **Touching the stunned Coco** | Kills Crash on NTSC-U and Xbox, and it is the case people ask about most. It does not happen on PAL: two sources say so, and a rig sweep of the Psychetron room after the scene landed no hits at all. |
| ✔️ | **Skipping movies** | They were never unskippable - ✕ has always stopped them, about a second in. The mod adds △ for consistency; measured 54.3 s untouched, 7.0 s with ✕ on the original disc. |

</details>

<details>
<summary><b>⛔ Not doing</b></summary>

<br>


| | Item | Why |
|:-:|---|---|
| ⛔ | **Skipping the falling-totem scene** | The skip drops Crash into the totem chase before it is set up and he dies. The developers cut that one for the same reason; it stays unskippable. |
| ⛔ | **New levels and new art** | This is a fix-and-polish mod: restoring what is on the disc, not adding to it. The *Beyond Twinsanity* mods (AnTime Agony, Lava Caves) add content - install them with [CrateModLoader](https://github.com/TheBetaM/CrateModLoader). |
</details>

## Credits

- **PeterDelta**: 480p / 60 Hz patch ([PeterDelta/PCSX2](https://github.com/PeterDelta/PCSX2))
- **CRASHARKI**: widescreen patch ([PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches)) and the HD texture pack ([ctwin-tp](https://github.com/CRASHARKI/ctwin-tp))
- **TechieSaru**: 21:9 fix ([GBAtemp thread](https://gbatemp.net/threads/648804))
- **Smartkin, NeoKesha and contributors**: [Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) and [twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed)

<sub>Crash Twinsanity is © its respective owners. This is an unofficial fan project and isn't affiliated with or endorsed by them.</sub>
