---
id: build
title: Building the ISO
sidebar_position: 1
---

# Building the ISO

`tools/build_mod.py` turns an untouched disc image into a patched one. It never writes to the source, and it is
deterministic: the same inputs give the same output, so the build is the only place changes exist. Nothing is ever
hand-patched into an ISO.

```bash
python tools/build_mod.py                              # find the original by CRC, write "<name> [Modded].iso"
python tools/build_mod.py --src my.iso --out out.iso
python tools/build_mod.py --include tools/rig/testops  # add extra recipes (test-only ones, say)
python tools/verify_iso.py original.iso modded.iso     # check the result
```

## The steps

1. **Tools.** Build `twinsdump` if its source is newer than the binary.
2. **Level edits.** Apply every `mod/levels/*.ops` recipe (plus any `--include` directories, plus
   `mod/skip_prompt.ops` last) to the original `.rm2` files, and splice the edited script items back in.
3. **Text.** Apply `mod/text.txt` to the language files - that is where the "hold △ to skip" string comes from.
4. **Materials.** Switch the shadow-receiver flag on for crate materials (`tools/materials.py`).
5. **Executable patches.** Apply `mod/elf_patches.txt`, checking every original word first.
6. **Disc layout.** Move `CRASH.BD` to the end of the image and pack the files that followed it down into its old
   place, updating ISO 9660 and UDF.
7. **Rebuild `CRASH.BD` / `CRASH.BH`** with the edited level files, and write the `.pnach` for the new CRC.

Each step prints what it changed, including the byte delta for every level file - which is the quickest way to spot a
recipe that did nothing.

## Why a recipe and not a patched file

Level files are large and mostly opaque. Keeping the *edit* rather than the *result* means:

- the repository contains no game data,
- a change can be read and reviewed as four lines of text,
- the same recipes can be applied to a freshly dumped disc, or to a different build, and will fail loudly rather than
  silently corrupt if the data underneath is not what was expected.

## What the ISO ends up with

- Executable patches for the skip, the fixes and the timing changes.
- Level recipes for the scenes whose skip wiring was cut, and for the contact-damage fix.
- The skip prompt in five languages.
- Crate materials marked as shadow receivers.
- `CRASH.BD` at the fast edge of the disc.

Everything else on the disc is byte-identical to the original, and `verify_iso.py` proves it.
