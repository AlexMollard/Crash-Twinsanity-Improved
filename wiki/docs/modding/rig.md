---
id: rig
title: The test rig
sidebar_position: 4
---

# The test rig

Every change in this mod is proved by playing it, not by reading it. The rig drives an isolated portable PCSX2
(`tools/pcsx2-test`, created by `setup_test_pcsx2.py`) over the PINE protocol on port 28012. Your own PCSX2 install is
never touched.

What it can do: a virtual pad, RAM read and write, save states, screenshots, a level warp, a teleport, and
screen-matching waits for menu navigation.

## The pieces

| File | What it is for |
|---|---|
| `rig.py` | The library and CLI: start/stop, `level()`, `teleport()`, `pos()`, `in_cutscene()`, `flow_state()`, `set_pad()`, `screenshot()` |
| `rebuild.py` | Builds `test.iso` and the whole state library from a fresh boot |
| `levels.txt` | `NAME PATH [cortex] [progress=N]` - what the state library contains |
| `cutscene_test.py` | Plays one scene in full, then skipped, from the same state, and compares |
| `run_cutscenes.py` | Runs `cutscene_test` over a list and records verdicts |
| `arrival_test.py` | Scenes that play the moment a level loads, from a fresh boot each time |
| `fmv_test.py` | Pre-rendered movies |
| `prompt_test.py` | The skip prompt appears during a scene and is gone afterwards |
| `load_bench.py` | Level load times from a fresh boot |
| `hurthook.py`, `hurt_sweep.py` | What is hurting Crash, and which objects in a level hurt on contact |
| `make_cortex_state.py` | Cortex levels need Cortex: boot, skip the classroom scene, then warp |

## The level warp

There is no debug warp in the game. The rig reuses the end-of-credits path: it writes a level path into the string
the credits code loads, cuts the credits to a single frame, and pushes the game-flow state machine into "credits
finished". About 1.5 s of that path is included in every load-time measurement.

## Things that will catch you out

- **A save state restores all of RAM**, including the executable. Anything that acts at boot, and any executable
  patch, must be tested from a fresh boot.
- **States embed the archive's file table.** Any level-data size change means rebuilding all of them.
- **`rebuild.py --levels X` deletes the other states** before rebuilding only the ones you named.
- **The warp keeps whichever character you are playing**, and a new game starts as Crash. A scene that waits for
  Cortex will wait forever - hence `make_cortex_state.py` and the `cortex` flag in `levels.txt`.
- **Story progress is read as a level loads**, so it has to be set *before* the warp: `progress=N` in `levels.txt`
  writes it to game-flow + 1284, bits 21-25.
- **A single warp timeout is usually a flake.** One level timed out once in fourteen rebuilds and passed on a retry.
- **But a *run* of warp timeouts means the game is wedged in the credits, and retrying can never fix it.** The warp
  works by forcing flow state 19 and making the credits finish on their first frame. If it times out, the branch is
  restored but the game is left sitting *in* state 19 - the real credits, forever - so every later attempt starts
  from there and fails. The tell is `flow_state == 19` with PINE perfectly healthy, which looks like a dead
  emulator but is not. Only a restart clears it. Check for it before warping.
- **Warp only once the game has reached the menu.** Warping at flow 5, while it is still settling, times out;
  waiting for flow 6-7 works. Flow 7 is the attract demo and warps fine.
- **The first warp after a cold boot does not land where later ones do.** It drops Crash at a default spawn rather
  than the level's own: `altdoc_c` puts him at `(-132.7, 1.6, 123.4)` on every warm warp and at `(4.8, -0.2, -38.0)`
  on the first one after boot. This has produced two wrong results in this project - slide-jump distances that
  would not reproduce, and an activation trace that reported objects 876 and 877 as *never activated* in a level
  where a warm warp shows both activated, because the cold warp had left Crash somewhere else entirely. **Warp
  once to throw the first one away, then warp again and measure.** The tell is a measurement that will not
  reproduce across boots while being perfectly stable within one.
- **There is one emulator, and `rig.py start` kills whatever is in it.** Two sessions driving the rig at once will
  silently corrupt each other's measurements - the symptoms are PINE timeouts, zeroed reads, and numbers that will
  not reproduce. The `re` ISO key gives separate *discs*, not separate *emulators*. If parallel work is needed, the
  real fix is a second PCSX2 instance on its own PINE port.
- **`rig.pos()` is ground-projected: its `y` does not move while Crash is airborne.** Reading it during a jump gives
  a flat line and makes a perfectly good jump look like it never happened. For anything off the ground use the
  player object's `+0x284` (height above ground) or `+0x064` (vertical velocity); the authoritative world position
  is the instance context's transform matrix `wColumn`, made current by `RotateAndTranslate`.
- **`0x309B68` is a frame counter,** +1 per game frame. Drive input off it rather than off wall-clock sleeps: a
  press measured in seconds is a different number of frames on the 50 Hz and 60 Hz builds, and wall-clock presses
  are not even repeatable at one rate. It also doubles as a check that the 60 Hz patch is live - it reads 50.00 Hz
  on the retail disc and 59.97 Hz on the modded build.
- **Crash clips scenery mid-run in the Earth hub,** deflecting his heading by 17° around frames 32-56 of a straight
  run from the warp spawn. It is deterministic, so it is easy to mistake for a physics result. Measure a heading
  over several windows and check it has settled before trusting it.
- **`--iso modded` is a locally built artifact and goes stale.** The repository ships no ISO, so that file is
  whatever `Build Modded ISO.bat` last produced on your machine - not the current source. Here it was built before
  three commits touched `mod/`, including the Tiki Mon contact-damage fix, so every rig run against it was testing
  an older build than the one the repository describes. **Compare its PCSX2 CRC against a fresh `test.iso` before
  trusting a measurement**: identical CRCs mean the same executable, and different ones mean the two differ
  somewhere. `rebuild.py` always builds `test.iso` from current source, which is why the state library is built
  from that and not from `[Modded]` - and it is why a state library and a stale `[Modded]` disagree.

