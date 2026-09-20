---
id: movies
title: The movie player
sidebar_position: 8
---

# The movie player

The pre-rendered movies are `.PSS` files streamed straight off the disc, played by a controller object that runs
alongside the game loop.

```text
G_GameMovieController = *(0x309AC0)
  bitfield >> 12 & 0xF   1 = starting, 2 = playing, 3 = stop requested
  +0x1E4                 decoded-frame counter (handy for measuring the real frame rate)

0x2AF958   per-frame step: asks the player object whether it is still running,
           and shuts it down through the player's own stop path when it is not
0x2B0170   "advance one displayed frame": decodes until the vsync callback presents one
0x2AFDE8   vsync callback - presents a frame and sets the "shown" flag
0x1A0448   present
```

The three bytes the vsync callback works with: `0x30A3C1` "a frame was shown", `0x30A3C2` the every-other-vsync
accumulator, `0x30A3C3` "the movie loop is waiting for a frame".

## Speed

The player showed a new frame on every **second** vsync. At PAL's 50 Hz that is 25 fps, which is what the movies are
authored at - but with the 480p / 60 Hz patch it became 30 fps, a fifth too fast, against audio that kept its own
pace.

The callback now jumps to a stub that counts in fifths: +5 per vsync, one frame per 12, which is exactly 25 fps at
60 Hz. It keeps counting while the loop is still decoding, as the original flag did.

Measured with the player's own decoded-frame counter: the two boot movies went from 30.1 and 29.7 fps to 25.0 and
24.7. The original disc at 50 Hz plays them at 25.1 and 24.8.

## Stopping a movie early

In the retail PAL game a movie stops for **✕**, after about a second - and for nothing else. Every other skip in this
mod is hold-△, so the mod makes movies answer that too.

`0x2AF958`'s "is it still running?" answer now goes through a stub. The stub reads the Triangle pressure the same way
script condition 575 does - `GetButtonPressure(G_GameController->mainGamePad, 4)` at `0x2B2250` - and reports
"finished" once it has been held for 30 frames. The movie then stops down its own ending path and the script that
started it carries on exactly as if it had played out. ✕ is untouched.

Measured at the Iceberg Lab door from a fresh boot: 54.2 s untouched, 1.8 s with △ held, 6.8 s with ✕ - the same as
the original disc's 7.0 s.

:::tip Telling a movie from a scene
If a "cutscene" will not respond to any script edit, check whether it is a movie. Watch the decoded-frame counter at
`G_GameMovieController + 0x1E4`: if it is climbing, you are looking at video, and no amount of script surgery will
change it.
:::
