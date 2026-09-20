"""The executable side of the mod: word patches, and a code cave big enough to actually write code in.

Crash Twinsanity's SLES_525.68 is a plain 32-bit MIPS ELF with a single loadable segment:

    PT_LOAD  file 0x1000  vaddr 0x100000  filesz 0x20a460  memsz 0x2db200

so 0x100000-0x30a460 comes off the disc (.text, .vutext, .data, .rodata, .sdata) and 0x30a460-0x3db200 is
zeroed storage (.sbss, .bss). Everything above 0x3db200 - the linker's `_end`, and 28 MB of it - is the game's
to allocate.

Which makes `_end` the one seam in the address map worth prying at, and three things decide what sits there:

  * the entry point zeroes the bss with 128-bit `sq` stores in a loop that tests before it increments, so it
    runs one store past `_end` and wipes 0x3db200-0x3db20f. CAVE_GUARD is that overshoot: code starts after it.
  * malloc gets its memory from sbrk (0x2cfcb0), whose break pointer is a single .data word at SBRK_BREAK,
    sitting in the image initialised to `_end`. Moving it is what actually reserves the cave - the game's
    11.5 MB pool is the first thing sbrk hands out, and without this it lands straight on top of our code.
  * entry() also calls InitHeap with `_end` as the base, which sets the ceiling sbrk checks against. Moving
    that too costs one word and keeps the two agreeing.

A second PT_LOAD then loads the cave off the disc. Nothing in the game moves and no existing address changes.

Before this, patches had to squeeze into an unused debug function at 0x116ea8 - 0x130 bytes, about 75
instructions - and cutscene skipping, 60 Hz frame timing and movie pacing had filled it.
"""
import struct

ELF_BASE = 0x100000
CAVE_BASE = 0x3DB200            # `_end`, where the segment is mapped
CAVE_GUARD = 0x10               # the boot-time bss clear overshoots this far past `_end`; nothing may live here
CAVE_SIZE = 0x2000              # 8 KB reserved whatever we use, so cave addresses do not move between builds
CAVE_CODE = CAVE_BASE + CAVE_GUARD

HEAP_BASE_INSN = 0x1000A0       # in entry(): addiu a0, a0, -0x4e00 -> a0 = 0x3db200, the InitHeap base
HEAP_BASE_ORIG = 0x2484B200
SBRK_BREAK = 0x2EABE4           # sbrk's break pointer, a .data word holding `_end` in the shipped image


class Elf:
    """The executable in memory, with the edits the build makes to it."""

    def __init__(self, data):
        self.data = bytearray(data)
        if self.data[:4] != b"\x7fELF": raise ValueError("not an ELF")
        self.phoff, = struct.unpack_from("<I", self.data, 28)
        self.phentsize, self.phnum = struct.unpack_from("<HH", self.data, 42)
        self.segments = [struct.unpack_from("<IIIIIIII", self.data, self.phoff + i * self.phentsize)
                         for i in range(self.phnum)]

    # ---------------------------------------------------------------- addresses
    def offset(self, vaddr):
        """File offset holding the byte at VADDR, or None if it is not backed by the file."""
        for p_type, off, va, _, filesz, _, _, _ in self.segments:
            if p_type == 1 and va <= vaddr < va + filesz: return off + vaddr - va
        return None

    def word(self, vaddr):
        return struct.unpack_from("<I", self.data, self.offset(vaddr))[0]

    def patch(self, vaddr, original, new, note=""):
        """Write one 32-bit word, refusing if what is already there is not ORIGINAL."""
        off = self.offset(vaddr)
        if off is None: raise SystemExit(f"executable {vaddr:08X}: not in a loadable segment ({note})")
        cur = struct.unpack_from("<I", self.data, off)[0]
        if cur != original:
            raise SystemExit(f"executable {vaddr:08X}: expected {original:08X}, found {cur:08X} ({note})"
                             " - wrong source disc, or two patches want the same word")
        struct.pack_into("<I", self.data, off, new)

    def write(self, vaddr, data):
        """Write bytes at VADDR (must already be file-backed)."""
        off = self.offset(vaddr)
        if off is None: raise SystemExit(f"executable {vaddr:08X}: not in a loadable segment")
        self.data[off:off + len(data)] = data

    # ---------------------------------------------------------------- the cave
    def add_segment(self, vaddr, data):
        """Append DATA to the file and map it at VADDR with a new PT_LOAD.

        The program header table sits at file offset 0x34 with room to spare before the first section at
        0x1000, so a second entry goes straight after the first one."""
        end = self.phoff + (self.phnum + 1) * self.phentsize
        first = min(off for t, off, *_ in self.segments if t == 1)
        if end > first: raise SystemExit("no room in the ELF header for another program header")
        off = len(self.data)
        self.data += data
        struct.pack_into("<IIIIIIII", self.data, self.phoff + self.phnum * self.phentsize,
                         1, off, vaddr, vaddr, len(data), len(data), 7, 0x10)   # PT_LOAD, rwx
        self.phnum += 1
        struct.pack_into("<H", self.data, 44, self.phnum)
        self.segments.append((1, off, vaddr, vaddr, len(data), len(data), 7, 0x10))

    def add_cave(self, code, base=CAVE_BASE, size=CAVE_SIZE):
        """Load CODE at BASE + CAVE_GUARD and move everything the game allocates up past the whole cave."""
        room = size - CAVE_GUARD
        if len(code) > room: raise SystemExit(f"cave code is {len(code)} bytes, the cave holds {room}")
        self.heap_base(base + size)
        self.add_segment(base, (b"\0" * CAVE_GUARD + bytes(code)).ljust(size, b"\0"))

    def heap_base(self, addr):
        """Move the bottom of the game's memory to ADDR: sbrk's break, and the ceiling InitHeap sets for it."""
        self.patch(SBRK_BREAK, CAVE_BASE, addr, "sbrk break pointer")
        delta = addr - 0x3E0000                        # entry() builds the base as lui 0x3e + addiu <delta>
        if not -0x8000 <= delta < 0x8000: raise SystemExit(f"heap base {addr:08X} too far from 0x3e0000")
        self.patch(HEAP_BASE_INSN, HEAP_BASE_ORIG, (HEAP_BASE_ORIG & 0xFFFF0000) | (delta & 0xFFFF), "InitHeap base")

    # ---------------------------------------------------------------- output
    def crc(self):
        """PCSX2's game CRC: XOR of the executable's 32-bit words."""
        import array
        w = array.array("I"); w.frombytes(bytes(self.data) + b"\0" * (-len(self.data) % 4))
        c = 0
        for x in w: c ^= x
        return f"{c:08X}"

    def __bytes__(self):
        return bytes(self.data)
