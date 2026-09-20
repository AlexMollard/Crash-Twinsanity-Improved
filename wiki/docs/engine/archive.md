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

Inside the archive each level is `<path>.rm2` (the level) and `<path>.sm2` (its sounds). An `.rm2` is a container of
numbered items in sections.

:::warning Never re-save a whole level
The Twinsanity Editor library's full save drops about 134 bytes of not-yet-understood data per level. The build
instead splices **individual items** back into the original bytes (`tools/rig/rm2splice.py`), so everything it does
not touch stays exactly as it shipped.
:::

## Save states and the file table

The test rig's PCSX2 save states contain the whole of RAM, and RAM contains the archive's file table as it was when
the state was made. If a level file changes size, every saved state is stale: the game will look for level data at
offsets that have moved.

So the rule is: **any change to level data means rebuilding the whole state library** (`tools/rig/rebuild.py`, about
18 minutes). Executable-only changes are worse in a different way - a save state restores the old code with it, so
patches have to be tested from a fresh boot.
