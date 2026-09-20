---
id: overview
title: What is on the disc
sidebar_position: 1
---

# What is on the disc

The PAL disc is a plain DVD with an ISO 9660 filesystem and a UDF bridge on top. Both directories describe the same
files, and the build has to keep them in agreement - see [the archive page](archive).

```text
/SLES_525.68          2.05 MB   the executable (a PS2 ELF)
/SYSTEM.CNF                     tells the console which file to boot
/CRASH6/CRASH.BD    886.84 MB   every level, packed end to end
/CRASH6/CRASH.BH      0.03 MB   the index: name, offset and length of each file inside CRASH.BD
/CRASH6/MUSIC.MB    211.50 MB   streamed music
/CRASH6/ENGLISH.MB   12.56 MB   speech, one bank per language (also FRENCH, GERMAN, ITALIAN, SPANISH)
/CRASH6/SYS/*.IRX               IOP modules the game uploads at boot
/FMV/*.PSS                      the pre-rendered movies, 8 to 155 MB each
```

## The archive

`CRASH.BD` is a flat blob and `CRASH.BH` is its table of contents: a list of names with an offset and a length. The
game only ever looks files up **by name**, which is why the build can move the whole archive to the outer edge of the
disc for [faster loading](loading) without breaking anything.

Inside the archive, each level is two files:

| | |
|---|---|
| `Levels\Earth\Hub\hubd.rm2` | the level itself - models, textures, animations, collision, objects, instances, scripts |
| `Levels\Earth\Hub\hubd.sm2` | the level's sound bank |

Paths use backslashes and are matched case-insensitively.

## Inside a level (`.rm2`)

An `.rm2` is a container of **items**, each with a numeric id, grouped into sections. The
[Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) library reads and writes this format, and this
project drives it through [`twinsdump`](../modding/recipes).

The sections this mod cares about:

| Section | What it holds |
|---|---|
| **Scripts** | The state machines that drive everything. Two items per behaviour: a small header, and the `COM_` item with the actual states. See [Scripts](scripts). |
| **Game objects** | Object *types*: a name, a list of script slots, and the models, animations and sounds they use. See [Objects](objects). |
| **Instances** | Placements of an object in the level: a position, a rotation and the object id. |
| **Triggers** | Boxes in the world that activate or message objects when the player enters them. |
| **Graphics** | Models, materials and shaders, including the flag that decides whether a surface receives Crash's shadow. See [Graphics](graphics). |
| **Collision, AI graphs, paths** | The level's collision mesh and the node graphs enemies walk along. |

:::tip Names survive
Every object and script keeps the name the developers gave it - `COM_TIKI_MON_ACTIVATED`,
`|LabInt|H02B_Cutscene|act_ICELABINT_CUTSCENE_DIRECTOR`. Those names are the single most useful thing in the whole
format; almost all of this wiki was found by reading them.
:::

## The executable

`SLES_525.68` is a 2 MB ELF that the PS2 loads at virtual address `0x100000`. The mapping from a file offset to a
virtual address is:

```text
file offset = virtual address - 0x100000 + 0x1000
```

PCSX2 identifies a game by a CRC over that executable, so any change to it produces a new CRC and needs a matching
`.pnach`. The build regenerates that automatically. See [The executable](executable).

## How the pieces line up at runtime

```text
 SLES_525.68 ─ engine, script interpreter, renderer, loaders
      │
      ├─ reads CRASH.BH once, then streams chunks out of CRASH.BD as you move
      │
      ├─ each level's .rm2 becomes:   objects ─ instances ─ triggers
      │                                   │
      │                                   └─ scripts: one state machine per running behaviour
      │
      └─ movies stream straight off the disc from /FMV/*.PSS
```
