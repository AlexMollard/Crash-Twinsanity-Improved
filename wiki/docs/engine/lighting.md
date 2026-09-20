---
id: lighting
title: Lighting (and why not Phong)
sidebar_position: 10
---

# Lighting, and why not Phong

## Where the lights are

Not in the `.rm2`. Each level is two files, and the one this mod had never opened is the other one:

| | |
|---|---|
| `hubd.rm2` | scripts, objects, instances, triggers, characters, collision |
| `hubd.sm2` | **the scenery**: its models, materials, textures, LOD models, the skydome - and the lights |

The lights live in a single `SceneryData` item per scenery file, in four lists: **ambient**, **directional**,
**point** and **negative**. Each light carries a colour (RGB plus a fourth channel), a radius, a position and two
direction vectors.

```bash
twinsdump Levels/Earth/Hub/huba.sm2 lights -v
```

```text
scenery 0 levels\earth\hub\huba: ambient 1, directional 2, point 4, negative 0
    ambient     rgb (0.33, 0.33, 0.33)  radius 4.5     at (136.6, -1.5, -50.9)
    directional rgb (0.56, 0.44, 0)     radius 5.37    at (136.4, -1.5, -50.6)
    directional rgb (0.24, 0.26, 0.5)   radius 5.05    at (136.4, -1.5, -50.6)
    point       rgb (0.41, 0.39, 0.2)   radius 146.53  at (-3.3, 8.6, -24.7)
    point       rgb (0.41, 0.39, 0.2)   radius 146.53  at (-42.2, 8.6, 37.4)
    point       rgb (0.41, 0.39, 0.2)   radius 146.53  at (-55.3, 8.6, 97.3)
    point       rgb (0.41, 0.39, 0.2)   radius 146.53  at (-57.4, 10.9, 136.2)
```

That is a proper little lighting rig: a grey ambient, a warm key and a cool fill, and four wide point lights walking
up the hub to keep the ground from going flat. It is not baked - these are evaluated at runtime.

## What the game uses, across all 134 scenery files

| | Total | Notes |
|---|:-:|---|
| Ambient | 140 | Essentially one per file |
| Directional | 432 | The workhorse - up to 10 in one file |
| Point | 103 | Wide radii, used to shape hubs and arenas |
| Negative | 11 | Supported, and almost never used |

The most common rig by far is **one ambient and two directional** (42 files), then one and five (27), one and four
(21). Eleven files have no directional or point light at all - `labint`, `altlabin`, `airship`, the Psychetron
corridors - and those interiors lean on ambient plus a handful of *negative* lights instead, which subtract light to
carve out shadowed pockets.

## Why Phong is not on the table

Short version: the PlayStation 2's Graphics Synthesizer has **no programmable per-pixel stage at all**. Gouraud is
not a setting the game picked over Phong; it is one bit in the GS primitive register (`IIP`), and the only other
value is flat. Every one of the game's 10,464 material shaders already asks for gouraud, so there is nothing to turn
up.

Lighting happens **per vertex**, on VU1, before the triangle ever reaches the rasteriser. The lights above are
transformed and accumulated into a colour per vertex, and the GS then interpolates those colours across the triangle.
That interpolation *is* Gouraud shading, and it is the only shading the hardware does.

Getting per-pixel lighting on a PS2 means faking it with multiple passes - lookup-table normal maps, projected light
textures, that family of tricks. In practice that would mean rewriting the VU1 microprogram, adding two or three
passes over every surface, and paying for it in fill rate on hardware that this mod has just finished getting to a
steady 60 fps. It is not a patch; it is a different renderer.

:::tip What is actually available
The lighting *data* is completely open, and this mod has never touched a single `.sm2` file. Colours, radii,
positions, the number of lights and the unused negative lights are all editable, and none of it costs anything at
runtime. If the goal is "the game looks better lit", that is the lever - not a shading model the hardware cannot
run.
:::

## The shadow pass is separate

Character shadows are not part of this lighting at all - they are a screen-space mask pass, described in
[Graphics](graphics). The receiver set is settled: after the crate fix, everything still excluded is a character or a
boss, which cast the shadow volumes themselves and would shadow themselves if included. A test build that made all
3,218 remaining opaque materials receivers was indistinguishable from the shipped 580 at every spot checked.
