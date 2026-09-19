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

def patch_archive_bytes(f, patches):
    """patches: {archive name: {offset in file: byte}} applied in place in the image's CRASH.BD (sizes unchanged)."""
    files = iso_files(f); bd_lba = files["/CRASH6/CRASH.BD"][0]
    where = {n.lower(): (off, size) for n, off, size, _ in parse_bh(read_file(f, files, "/CRASH6/CRASH.BH"))}
    for name, changes in patches.items():
        off, size = where[name.lower()]
        for o, b in changes.items():
            if o >= size: raise SystemExit(f"{name}: patch offset {o} outside the file")
            f.seek(bd_lba * SECTOR + off + o); f.write(bytes([b]))

def _udf_crc(data):
    """CRC-16/CCITT (poly 0x1021, init 0) as used by UDF descriptor tags."""
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8): crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def _udf_write(f, sector, d):
    """Recompute a UDF descriptor's tag CRC and checksum, then write it back."""
    n = struct.unpack_from("<H", d, 10)[0]
    struct.pack_into("<H", d, 8, _udf_crc(d[16:16 + n]))
    d[4] = sum(d[i] for i in range(16) if i != 4) & 0xFF
    f.seek(sector * SECTOR); f.write(d)

def _read_sector(f, sector): f.seek(sector * SECTOR); return bytearray(f.read(SECTOR))

def udf_layout(f):
    """The disc's UDF bridge: (partition start, [partition descriptor sectors], {partition-relative lba: file entry sector})."""
    avdp = _read_sector(f, 256)
    if struct.unpack_from("<H", avdp, 0)[0] != 2: return None
    pds, start = [], None
    for ln, loc in (struct.unpack_from("<II", avdp, 16), struct.unpack_from("<II", avdp, 24)):   # main and reserve sequence
        for s in range(loc, loc + ln // SECTOR):
            d = _read_sector(f, s); tag = struct.unpack_from("<H", d, 0)[0]
            if tag == 5: pds.append(s); start = struct.unpack_from("<I", d, 188)[0]
            if tag == 8: break
    first_file = min(l for l, _, _ in iso_files(f).values())
    fes = {}
    for s in range(start, first_file):
        d = _read_sector(f, s)
        if struct.unpack_from("<H", d, 0)[0] == 261 and (struct.unpack_from("<H", d, 34)[0] & 7) == 0:   # file entry, short_ad
            l_ea, l_ad = struct.unpack_from("<II", d, 168)
            if l_ad == 8: fes[struct.unpack_from("<I", d, 176 + l_ea + 4)[0]] = s
    return start, pds, fes

def udf_set_extent(f, udf, old_lba, lba, size):
    """Point the UDF file entry of the file at OLD_LBA to LBA/SIZE (one extent)."""
    start, _, fes = udf
    fe = fes.pop(old_lba - start); d = _read_sector(f, fe); l_ea = struct.unpack_from("<I", d, 168)[0]
    struct.pack_into("<QQ", d, 56, size, -(-size // SECTOR))
    struct.pack_into("<II", d, 176 + l_ea, size, lba - start); _udf_write(f, fe, d)
    fes[lba - start] = fe

def relocate_to_end(f, paths, log=print):
    """Move PATHS (in order) to the end of the image and update the ISO9660 records, the UDF file entries and
    partition, the volume size, and the UDF anchor that has to sit in the last sector."""
    files = iso_files(f); udf = udf_layout(f)
    f.seek(0, 2); end = f.tell() // SECTOR
    avdp = _read_sector(f, end - 1) if udf and struct.unpack_from("<H", _read_sector(f, end - 1), 0)[0] == 2 else None
    lba = end
    for p in paths:
        old, size, rec = files[p.upper()]
        f.seek(old * SECTOR); data = f.read(size)
        f.seek(lba * SECTOR); f.write(data + b"\0" * (-size % SECTOR))
        f.seek(rec + 2); f.write(struct.pack("<I", lba) + struct.pack(">I", lba))
        if udf: udf_set_extent(f, udf, old, lba, size)
        log(f"  {p}: sector {old} -> {lba}")
        lba += -(-size // SECTOR)
    if avdp is not None:                               # anchor in the new last sector; partition grows to just before it
        struct.pack_into("<I", avdp, 12, lba); _udf_write(f, lba, avdp); lba += 1
        for s in udf[1]:
            d = _read_sector(f, s); struct.pack_into("<I", d, 192, lba - 1 - udf[0]); _udf_write(f, s, d)
    f.seek(16 * SECTOR + 80); f.write(struct.pack("<I", lba) + struct.pack(">I", lba))
    f.truncate(lba * SECTOR)

def rebuild_archive(src, dst, reps, log=print):
    """Rewrite CRASH.BD/BH in DST from SRC's archive with REPS {archive name: bytes} (sizes may change).
    Every file is streamed in original order; BH offsets and the ISO9660 and UDF sizes of CRASH.BD are updated.
    The room for CRASH.BD is measured on DST, so files moved out of its way (relocate_to_end) count."""
    files = iso_files(src); dfiles = iso_files(dst)
    bh_lba, bh_size, _ = files["/CRASH6/CRASH.BH"]; bd_lba, bd_size, bd_rec = files["/CRASH6/CRASH.BD"]
    room = (min(l for l, _, _ in dfiles.values() if l > bd_lba) - bd_lba) * SECTOR
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
    left = room - pos
    while left: n = min(left, 16 << 20); dst.write(b"\0" * n); left -= n
    dst.seek(bh_lba * SECTOR); dst.write(bh)
    dst.seek(bd_rec + 10); dst.write(struct.pack("<I", pos) + struct.pack(">I", pos))
    udf = udf_layout(dst)
    if udf: udf_set_extent(dst, udf, bd_lba, bd_lba, pos)
    log(f"  CRASH.BD {bd_size} -> {pos} bytes ({pos - bd_size:+d}), {room - pos} bytes of disc space left")
