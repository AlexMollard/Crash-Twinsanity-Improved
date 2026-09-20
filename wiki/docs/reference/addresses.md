---
id: addresses
title: Addresses
sidebar_position: 2
---

# Addresses

All virtual, for **PAL SLES-52568 v1.01** (original PCSX2 CRC `1510E1D1`). They are meaningless on any other build.

```text
file offset = virtual address - 0x100000 + 0x1000
gp          = 0x311870        (so a gp-relative -32740 is *(0x30988C))
```

## Globals

| Address | What |
|---|---|
| `0x30988C` | game-flow / game-controller object. Flow state = `(*(obj+12) >> 12) & 0x3F`; `+0x3C` is player 1's pad; `+1284` bits 21-25 are story progress |
| `0x3098FC` | player context (used by the hurt-flicker code) |
| `0x309908` | player character object. `+16` bit 10 = invincible, `+20` bits 6-13 = health (masks + 1) |
| `0x309AC0` | `G_GameMovieController`. `+0x1E4` = decoded-frame counter |
| `0x309AC8` | game clock controller. `+0x68` fps, `+0x70` tick rate (576000/s) |
| `0x309AD8` | chunk loading manager. Word 0: bits 0-11 wanted, bits 12-23 done |
| `0x30A3C1` | movie: a frame was shown |
| `0x30A3C2` | movie: vsync accumulator |
| `0x30A3C3` | movie: the loop is waiting for a frame |
| `0x30BE90` | the level-path string the end-of-credits code loads (the rig's warp target) |
| `0x2EC530` | script command factory table, indexed by command id |
| `0x2F0AB8` | script condition check table |

## Memory

The game uses essentially all of the console's 32 MB and leaves **8 KB spare**. Two allocations account for almost
all of it, and anything added to the executable has to be paid for out of one of them.

| Address | What |
|---|---|
| `0x309B18` | General pool pointer |
| `0x309B1C` | Streaming buffer pointer |
| `0x2EABE4` | The `sbrk` break |

| Allocation | Site | Size |
|---|---|---|
| General pool | `GetHeapManager_` `0x181DB0` | `0x00B7E890` (11.5 MB) |
| Streaming buffer | `GetDiskManager_` `0x181E58` | `0x010A3D70` (16.6 MB) |

On the retail disc at the title screen the pool sits at `0x3DB210`, the streaming buffer ends at `0x01FFD820`, the
break is at `0x01FFE000` and RAM ends at `0x02000000`. Growing the executable without shrinking one of those two
makes the *second* allocation overrun the end of the heap: `sbrk` returns -1, `malloc` returns null, and the graphics
init at `0x1AF150` writes its structure through the null pointer - which shows up in PCSX2's log as TLB misses
storing to `0x0`, `0x4`, `0x8` … immediately after the 480p mode change, and a black screen.

## Functions

| Address | What |
|---|---|
| `0x106C40` | `BuildScriptCondition` |
| `0x116EA8` | Unused debug function - the mod's [code cave](../engine/executable#the-code-cave), now full |
| `0x12C588` | Condition 572's original "return 0.0" stub |
| `0x12C648` | Condition 575 - player *param* holds Triangle |
| `0x1315E0` | Hurt-flicker / grace-period update, once per frame |
| `0x1317F8` | Player state reset - called when a cutscene takes or returns control |
| `0x137510` | The player's damage handler. Info struct: flags at `+0x10` (2 = explosion), amount at `+0x14` |
| `0x13E010` | "Something touched the player": decides whether it hurts, on the toucher's helper flags bit 8 |
| `0x13E1C8` | Builds the contact hit (flags `0x400`, damage 1) and calls the damage handler |
| `0x13F9A0` | Third mask: sets invincible for 8 seconds |
| `0x17D6F0` | Game clock creation - where the PAL 50 came from |
| `0x17DDC8` | Background loader, once per frame |
| `0x178150` / `0x178290` | Cutscene take control / return control |
| `0x192360` | Loader frame budget |
| `0x1A0448` | Present |
| `0x1CB158`, `0x1F1A10` | Shadow volume lists and the screen-space shadow pass |
| `0x2AB150` | Chunk manager step |
| `0x2ABB48` | Flush queued IOP commands |
| `0x2AF958` | Movie player per-frame step |
| `0x2AFDE8` | Vsync callback |
| `0x2B0170` | Movie: advance one displayed frame |
| `0x2B2250` | `GetButtonPressure(pad, button)` - 4 is Triangle; returns the raw 0-255 pressure in `v0` |
| `0x2B4FD0` | `ReadSections_` |
| `0x2C24A8` | `sceGsResetGraph` - the 480p patch site |

## Rig scratch RAM

| Address | What |
|---|---|
| `0xFF000` / `0xFF004` | Virtual pad enable / raw pad bytes |
| `0xFF100` | The pad hook's cave |
| `0xFF200` | The warp path string |
| `0xFF400` | `hurthook` ring buffer |
| `0xFF600`, `0xFF700` | Scratch caves for live hooks |
