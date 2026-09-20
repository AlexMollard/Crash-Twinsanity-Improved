<div align="center">

<img src="wiki/static/img/logo.svg" alt="" width="112" height="112">

# Crash Twinsanity Improved

**A fix-and-polish mod for the PAL release of *Crash Twinsanity* (PS2), built for PCSX2.**
Restores the cutscene skipping the developers cut, loads levels faster, adds 480p/60 Hz output, and ships widescreen,
HD texture and graphics presets. One script turns your own disc image into a patched ISO.

[![Platform](https://img.shields.io/badge/platform-PlayStation%202-003791?logo=playstation&logoColor=white)](#requirements)
[![Emulator](https://img.shields.io/badge/emulator-PCSX2%202.x-1f6feb)](https://pcsx2.net)
[![Region](https://img.shields.io/badge/region-PAL%20%C2%B7%20SLES--52568%20v1.01-555)](#requirements)
[![Cutscene skips](https://img.shields.io/badge/cutscene%20skips%20restored-16-2ea44f)](#cutscene-skip-status)
[![Python](https://img.shields.io/badge/python-3-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![.NET](https://img.shields.io/badge/.NET%20Framework-4.8-512BD4?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com)
[![Last commit](https://img.shields.io/github/last-commit/AlexMollard/Crash-Twinsanity-Improved)](https://github.com/AlexMollard/Crash-Twinsanity-Improved/commits/main)

[Features](#features) · [Quick start](#quick-start) · [Cutscene skips](#cutscene-skip-status) · [Gameplay fixes](#gameplay-fixes) · [How it works](#how-it-works) · [Roadmap](#roadmap) · [Wiki](https://alexmollard.github.io/Crash-Twinsanity-Improved/) · [Credits](#credits)

</div>

> [!IMPORTANT]
> This repository contains **no game data**. You need your own copy of the PAL disc
> (*Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It)*, SLES-52568 v1.01, PCSX2 CRC `1510E1D1`).
> The build never modifies it and writes a separate `[Modded]` ISO next to it.

## Features

| | Feature | Where | Notes |
|:-:|---|---|---|
| ⏭️ | **Cutscene skip: hold △** | ISO | Brings back the skip the developers disabled, and wires it back into scenes where the skip was removed from the level data. [Status ↓](#cutscene-skip-status) |
| 💬 | **"Hold △ to skip" prompt** | ISO | Appears in the letterbox's bottom bar during every skippable cutscene, in all five languages. |
| 🎬 | **Movies answer △ too** | ISO | The pre-rendered movies only ever stopped for ✕, and only after a moment. They now take the same hold-△ as everything else. [Details ↓](#skipping-the-movies) |
| 🛡️ | **Aku Aku invincibility that works** | ISO | With three masks Crash no longer dies to TNT, Nitro or bomb explosions. [Details ↓](#aku-aku-invincibility) |
| 🌑 | **Shadows on crates** | ISO | Crash's shadow now falls on crates too, so you can see where you'll land. [Details ↓](#shadows-on-crates) |
| 🗿 | **A beaten boss stays beaten** | ISO | The defeated Tiki Mon still hurt anything that touched it, costing a mask or the whole fight. [Details ↓](#things-that-hurt-when-they-shouldnt) |
| 👻 | **No more invisible Crash** | ISO | Getting hurt just before a cutscene could leave Crash invisible through the scene and after it. [Details ↓](#invisible-crash-after-a-cutscene) |
| ⏱️ | **Faster loading** | ISO + PCSX2 | Level loads take 25–35% less time from the ISO changes alone, and 40–50% less with PCSX2's Fast CDVD (on in the preset). [Details ↓](#faster-loading) |
| 📺 | **480p / 60 Hz output** | ISO | Progressive output instead of 50 Hz PAL interlaced (patch by PeterDelta), with the game's frame timing set to match: a steady 60 fps, and movies at their real speed. [Details ↓](#steady-60-fps) |
| 🖥️ | **Widescreen 16:9 or 21:9 ultrawide** | PCSX2 | 21:9 is enabled by default. Use one or the other, never both. |
| 🎨 | **HD textures** | PCSX2 | CRASHARKI's *ctwin-tp* pack (616 PNGs, English level cards). |
| ⚙️ | **Graphics preset** | PCSX2 | 6× resolution, 16× anisotropic filtering, High blending, CAS sharpening, no dithering. |
| 🌐 | **English by default** | PCSX2 | The PAL disc follows the BIOS language, so the BIOS `.NVM` is switched to English. |

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

<details>
<summary><b>Command-line build</b></summary>

```bash
python tools/build_mod.py                      # finds the original ISO by CRC, writes "<name> [Modded].iso"
python tools/build_mod.py --src my.iso --out out.iso
python tools/verify_iso.py original.iso "original [Modded].iso"   # sanity-check a build
```

</details>

## Cutscene skip status

Hold **△** during a cutscene to skip it. Every skippable scene shows *HOLD △ TO SKIP* in the bottom letterbox bar. Every level edit below is tested on the automated rig: the scene is played in full and then skipped from the same save state. The rig checks that gameplay comes back sooner and that the player ends in the same situation.

| Status | Cutscene | Full → skipped¹ | What the skip also does |
|:-:|---|:-:|---|
| ✅ | Wired-in skips: Aku Aku training, Totem Hokum, Dingodile, Uka Uka, Henchmania, … | — | Executable patch only |
| ✅ | Beach: Aku Aku crate (mask) | — | Hides the crate's Aku Aku |
| ✅ | Beach training | 6.1 s → 4.6 s | |
| ✅ | Angry skunk | 11.4 s → 4.6 s | |
| ✅ | Rooftop Rampage | 13.2 s → 4.4 s | |
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
| ⛔ | Totem falling | — | **Left unskippable.** Skipping drops Crash into the totem chase before it's set up, and he dies. |
| 🚧 | Party arena | — | Work in progress (`mod/levels-wip`): the scene is switched on by beating the Mechabandicoot, which the rig can't do yet |

<sub>¹ Time from the start of the scene until the player has control again. The skipped times include about 2.5 s of the rig's own wait and button hold.</sub>

> [!NOTE]
> **Cutscenes that are movies.** Some of what the game calls a cutscene is a pre-rendered movie rather than an in-engine
> scene - the Iceberg Lab interior, for instance, plays 53 seconds of `H02_B.PSS` every time you walk in. Those are not
> in the table: they already stopped for ✕ in the retail game, and now [answer △ as well](#skipping-the-movies).

> [!NOTE]
> **Known differences after a skip.** A few level hints don't appear: "Clear a path for Cortex!", "Use ◯ to crouch", "Tap □ to rapid fire". In Iceberg Lab and Classroom Chaos the character stands a few steps from where the full scene would leave them.

## Gameplay fixes

### Aku Aku invincibility

Collecting a third mask sets Crash's invincible flag for 8 seconds, but the damage handler lets any hit of 50 or more
through, and every explosion (TNT, Nitro, bombs) deals 100. So an invincible Crash still died to TNT. The fix
(`mod/elf_patches.txt`) makes invincibility also block damage flagged as an explosion; other instant deaths still go
through. The same flag covers the two-second grace period after a hit, so explosions no longer kill you during it either.
Rig-tested: TNT while invincible leaves Crash at full health, and without invincibility it still kills. Enemy hits are unchanged.

### Shadows on crates

Characters cast a real silhouette shadow: one small volume per bone, drawn straight down into a screen-space mask.
The mask is applied only to pixels whose material sets the GS *alpha correction* flag (FBA), which marks them as
shadow receivers. Level scenery has the flag on. Characters have it off, so they don't shadow themselves. Most crate
materials were given the character settings, so Crash's shadow never showed on a crate. The build
(`tools/materials.py`) switches the flag on for every opaque crate material in all levels, the extra-life crate
included: 580 shaders in 89 level files, one byte each, with no size changes. Rig-tested with an A/B comparison on the
Rooftop iron crates, in both the software and hardware renderers.

Moving platforms were checked the same way. Every lift, bridge, ice floe, hovering platform, boat and holo-platform in the
game already has the flag on, so they already receive the shadow. Apart from crates, the only objects without it are
characters, enemies, doors and walls.

### Steady 60 fps

The 480p / 60 Hz patch switches the video output to 60 Hz, but the game still set its internal frame rate to PAL's
50 from the start-up region flag. That number is used for one thing: how much of each frame the background loader
may use. Believing a frame lasts 20 ms instead of 16.7 ms, the loader overran the frame wherever it stays busy
(the hubs), and roughly every fifth frame was shown twice - about 50 fps with visible judder. One word in
`mod/elf_patches.txt` sets it to 60. Rig: in the Earth hub 57-61 of 300 frames were doubled before, 1 of 360 after,
and level loads got a little faster too (Classroom Chaos 9 s → 8 s with Fast CDVD), since no frames are wasted.

### Movies at their real speed

The movie player shows a new frame on every second vsync: 25 fps at PAL's 50 Hz, but 30 fps - 20% fast - once the
output runs at 60 Hz. The vsync callback now counts in fifths (a frame every 2.4
vsyncs), which is exactly 25 fps at 60 Hz, and keeps counting while the player is still decoding, as the original
flag did. Rig, reading the player's own frame counter: the boot movies went from 30.1 and 29.7 fps to 25.0 and
24.7 fps; the original disc at 50 Hz plays them at 25.1 and 24.8.

### Skipping the movies

About half of Twinsanity's cut scenes are pre-rendered movies rather than in-engine scenes - walking into the Iceberg
Lab interior plays 53 seconds of `H02_B.PSS`. The retail game does let you cut one short, but only with **✕**, and only
after about a second, which is easy to miss when every other skip in this mod is hold-△.

Movies now answer **△** as well. The movie player checks once a frame whether its stream is still running and shuts it
down when the answer is no; that check now goes through a stub (`mod/elf_patches.txt`) which also reads the Triangle
button - the same pad read the cut scene skip uses - and answers "finished" after 30 frames of holding. Nothing else
changes: the movie stops down its own ending path, the script that started it carries on as if it had played out, and
✕ still works exactly as before. The half-second hold keeps a button pressed for another reason from cutting a movie
short.

Rig-tested at the lab interior from a fresh boot: untouched, the movie runs 54.2 s; with △ held it ends in 1.8 s, in
the same place and the same game-flow state; ✕ ends it in 6.8 s, matching the original disc's 7.0 s. The start-up
logos are movies too, so holding △ through them brings the title screen up after 44 s instead of 62 s.

### Things that hurt when they shouldn't

Beat the Tiki Mon at the top of the Earth hub and the totem drops to the ground and stays there, looking thoroughly
finished. Walk into it and it still hits you - a mask if you have one, otherwise a life and the whole fight again.

Contact damage is one flag on an object (agent bit 6, which the game sets and clears with `SetAgent` all over the
place - 718 scripts turn it off). The Tiki Mon's fight ends with `BossModeExit`, a cutscene and nothing else: the flag
is never cleared, so the wreck keeps hitting. The level recipe `mod/levels/harmless_after_defeat.ops` adds the game's
own `SetAgent(64)` to the last step of the boss script. The totem keeps its collision, so you can still climb on it.

Rig-tested by hooking the engine's contact-damage call and counting hits: before the fight, touching the boss lands 19
hits and costs a mask, exactly as it should; after the defeat it lands none and Crash can stand on the wreck.

More of the game is being swept for the same thing - see the [roadmap](#roadmap).

### Invisible Crash after a cutscene

After a hit, Crash flickers for two seconds: the grace-period code hides him for the last fifth of every 0.2 s while
he can't be hurt again. When a cutscene takes control of the player (and again when it hands control back), the game
resets that state machine without ending it, so whatever the flicker last set sticks. One time in five that is
"hidden": Crash is missing from the whole cutscene, and stays invisible in gameplay afterwards until something else
shows him. The reset now goes through a small stub (`mod/elf_patches.txt`) that ends a running grace period properly,
making the character visible again and clearing the grace invincibility. Rig-tested with a worm hit followed by the
Aku Aku crate tutorial: without the fix Crash is gone from the scene and from gameplay after it, with it he is visible
in both, and a normal hit still flickers for exactly two seconds.

### Faster loading

Entering a level streams 15 to 25 MB from `CRASH.BD`: the level plus the neighbouring areas it keeps loaded. Three
things made that slow:

- **Each disc read waited for the next frame.** The loader queues reads and sent the queue to the IOP only once per
  frame, so every read cost at least a frame, even when the drive was idle. A 14-instruction stub
  (`mod/elf_patches.txt`) now sends the queue before each loader step. It sits in an unused debug function.
- **The level data sat on the slow inner part of the disc.** A PS2 drive spins a DVD at constant speed (CAV), so the
  outer edge reads up to 2.5× faster than the inner edge. PCSX2 models this too. `CRASH.BD` started 225 MB into the
  disc. The build now puts it at the end, and moves the movies and speech banks that followed it into its old place,
  so the image doesn't grow.
- **Emulated disc speed.** The PCSX2 preset turns on *Fast CDVD*, which halves emulated read times. The movies, which
  stream from the disc, play at their normal pace with it on. It's a per-game setting, so you can switch it off in the
  game's properties.

The first two are changes to the ISO, so they should help on a real PS2 as well (only tested in PCSX2). Most of the
remaining time is the drive itself. Load times measured with the rig, from its level warp until Crash can move, on a fresh boot:

| Level | Before | Modded ISO | Modded ISO + Fast CDVD |
|---|:-:|:-:|:-:|
| Earth hub (`huba`) | 9.5 s | 7.0 s | 5.5 s |
| Classroom Chaos (`crgpa08`) | 16.0 s | 10.5 s | 8.0 s |

## Known side effects of 480p / 60 Hz

- On a real PS2 this needs a 480p-capable connection, such as component cables or an HDMI adapter. Over SCART or composite to a PAL TV you get no picture, so use the original disc there.

## How it works

<details>
<summary><b>Why cutscene skipping was broken</b></summary>

<br>

Twinsanity's level scripts are state machines. A cutscene "director" plays the scene and checks script condition **572**
(`CutsceneSkipped`) every frame. When that condition is true, it jumps to a skip branch. Some scenes also run a
`*_CUTSCENE_SKIP` script, and the actors handle user message **244** ("skipped") by warping to their end marks.

In the retail build, condition 572 was stubbed to always return `0`. On top of that, about 19 scenes had their skip branch (and
sometimes the actors' 244 handlers) moved into unreachable states in the level data.

- **Executable patch** (`mod/elf_patches.txt`): condition 572 becomes "the player holds △", reusing the game's own
  Triangle check. That alone restores every scene whose skip branch was still wired in.
- **Level edits** (`mod/levels/*.ops`): reconnect the cut branches with `twinsdump edit`. Where a scene sets up the
  next section, the edit also runs the scene's own last step: character switches, actors leaving, and so on.
- **Skip prompt** (`mod/skip_prompt.ops`, `mod/text.txt`): the text goes into an unused slot of the game's hint table
  (`Language/AgentLab`, with `^` as the △ glyph). Each skippable scene's director sets it with `BottomTextDisplay`
  when the scene starts and clears it when the scene ends or is skipped. It skips `BottomTextShow`, which would
  swap the letterbox for the translucent hint strip, so the text is drawn inside the letterbox instead.

</details>

<details>
<summary><b>How the ISO is built</b></summary>

<br>

`tools/build_mod.py` works on a copy of the original ISO:

1. Patches `SLES_525.68` from `mod/elf_patches.txt`. Every word is checked against its original value before anything is written.
2. Applies each level recipe to the original `.rm2` from `CRASH.BD`, then splices the edited script items back in.
   It also switches on the shadow-receiver flag for crate materials in every level (`tools/materials.py`).
3. Moves `CRASH.BD` (all level data, about 930 MB) to the end of the image, the fast outer edge of the disc, and moves
   the files that followed it (speech banks, IOP modules, movies) down into its place. The image stays the same size and
   `CRASH.BD` can grow freely. The game finds its files by name, and both the ISO9660 and UDF directories are updated.
4. Rebuilds `CRASH.BD/BH` and writes the matching `.pnach` for the new executable CRC.

`tools/verify_iso.py` checks the result: the ISO9660 and UDF directories agree, the descriptor tags are valid, no files
overlap, and every untouched file is byte-identical to the original.

</details>

## The wiki

How the engine actually works - the scripting system, how a cutscene is put together, objects and their agent flags,
the archive and disc layout, the movie player, and the addresses everything lives at - is written up as a separate
site in [`wiki/`](wiki), built with [Docusaurus](https://docusaurus.io):

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
├── shader_survey.py     what GS state the game's own materials ask for
├── twinsdump/           level inspection and editing CLI (uses the Twinsanity Editor library)
├── re/                  headless Ghidra scripts for the twinsanity-reversed project (ghidra.py xref/decomp/callers)
├── rig/                 automated test rig driving an isolated PCSX2 over PINE
├── twinsanity-editor/   submodule
└── twinsanity-reversed/ submodule
wiki/                   the engine wiki (Docusaurus)
```

<details>
<summary><b>Test rig</b></summary>

<br>

The rig drives a separate portable PCSX2 (`tools/pcsx2-test`, created by `setup_test_pcsx2.py`) through the PINE
protocol. It has a virtual pad, screenshots, RAM access, save states, a level warp and a teleport. That's enough to play
a cutscene in full and skipped from the same state and compare the results.

```bash
cd tools/rig
python rebuild.py --include mod/levels-wip --levels crgpa08   # test ISO + fresh save states
python rebuild.py --include tools/rig/testops                 # test-only recipes (e.g. jump the Tiki Mon to his defeat)
python run_cutscenes.py cutscenes_orphan.txt classroom        # full vs skipped, verdict in results/summary.txt
python prompt_test.py classroom crgpa08 6.60 2.08 -20.58 10.8  # skip prompt shown during the scene, gone after
RIG_FASTCDVD=true python load_bench.py fast                   # level load times from a fresh boot
python arrival_test.py walrus Levels\Ice\HighSeas\gpa10 results skip   # scenes that play as a level loads
python fmv_test.py Levels\Ice\Hub\labint -14.34 -2.85 -10.33 hold    # pre-rendered movie, skipped
python make_cortex_state.py amberly_cortex Levels\school\Madame\amberly   # Cortex levels need Cortex (via the classroom skip)
```

</details>

## Roadmap

<div align="center">

| ✅ Shipped | 🔭 Next up | 🧱 Bigger projects | 🔬 Investigating | ✔️ Checked, fine here | ⛔ Not doing |
|:-:|:-:|:-:|:-:|:-:|:-:|
| **11** | **4** | **4** | **5** | **2** | **2** |

*Nothing ships until the automated rig has played it. Most of the open list comes from bugs the community has
documented for the PAL release, or from surveys of the level data; each line says where it stands and what is in the
way. The [wiki](https://alexmollard.github.io/Crash-Twinsanity-Improved/) explains the machinery behind all of it.*

</div>

### ✅ Shipped

| | Fix | What you notice |
|:-:|---|---|
| ⏭️ | **Cutscene skip** | Hold △ and the scene ends. 16 scenes needed their cut branch rebuilt in the level data; the rest came back with the executable patch. [Status ↑](#cutscene-skip-status) |
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

### 🔭 Next up

| | Item | Where it stands |
|:-:|---|---|
| 🧭 | **Evil Crash runs in circles (Bandicoot Pursuit)** | The famous PAL one. Reproduced on the rig: his run heading sits about 20° off the route and he orbits the node instead of reaching it. It is his steering code, not the level's path data. |
| 🦭 | **Rusty Walrus runs in circles** | [Reported for PAL](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity), and the walrus uses the same route-node steering as Evil Crash - very likely one bug behind two chases. It did not reproduce standing still (the walrus arrived and killed Crash 220 times in 32 s), so the repro needs the player actually running the route. |
| 🔒 | **Softlock after the Rusty Walrus chase** | Mashing jump through the cutscene skips the Brio/Tropy scene and strands Crash on the boss iceberg with no music. Squarely this mod's territory - the same family as the invisible-Crash fix. |
| 🗿 | **The rest of the contact-damage reports** | The Tiki Mon was the first. `tools/rig/hurthook.py` names whatever hit you, so the remaining reports get checked one at a time. |

### 🧱 Bigger projects

These are features rather than fixes, and each needs new tooling before it can even be attempted.

| | Item | What it would take |
|:-:|---|---|
| 🚩 | **Checkpoints in the long stretches** | A survey of every level file found 22 of the 93 substantial ones with no checkpoint crate placed at all, among them the biggest in the game - the Earth hub, the 10th-dimension lab exterior, the Rockslide start, the Academy hub. Some of those respawn you another way, so each needs checking by playing it. Adding one means adding an *instance* to a level, which `twinsdump` cannot do yet; that tooling is the actual work, and placements have to be chosen in-game rather than guessed from coordinates. |
| 🎥 | **Scenes that never play** | Ten cutscene directors are placed in levels with nothing pointing at them - among them `UKAUKA_DEFEATED`, `BR_CORTEX_PIPE`, `CAVERN`, `EARTH_HUB` and `HUB2_TO_HUB3`. Some are started another way (the Iceberg Lab's turned out to be a movie), so each has to be checked before claiming anything. Any that genuinely never run are scenes sitting unused on the retail disc, and restoring one is the same kind of edit as restoring a skip. |
| 💡 | **Lighting** | The levels have a real runtime lighting rig, and it is in the `.sm2` scenery files this mod has never opened: 140 ambient, 432 directional, 103 point and 11 negative lights across the game, evaluated per vertex. The Earth hub alone has a grey ambient, a warm key, a cool fill and four wide point lights. All of it is editable data that costs nothing at runtime, which makes it the one real lever for "better lit" - unlike Phong, which the PS2's hardware cannot do at all ([why](https://alexmollard.github.io/Crash-Twinsanity-Improved/engine/lighting)). |
| 🎨 | **The rest of the rendering** | A survey of all 10,464 material shaders says the easy levers are already pulled: every one is gouraud-shaded with linear magnification and a slight sharpening LOD bias. Two findings came out of it - **no material in the game enables GS fog at all**, so the fog line is draw distance or vertex shading rather than a fog register; and the shadow-receiver set is finished, since a test build making all 3,218 remaining opaque materials receivers was indistinguishable from the shipped 580. What is left is code: draw distance and the shadow pass. The rig can A/B a rendering change with the framing locked (`RIG_GS`, plus a save state so only the rendering differs). |

### 🔬 Investigating

| | Item | Where it stands |
|:-:|---|---|
| 🌫️ | **The fog line** | A visible seam where the fog starts. Needs a level and a spot to reproduce before anything can be measured. |
| 🐌 | **Slow menus** | [Documented as a PAL trait](https://beyondtwinsanity.com/evolution/versions/). Needs measuring on the rig before it can be called a bug or a fix. |
| 🧷 | **Cortex detaches from Crash at Farmer Ernest's fence** | [Reported for PAL](https://beyondtwinsanity.com/evolution/versions/). Not yet reproduced. |
| 🎭 | **Leftovers after being hurt into a cutscene** | The floating mask and Cortex's floating ray gun are the same family as the invisible-Crash bug, which is fixed; these are separate objects whose state is not reset. |
| 🐜 | **Enemies that freeze solid** | The "undefeatable ant" in Cavern Catastrophe stays frozen until you lose a life. Sounds like a script state machine that stops stepping - the same shape as several things already fixed. |

### ✔️ Checked, fine here

| | Item | Finding |
|:-:|---|---|
| ✔️ | **Touching the stunned Coco** | Kills Crash on NTSC-U and Xbox, and it is the case people ask about most. It does not happen on PAL: two sources say so, and a rig sweep of the Psychetron room after the scene landed no hits at all. |
| ✔️ | **Skipping movies** | They were never unskippable - ✕ has always stopped them, about a second in. The mod adds △ for consistency; measured 54.3 s untouched, 7.0 s with ✕ on the original disc. |

### ⛔ Not doing

| | Item | Why |
|:-:|---|---|
| ⛔ | **Skipping the falling-totem scene** | The skip drops Crash into the totem chase before it is set up and he dies. The developers cut that one for the same reason; it stays unskippable. |
| ⛔ | **New levels and new art** | This is a fix-and-polish mod: restoring what is on the disc, not adding to it. The *Beyond Twinsanity* mods (AnTime Agony, Lava Caves) add content - install them with [CrateModLoader](https://github.com/TheBetaM/CrateModLoader). |

## Credits

- **PeterDelta**: 480p / 60 Hz patch ([PeterDelta/PCSX2](https://github.com/PeterDelta/PCSX2))
- **CRASHARKI**: widescreen patch ([PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches)) and the HD texture pack ([ctwin-tp](https://github.com/CRASHARKI/ctwin-tp))
- **TechieSaru**: 21:9 fix ([GBAtemp thread](https://gbatemp.net/threads/648804))
- **Smartkin, NeoKesha and contributors**: [Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) and [twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed)

<sub>Crash Twinsanity is © its respective owners. This is an unofficial fan project and isn't affiliated with or endorsed by them.</sub>
