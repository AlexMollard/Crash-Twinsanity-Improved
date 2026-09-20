---
id: graphics
title: Graphics
sidebar_position: 9
---

# Graphics

## Shadows

Characters cast a real silhouette shadow: one small volume per bone, projected straight down, collected into
per-chunk record lists (`0x1CB158`) and drawn into a screen-space mask in DMA chain slot `0x15` (`0x1F1A10`).

The mask is then applied **only** to pixels whose material has the GS *alpha correction* flag (FBA) set. That flag is
what marks a surface as a shadow receiver. Level scenery has it on. Characters have it off, so they do not shadow
themselves.

Most crate materials were given the character settings, so Crash's shadow never fell on a crate - which matters,
because a shadow is how you judge where you will land. `tools/materials.py` switches the flag on for every opaque
crate material in every level: 580 shaders across 89 level files, one byte each, no size change.

Every lift, bridge, ice floe, hovering platform, boat and holo-platform in the game already had the flag on. Apart
from crates, the only things without it are characters, enemies, doors and walls.

## 480p / 60 Hz

The output patch (by PeterDelta) changes two words in `sceGsResetGraph` to select DTV 480p and frame mode instead of
PAL interlaced. On real hardware that needs a 480p-capable connection - over SCART or composite to a PAL TV you get
no picture.

Switching the output to 60 Hz on its own leaves two things out of step, both of which the mod fixes:

- the game clock still said 50, which broke the loader's frame budget - see [Loading](loading),
- the movie player still showed a frame every second vsync, which ran movies 20% fast - see [Movies](movies).

## The GS side, in brief

Materials carry the DMA chain slot they draw in (`Material.Unknown` in the editor library) and a shader with the GS
register settings, FBA among them. `twinsdump objgfx` lists an object's materials and shaders, which is how the crate
survey was done.
