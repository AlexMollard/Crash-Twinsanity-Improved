"""ISO / archive helpers for the Crash Twinsanity PAL disc (SLES-52568): ISO9660 directory, the CRASH.BD/BH
archive, the SLES_525.68 executable and PCSX2's game CRC."""
import array, os, struct

SECTOR = 2048
ELF_PATH = "/SLES_525.68"
ELF_BASE, ELF_FILE_OFF = 0x100000, 0x1000        # single PT_LOAD segment: file offset = vaddr - 0x100000 + 0x1000
ORIGINAL_CRC = "1510E1D1"                         # untouched PAL disc

def iso_files(f):
    """{'/DIR/NAME': (lba, size, directory_record_offset)} for every file on the disc."""
    f.seek(16 * SECTOR); pvd = f.read(SECTOR); root = pvd[156:190]; out = {}
    def walk(lba, size, path):
        f.seek(lba * SECTOR); data = f.read(size); i = 0
        while i < len(data):
            n = data[i]
            if n == 0: i = (i // SECTOR + 1) * SECTOR; continue
            rec = data[i:i + n]; elba, esz = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
            name = rec[33:33 + rec[32]]
            if name not in (b"\0", b"\1"):
                p = path + "/" + name.decode().split(";")[0]
                if rec[25] & 2: walk(elba, esz, p)
                else: out[p.upper()] = (elba, esz, lba * SECTOR + i)
            i += n
    walk(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "")
    return out

def read_file(f, files, path):
    lba, size, _ = files[path.upper()]; f.seek(lba * SECTOR); return f.read(size)

def pcsx2_crc(elf):
    """PCSX2's game CRC: XOR of the executable's 32-bit words."""
    words = array.array("I"); words.frombytes(elf + b"\0" * (-len(elf) % 4)); c = 0
    for w in words: c ^= w
    return f"{c:08X}"

def iso_crc(path):
    with open(path, "rb") as f: return pcsx2_crc(read_file(f, iso_files(f), ELF_PATH))

def parse_bh(bh):
    """[[name, offset, size, record_offset_of_offset_field], ...] in archive order."""
    p, out = 4, []
    while p < len(bh):
        n = struct.unpack_from("<i", bh, p)[0]; name = bh[p + 4:p + 4 + n].decode("ascii")
        off, size = struct.unpack_from("<II", bh, p + 4 + n); out.append([name, off, size, p + 4 + n]); p += 12 + n
    return out

def archive_file(f, files, name):
    """Bytes of one file inside CRASH.BD (name as stored in CRASH.BH, case-insensitive)."""
    bh = read_file(f, files, "/CRASH6/CRASH.BH"); bd_lba = files["/CRASH6/CRASH.BD"][0]
    for n, off, size, _ in parse_bh(bh):
        if n.lower() == name.lower(): f.seek(bd_lba * SECTOR + off); return f.read(size)
    raise KeyError(name)

def patch_elf(f, files, patches):
    """patches: [(vaddr, original, new, note)]. Verifies every original word before writing anything."""
    lba, size, _ = files[ELF_PATH]; base = lba * SECTOR
    for va, orig, new, note in patches:
        f.seek(base + va - ELF_BASE + ELF_FILE_OFF); cur = struct.unpack("<I", f.read(4))[0]
        if cur != orig: raise SystemExit(f"executable {va:08X}: expected {orig:08X}, found {cur:08X} ({note}) - wrong source disc?")
    for va, orig, new, note in patches:
        f.seek(base + va - ELF_BASE + ELF_FILE_OFF); f.write(struct.pack("<I", new))

def rebuild_archive(src, dst, reps, log=print):
    """Rewrite CRASH.BD/BH in DST from SRC's archive with REPS {archive name: bytes} (sizes may change).
    Every file is streamed in original order; BH offsets and the ISO9660 size of CRASH.BD are updated."""
    files = iso_files(src)
    bh_lba, bh_size, _ = files["/CRASH6/CRASH.BH"]; bd_lba, bd_size, bd_rec = files["/CRASH6/CRASH.BD"]
    room = (min(l for l, _, _ in files.values() if l > bd_lba) - bd_lba) * SECTOR
    src.seek(bh_lba * SECTOR); bh = bytearray(src.read(bh_size)); entries = parse_bh(bh)
    reps = {k.lower(): v for k, v in reps.items()}
    unknown = set(reps) - {e[0].lower() for e in entries}
    if unknown: raise SystemExit(f"not in the archive: {sorted(unknown)}")
    total = sum(len(reps[e[0].lower()]) if e[0].lower() in reps else e[2] for e in entries)
    if total > room: raise SystemExit(f"archive would be {total} bytes but only {room} fit on the disc")
    pos = 0; dst.seek(bd_lba * SECTOR)
    for name, off, size, rec in entries:
        if name.lower() in reps:
            data = reps[name.lower()]; dst.write(data); log(f"  {name}: {size} -> {len(data)} bytes"); size = len(data)
        else:
            src.seek(bd_lba * SECTOR + off); left = size
            while left:
                chunk = src.read(min(left, 16 << 20)); dst.write(chunk); left -= len(chunk)
        struct.pack_into("<II", bh, rec, pos, size); pos += size
    dst.write(b"\0" * (room - pos))
    dst.seek(bh_lba * SECTOR); dst.write(bh)
    dst.seek(bd_rec + 10); dst.write(struct.pack("<I", pos) + struct.pack(">I", pos))
    log(f"  CRASH.BD {bd_size} -> {pos} bytes ({pos - bd_size:+d}), {room - pos} bytes of disc space left")
