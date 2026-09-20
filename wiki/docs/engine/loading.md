---
id: loading
title: Loading and streaming
sidebar_position: 7
---

# Loading and streaming

Entering a level streams 15 to 25 MB out of `CRASH.BD` - the level itself plus the neighbouring areas the game keeps
resident. Three separate things made that slow, and the mod addresses all three.

## The loader

```text
0x17DDC8   background loader, called once per frame
   │
   ├─ 0x2ABB48   flush queued commands to the IOP   (once per pass)
   │
   └─ 0x2AB150   chunk manager step, looped while it makes progress
                 G_ChunkLoadingManager_ = *(0x309AD8)
                 word 0: bits 0-11 "wanted", bits 12-23 "done"
```

The loader also has a frame budget, taken from the game clock at `0x192360`.

## Reads waited for the next frame

The chunk manager queued disc reads and the loader only pushed the queue to the IOP **once per frame**. Every read
therefore cost at least a frame even when the drive was idle. A 14-instruction stub in the code cave now flushes the
queue before each chunk-manager step instead, hooked at `0x17DE40`. That was the single biggest win.

Two other ideas were measured and dropped: spinning the outer loop while reads are pending gained nothing, and a
512 KB read buffer gained about half a second (2 MB broke the boot - it is heap).

## The data was on the slow part of the disc

See [the archive page](archive): `CRASH.BD` now lives at the outer edge.

## Emulated drive speed

PCSX2's *Fast CDVD* halves emulated read times; the mod's game settings turn it on. It is a per-game setting, so it
can be switched off in the game's properties.

## Results

Measured with the rig, from its level warp until Crash can move, on a fresh boot (each figure includes about 1.5 s of
the warp's own credits path):

| Level | Retail | Modded ISO | Modded ISO + Fast CDVD |
|---|:-:|:-:|:-:|
| Earth hub (`huba`) | 9.5 s | 7.0 s | 5.5 s |
| Classroom Chaos (`crgpa08`) | 16.0 s | 10.5 s | 8.0 s |

The first two changes are changes to the disc image, so they should help on real hardware too - though that has not
been tested. What is left is mostly the drive: reads arrive 128 KB at a time, quantised to frames.

## Frame timing

The 480p / 60 Hz patch switches the output to 60 Hz, but the game still set its internal frame rate from the PAL
region flag - 50. That number is used for exactly one thing: how much of each frame the background loader may use.
Believing a frame lasted 20 ms instead of 16.7 ms, the loader overran wherever it stayed busy, and roughly every
fifth frame was shown twice.

One word at `0x17D6F0` sets it to 60. In the Earth hub, 57-61 of 300 frames were doubled before and 1 of 360 after.
