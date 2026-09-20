"""The executable side of the mod: word patches, and a code cave big enough to actually write code in.

Crash Twinsanity's SLES_525.68 is a plain 32-bit MIPS ELF with a single loadable segment:

    PT_LOAD  file 0x1000  vaddr 0x100000  filesz 0x20a460  memsz 0x2db200

so 0x100000-0x30a460 comes off the disc (.text, .vutext, .data, .rodata, .sdata) and 0x30a460-0x3db200 is
zeroed storage (.sbss, .bss). The entry point clears exactly that second range and then calls InitHeap with
0x3db200 - the linker's `_end` - as the base of the heap, with no size limit, so every byte of the console's
remaining 28 MB belongs to the game's allocator from boot onwards.

That makes the top of `_end` the one place in the address map that is nobody's: past the range the boot code
zeroes, and below the heap only because a single `addiu` in the entry point says so. CAVE_BASE puts our code
there, a second PT_LOAD loads it, and `heap_base` moves the game's allocator up by the same amount. The cave
survives the bss clear, no game data moves, and no existing address changes.

Before this, patches had to squeeze into an unused debug function at 0x116ea8 - 0x130 bytes, about 75
instructions, and by the time cutscene skipping, 60 Hz frame timing and movie pacing were in, it was full.
"""
import struct

ELF_BASE = 0x100000
CAVE_BASE = 0x3DB200            # `_end`: above the bss the entry point clears, below the heap once it is moved
CAVE_SIZE = 0x2000              # 8 KB reserved whatever we use, so cave addresses do not move between builds

HEAP_BASE_INSN = 0x1000A0       # in entry(): addiu a0, a0, -0x4e00 -> a0 = 0x3db200, the InitHeap base
HEAP_BASE_ORIG = 0x2484B200


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
        """Load CODE at BASE and move the game's heap up past it."""
        if len(code) > size: raise SystemExit(f"cave code is {len(code)} bytes, the cave is {size}")
        self.heap_base(base + size)
        self.add_segment(base, bytes(code).ljust(size, b"\0"))

    def heap_base(self, addr):
        """Repoint the InitHeap call in entry() at ADDR (the immediate is added to 0x3e0000)."""
        delta = addr - 0x3E0000
        if not -0x8000 <= delta < 0x8000: raise SystemExit(f"heap base {addr:08X} too far from 0x3e0000")
        self.patch(HEAP_BASE_INSN, HEAP_BASE_ORIG, (HEAP_BASE_ORIG & 0xFFFF0000) | (delta & 0xFFFF), "heap base")

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
