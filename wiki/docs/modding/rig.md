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
- **Re-read object pointers before writing to them.** See the warning in [Executable patches](elf-patches).
- **Reference screenshots are build-specific.** The menu images used for waits were captured on the modded build and
  do not match the retail one closely enough; use fixed timings when booting the original ISO.

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
