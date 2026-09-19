"""ISO / archive helpers for the Crash Twinsanity PAL disc (SLES-52568): ISO9660 directory, the CRASH.BD/BH
archive, the SLES_525.68 executable and PCSX2's game CRC."""
import array, os, struct

SECTOR = 2048
ELF_PATH = "/SLES_525.68"
ELF_BASE, ELF_FILE_OFF = 0x100000, 0x1000        # single PT_LOAD segment: file offset = vaddr - 0x100000 + 0x1000
ORIGINAL_CRC = "1510E1D1"                         # untouched PAL disc
BD, BH = "/CRASH6/CRASH.BD", "/CRASH6/CRASH.BH"

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
    fe = fes.pop(old_lba - start); _write_fe(f, fe, start, lba, size)
    fes[lba - start] = fe

def _write_fe(f, fe, start, lba, size):
    d = _read_sector(f, fe); l_ea = struct.unpack_from("<I", d, 168)[0]
    struct.pack_into("<QQ", d, 56, size, -(-size // SECTOR))
    struct.pack_into("<II", d, 176 + l_ea, size, lba - start); _udf_write(f, fe, d)

def _set_record(f, rec, lba, size):
    """ISO9660 directory record: extent location and data length (both byte orders)."""
    f.seek(rec + 2); f.write(struct.pack("<I", lba) + struct.pack(">I", lba) + struct.pack("<I", size) + struct.pack(">I", size))

def _copy_sectors(f, old, new, size):
    """Copy SIZE bytes from sector OLD to sector NEW within the image (overlapping ranges are fine)."""
    n = -(-size // SECTOR) * SECTOR; step = 16 << 20
    for o in (range(0, n, step) if new < old else reversed(range(0, n, step))):
        k = min(step, n - o); f.seek(old * SECTOR + o); chunk = f.read(k)
        f.seek(new * SECTOR + o); f.write(chunk + b"\0" * (k - len(chunk)))

def archive_last(f, log=print):
    """Disc layout for faster loading: CRASH.BD (all level data) moves to the end of the image - the outer edge of the
    disc, where the drive (CAV, and PCSX2's model of it) reads fastest - and the files that followed it (speech banks,
    IOP modules, movies) move down into its place in their original order. The image size stays the same and CRASH.BD
    can grow freely. Only the directory records and UDF entries of CRASH.BD change here: rebuild_archive writes its data.
    The game opens every file by name (sceCdSearchFile), so no code refers to sectors."""
    files = iso_files(f); udf = udf_layout(f)
    bd_lba, bd_size, bd_rec = files[BD]
    fe_of = {}
    if udf:                                           # map files to UDF entries before anything moves (sectors get reused)
        by_lba = {lba: p for p, (lba, _, _) in files.items()}
        fe_of = {by_lba[rel + udf[0]]: fe for rel, fe in udf[2].items() if rel + udf[0] in by_lba}
        missing = set(files) - set(fe_of)
        if missing: raise SystemExit(f"no UDF entry for {sorted(missing)}")
    lba = bd_lba; moved = 0
    for old, p in sorted((l, p) for p, (l, _, _) in files.items() if l > bd_lba):
        size = files[p][1]
        _copy_sectors(f, old, lba, size); _set_record(f, files[p][2], lba, size)
        if udf: _write_fe(f, fe_of[p], udf[0], lba, size)
        lba += -(-size // SECTOR); moved += size
    lba = -(-lba // 16) * 16                          # start CRASH.BD on an ECC block (16 sectors)
    _set_record(f, bd_rec, lba, bd_size)
    if udf: _write_fe(f, fe_of[BD], udf[0], lba, bd_size)
    log(f"  {len(files) - sum(1 for l, _, _ in files.values() if l <= bd_lba)} files ({moved / 2**20:.0f} MB) moved to sector {bd_lba}, CRASH.BD: sector {bd_lba} -> {lba}")
    return lba

def set_image_end(f, lba):
    """End the image at sector LBA: a UDF anchor goes in the last sector (it must sit there), the partition grows to
    just before it, and the ISO9660 volume size matches."""
    udf = udf_layout(f)
    if udf:
        avdp = _read_sector(f, 256); struct.pack_into("<I", avdp, 12, lba); _udf_write(f, lba, avdp); lba += 1
        for s in udf[1]:
            d = _read_sector(f, s); struct.pack_into("<I", d, 192, lba - 1 - udf[0]); _udf_write(f, s, d)
    f.seek(16 * SECTOR + 80); f.write(struct.pack("<I", lba) + struct.pack(">I", lba))
    f.truncate(lba * SECTOR)

def rebuild_archive(src, dst, reps, log=print):
    """Rewrite CRASH.BD/BH in DST from SRC's archive with REPS {archive name: bytes} (sizes may change).
    Every file is streamed in original order to where DST's directory puts CRASH.BD; BH offsets and the ISO9660 and
    UDF sizes of CRASH.BD are updated. If CRASH.BD is the last file (archive_last), the image ends right after it."""
    files = iso_files(src); dfiles = iso_files(dst)
    bh_lba, bh_size, _ = files[BH]; bd_lba, bd_size, _ = files[BD]
    at, _, rec = dfiles[BD]
    later = [l for l, _, _ in dfiles.values() if l > at]
    room = (min(later) - at) * SECTOR if later else None
    src.seek(bh_lba * SECTOR); bh = bytearray(src.read(bh_size)); entries = parse_bh(bh)
    reps = {k.lower(): v for k, v in reps.items()}
    unknown = set(reps) - {e[0].lower() for e in entries}
    if unknown: raise SystemExit(f"not in the archive: {sorted(unknown)}")
    total = sum(len(reps[e[0].lower()]) if e[0].lower() in reps else e[2] for e in entries)
    if room is not None and total > room: raise SystemExit(f"archive would be {total} bytes but only {room} fit on the disc")
    if total >= 1 << 30: raise SystemExit(f"archive would be {total} bytes - over the 1 GiB a single UDF extent holds")
    pos = 0; dst.seek(at * SECTOR)
    for name, off, size, brec in entries:
        if name.lower() in reps:
            data = reps[name.lower()]; dst.write(data); log(f"  {name}: {size} -> {len(data)} bytes"); size = len(data)
        else:
            src.seek(bd_lba * SECTOR + off); left = size
            while left:
                chunk = src.read(min(left, 16 << 20)); dst.write(chunk); left -= len(chunk)
        struct.pack_into("<II", bh, brec, pos, size); pos += size
    left = (room if room is not None else -(-pos // SECTOR) * SECTOR) - pos
    while left: n = min(left, 16 << 20); dst.write(b"\0" * n); left -= n
    dst.seek(bh_lba * SECTOR); dst.write(bh)
    _set_record(dst, rec, at, pos)
    udf = udf_layout(dst)
    if udf: udf_set_extent(dst, udf, at, at, pos)
    if room is None: set_image_end(dst, at + -(-pos // SECTOR))
    log(f"  CRASH.BD {bd_size} -> {pos} bytes ({pos - bd_size:+d})" + (f", {room - pos} bytes of disc space left" if room is not None else ", at the end of the image"))