- **A movie and an in-engine scene both letterbox, and a movie's skip proves nothing about a level recipe.**
  `in_cutscene()` reads the black bars, so it says "cutscene" for a pre-rendered movie as readily as for a scene
  the level data drives - and the executable patch already skips movies game-wide. Point a list entry at an FMV
  trigger and it reports a healthy `PASS` for a recipe that is doing nothing whatever: the Iceberg Lab interior
  gave **55.7 s → 4.0 s with its recipe built in and 55.7 s → 4.0 s without it**, and the `icelabint_*`
  screenshots left in `results/` are that movie rather than the scene anyone thought had been tested. The movie
  player's decoding flag `0x30A3C3` separates them cleanly - 1 throughout the Iceberg Lab FMV, 0 throughout
  Classroom Chaos - so `cutscene_test` now labels every run `movie` or `scene`.

  One trigger can play **both**, so the label alone is not enough and the run is timed in two parts. That split
  is what actually answers the question, and it answers it without a control build:

  | | Movie | In-engine scene | |
  |---|:-:|:-:|---|
  | `icelabint` (levels-wip) | 51.0 s → **0.0 s** | 4.6 s → 4.0 s | the saving is entirely the movie; the recipe does nothing |
  | `lab_psychetron` (shipped) | 7.8 s → 9.8 s | 16.7 s → **1.8 s** | the movie is not shortened at all; the recipe does all of it |

  So a movie in the run is not by itself a reason to distrust a verdict - `lab_psychetron` is sound - but a
  verdict whose whole saving sits in the movie column is evidence about the executable patch and nothing else.

- **Re-read object pointers before writing to them.** See the warning in [Executable patches](elf-patches).
- **Reference screenshots are build-specific.** The menu images used for waits were captured on the modded build and
  do not match the retail one closely enough; use fixed timings when booting the original ISO.

- **A regression list in the wrong format used to run nothing and say nothing.** `run_cutscenes.py` needs
  `NAME STATE X Y Z`, and `cutscenes.txt` is written `NAME STATE X Z` with no height - so all **11** scenes in it,
  the ones whose skip comes from the executable patch alone, were skipped by the same silent `continue` that
  filters out unwanted names. The runner now reports every line it cannot parse and ends with a count, because a
  run that reports nothing is not a run that passed. The heights have since been recovered from the level data -
  every trigger carries its own centre, so each entry was matched on X and Z and its Y read out - and all 11 now
  parse and run, taking coverage of the shipped skips from 14 to **25**. One entry matched its trigger 1.2 units
  out rather than the usual 0.05; that turned out to be a director with two triggers, both at the same height, so
  the value was safe either way.

## A typical session

```bash
cd tools/rig
python rebuild.py                                                # test ISO + 34 fresh states (~18 min)
python run_cutscenes.py cutscenes_orphan.txt                     # every restored skip, full vs skipped
python cutscene_test.py classroom crgpa08 6.60 2.08 -20.58       # one of them
python fmv_test.py Levels\Ice\Hub\labint -14.34 -2.85 -10.33 hold
RIG_FASTCDVD=true python load_bench.py fast
```

Environment switches: `RIG_PATCH=ADDR=WORD,...` applies executable patches from boot, plus `RIG_FASTCDVD`,
`RIG_RENDERER` (13 = software), `RIG_EE_RATE` and `RIG_UPSCALE`.

## The baseline

First run of all 25 shipped skips together, from a state library built entirely from the current source:

| | Count | |
|---|:-:|---|
| **PASS** | 15 | gameplay returns sooner, player ends up in the same situation |
| **CHECK** | 7 | a difference a human has to judge - all of them explained |
| **NOT TRIGGERED** | 3 | `sentry`, `dingodile_hut`, `ngin_switch` - the scene never started |

The CHECKs are not failures. `totem_falling` reports 21.5 s against 21.2 s, which looks like a skip that does
nothing and **is exactly right**: that scene is [deliberately left unskippable](what-changed) because skipping drops
Crash into the totem chase before it is set up. `henchmania` reports the skip taking *longer* than the full scene,
which is the follow-on Brio/Tropy scene chaining on - the measurement stops when gameplay resumes, and a second
scene delays that. The rest are end-position differences already documented as legitimate.

The three NOT TRIGGERED turned out not to be cutscenes at all. Their coordinates are accurate - each sits on a
real trigger to within 0.06 - but those triggers target **actors**: `act_SENTRY_TRIBESMAN`,
`act_BATTLESHIP_NGIN_SWITCHTHROWER`, and an actor inside gpa01's Dingodile-hut group. None of the three levels
contains a cutscene director at all, checked both by the survey and by searching their object tables directly. So
the entries were wrong when they were written, and the silently-skipped list is why nobody found out. They are
commented out with the reason, leaving **22** entries that all mean something.

## What a verdict looks like

```text
classroom:
  full : {'seconds': 11.5, 'pos': (...), 'flow': 12}
  skip : {'seconds': 4.1,  'pos': (...), 'flow': 12}
  => CHECK: 11.5s -> 4.1s, end position 5.8 apart, flow 12 vs 12
```

`PASS` means gameplay came back sooner and the player ended up in the same situation. `CHECK` means something differs
and a human has to look - in Classroom Chaos the character legitimately stands a few steps from where the full scene
leaves them. Verdicts are appended to `results/summary.txt`, which is what makes "is this a regression, or has it
always been like that?" an answerable question.
