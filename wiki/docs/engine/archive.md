---
id: archive
title: The archive and the disc
sidebar_position: 5
---

# The archive and the disc

## CRASH.BD / CRASH.BH

`CRASH.BD` is one 887 MB blob holding every level file end to end. `CRASH.BH` is its index: for each entry, a name
and where to find it. The game resolves files **by name**, never by position, which is what makes the layout changes
below safe.

Originally `CRASH.BD` had about 2 KB of slack at the end, so any level edit that made a file bigger had to be paid
for by making another one smaller. The build now sidesteps that entirely.

## Moving the archive to the outer edge

A PS2 drive spins a DVD at a constant angular speed, so the outer edge reads up to 2.5x faster than the inner edge.
PCSX2 models this: its read speed is `0.40 + 0.60 x LBA / 2298496`. `CRASH.BD` started 225 MB into the disc, in the
slow half.

The build now moves it to the end of the image and packs the 39 files that followed it (speech banks, IOP modules,
movies) down into the space it used to occupy. The image stays exactly the same size, `CRASH.BD` can grow as much as
it likes, and both directories are rewritten to match.

![Disc layout before and after: CRASH.BD starts 225 MB in, on the slow half; the build moves it to the outer edge and packs the files that followed it into the gap, without changing the image size](/img/disc-layout.svg)

This is `isotools.archive_last()`, run as the "Disc layout" step of `tools/build_mod.py`.

## Keeping ISO 9660 and UDF honest

The disc carries two directory structures describing the same files. Change a file's position or size and **both**
have to be updated, along with UDF's file entry lengths and the anchor that records the end of the image.
`tools/verify_iso.py` checks a finished build:

- ISO 9660 and UDF agree on every file's position and length,
- UDF descriptor tags and checksums are valid,
- no two files overlap and nothing runs past the end of the image,
- every file the build did not intend to touch is byte-identical to the original.

## Level files

Inside the archive each level is `<path>.rm2` - scripts, objects, instances, triggers, characters and collision - and
`<path>.sm2`, the scenery: its models, materials, textures, the skydome and the level's lights (see
[Lighting](lighting)). There are 135 of the first and 134 of the second. Both are containers of numbered items in
sections.

:::warning Prefer splicing to re-saving a whole level
The Twinsanity Editor library's full save used to be badly lossy, and two bugs have since been found and patched:

- a **texture** field was read and not written back, which is where "it drops about 134 bytes per level" came from
- `CollisionSurface` is asymmetric - it reads a `ushort` but writes a 4-byte `int` into a 114-byte slot, so every
  surface overruns the next by two and the file comes back the same size with scrambled tails. 452 bytes of damage
  across 161 surfaces in `labext` alone, and it silently corrupted collision on any level saved through the GUI.
- **particle names** are a fixed 16-byte field; the reader stopped at the terminator and the writer padded the rest
  with zeros, losing the tail of whatever longer name had been there.

All three are the same mistake in different clothes - a field read and not kept, written back as zeros - and all
three are patched in `tools/patches/`, applied to the submodule by the build:

| | files that round-trip byte for byte |
|---|:-:|
| unpatched | 1 of 135 |
| + texture fix | 98 of 135 |
| + collision fix | 98 of 135 (it repairs layout, not a dropped value) |
| + particle fix | **135 of 135** |

So the library is now lossless on every file in the archive. The build still splices **individual items** back into
the original bytes (`tools/rig/rm2splice.py`) rather than re-saving, and that remains the safer choice for changing
one field in one script - but it is no longer the *only* safe path, and whole-file authoring is now on the table.
:::

## Save states and the file table

The test rig's PCSX2 save states contain the whole of RAM, and RAM contains the archive's file table as it was when
the state was made. If a level file changes size, every saved state is stale: the game will look for level data at
offsets that have moved.

So the rule is: **any change to level data means rebuilding the whole state library** (`tools/rig/rebuild.py`, about
18 minutes). Executable-only changes are worse in a different way - a save state restores the old code with it, so
patches have to be tested from a fresh boot.
