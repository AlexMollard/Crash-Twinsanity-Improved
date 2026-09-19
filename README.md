<div align="center">

# Crash Twinsanity Improved

**A fix-and-polish mod for the PAL release of *Crash Twinsanity* (PS2), built for PCSX2.**
Restores the cutscene skipping the developers cut, adds 480p/60 Hz output, and ships widescreen,
HD texture and graphics presets. One script turns your own disc image into a patched ISO.

[![Platform](https://img.shields.io/badge/platform-PlayStation%202-003791?logo=playstation&logoColor=white)](#requirements)
[![Emulator](https://img.shields.io/badge/emulator-PCSX2%202.x-1f6feb)](https://pcsx2.net)
[![Region](https://img.shields.io/badge/region-PAL%20%C2%B7%20SLES--52568%20v1.01-555)](#requirements)
[![Cutscene skips](https://img.shields.io/badge/cutscene%20skips%20restored-10-2ea44f)](#cutscene-skip-status)
[![Python](https://img.shields.io/badge/python-3-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![.NET](https://img.shields.io/badge/.NET%20Framework-4.8-512BD4?logo=dotnet&logoColor=white)](https://dotnet.microsoft.com)
[![Last commit](https://img.shields.io/github/last-commit/AlexMollard/Crash-Twinsanity-Improved)](https://github.com/AlexMollard/Crash-Twinsanity-Improved/commits/main)

[Features](#features) · [Quick start](#quick-start) · [Cutscene skips](#cutscene-skip-status) · [Gameplay fixes](#gameplay-fixes) · [How it works](#how-it-works) · [Development](#development) · [Credits](#credits)

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
| 🛡️ | **Aku Aku invincibility that works** | ISO | With three masks Crash no longer dies to TNT, Nitro or bomb explosions. [Details ↓](#aku-aku-invincibility) |
| 📺 | **480p / 60 Hz output** | ISO | Progressive output instead of 50 Hz PAL interlaced (patch by PeterDelta). |
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
> graphics preset, the texture pack and the English BIOS language, and it's safe to run any time.

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
| ⛔ | Totem falling | — | **Left unskippable.** Skipping drops Crash into the totem chase before it's set up, and he dies. |
| 🚧 | Rockslide Rumble, Walrus, Psychetron room (×2), dorm room, bell tower, party arena, lab interior | — | Work in progress (`mod/levels-wip`) |

<sub>¹ Time from the start of the scene until the player has control again. The skipped times include about 2.5 s of the rig's own wait and button hold.</sub>

> [!NOTE]
> **Known differences after a skip.** A few level hints don't appear: "Clear a path for Cortex!", "Use ◯ to crouch", "Tap □ to rapid fire". In Iceberg Lab and Classroom Chaos the character stands a few steps from where the full scene would leave them.

## Gameplay fixes

### Aku Aku invincibility

Collecting a third mask sets Crash's invincible flag for 8 seconds, but the damage handler lets any hit of 50 or more
through, and every explosion (TNT, Nitro, bombs) deals 100. So an invincible Crash still died to TNT. The fix
(`mod/elf_patches.txt`) makes invincibility also block damage flagged as an explosion; other instant deaths still go
through. The same flag covers the two-second grace period after a hit, so explosions no longer kill you during it either.
Rig-tested: TNT while invincible leaves Crash at full health, and without invincibility it still kills. Enemy hits are unchanged.

## Known side effects of 480p / 60 Hz

- FMVs play about 10% fast. Gameplay speed is unaffected.
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
3. Moves the English speech bank (`ENGLISH.MB/MH`, about 13 MB) to the end of the image so `CRASH.BD` can grow. The game
   finds its files by name, and both the ISO9660 and UDF directories are updated.
4. Rebuilds `CRASH.BD/BH` and writes the matching `.pnach` for the new executable CRC.

`tools/verify_iso.py` checks the result: the ISO9660 and UDF directories agree, the descriptor tags are valid, and every untouched file is
byte-identical to the original.

</details>

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
├── twinsdump/           level inspection and editing CLI (uses the Twinsanity Editor library)
├── re/                  headless Ghidra scripts for the twinsanity-reversed project (ghidra.py xref/decomp/callers)
├── rig/                 automated test rig driving an isolated PCSX2 over PINE
├── twinsanity-editor/   submodule
└── twinsanity-reversed/ submodule
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
python run_cutscenes.py cutscenes_orphan.txt classroom        # full vs skipped, verdict in results/summary.txt
python prompt_test.py classroom crgpa08 6.60 2.08 -20.58 10.8  # skip prompt shown during the scene, gone after
```

</details>

### Roadmap

- [x] Restore the cutscene skip (executable patch plus 10 level edits)
- [x] One-step ISO build with room for level edits
- [x] An on-screen "hold △ to skip" prompt, using the game's own hint text
- [x] Make three-mask invincibility protect from explosions
- [ ] Show Crash's shadow on crates
- [ ] The remaining cutscenes in `mod/levels-wip`

### Not included

The *Beyond Twinsanity* content mods (AnTime Agony, Lava Caves) add new content rather than fixes. Install them with
[CrateModLoader](https://github.com/TheBetaM/CrateModLoader).

## Credits

- **PeterDelta**: 480p / 60 Hz patch ([PeterDelta/PCSX2](https://github.com/PeterDelta/PCSX2))
- **CRASHARKI**: widescreen patch ([PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches)) and the HD texture pack ([ctwin-tp](https://github.com/CRASHARKI/ctwin-tp))
- **TechieSaru**: 21:9 fix ([GBAtemp thread](https://gbatemp.net/threads/648804))
- **Smartkin, NeoKesha and contributors**: [Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) and [twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed)

<sub>Crash Twinsanity is © its respective owners. This is an unofficial fan project and isn't affiliated with or endorsed by them.</sub>
