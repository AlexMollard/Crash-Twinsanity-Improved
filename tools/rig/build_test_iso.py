"""Builds an ISO = the [Modded] ISO with edited files inside the CRASH.BD/BH archive.

  python build_test_iso.py [--out PATH] [--fresh] Levels\\Earth\\Hub\\beach.rm2=path\\to\\beach.rm2 [...]

The archive is regenerated in place: every file is streamed from the [Modded] ISO in its original order, with
replacements swapped in (they may change size), CRASH.BH is rewritten with the new offsets, and the ISO9660
directory entry for CRASH.BD gets the new size. The archive must still fit before the next file on the disc
(the PAL disc leaves 1975 spare bytes). Default output: tools/rig/test.iso (copied from [Modded] if missing)."""
import os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(MOD, "Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It) [Modded].iso")
SECTOR = 2048

def iso_files(f):
    """{PATH: (lba, size, record_abs_offset)} for every file on the disc."""
    f.seek(16 * SECTOR); pvd = f.read(SECTOR)
    root = pvd[156:190]; out = {}
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

def parse_bh(bh):
    p, out = 4, []
    while p < len(bh):
        n = struct.unpack_from("<i", bh, p)[0]; name = bh[p + 4:p + 4 + n].decode("ascii")
        off, size = struct.unpack_from("<II", bh, p + 4 + n); out.append([name, off, size, p + 4 + n]); p += 12 + n
    return out

def build(out, reps, fresh=False):
    if fresh or not os.path.exists(out):
        print("copying", os.path.basename(SRC), "->", out); shutil.copyfile(SRC, out)
    with open(SRC, "rb") as src, open(out, "r+b") as dst:
        files = iso_files(src)
        bh_lba, bh_size, _ = files["/CRASH6/CRASH.BH"]; bd_lba, bd_size, bd_rec = files["/CRASH6/CRASH.BD"]
        room = (min(l for l, _, _ in files.values() if l > bd_lba) - bd_lba) * SECTOR
        src.seek(bh_lba * SECTOR); bh = bytearray(src.read(bh_size)); entries = parse_bh(bh)
        reps = {k.lower(): open(v, "rb").read() for k, v in reps.items()}
        unknown = set(reps) - {e[0].lower() for e in entries}
        if unknown: raise SystemExit(f"not in archive: {unknown}")
        new_total = sum(len(reps.get(e[0].lower(), b"")) if e[0].lower() in reps else e[2] for e in entries)
        if new_total > room: raise SystemExit(f"archive would be {new_total} bytes, only {room} fit on the disc")
        pos = 0
        dst.seek(bd_lba * SECTOR)
        for e in entries:
            name, off, size, rec = e
            if name.lower() in reps:
                data = reps[name.lower()]; dst.write(data)
                print(f"{name}: {size} -> {len(data)} bytes at BD+{pos:#x}"); size = len(data)
            else:
                src.seek(bd_lba * SECTOR + off); left = size
                while left:
                    chunk = src.read(min(left, 16 << 20)); dst.write(chunk); left -= len(chunk)
            struct.pack_into("<II", bh, rec, pos, size); pos += size
        dst.write(b"\0" * (room - pos))                      # clear the rest of the archive's disc space
        dst.seek(bh_lba * SECTOR); dst.write(bh)
        dst.seek(bd_rec + 10); dst.write(struct.pack("<I", pos) + struct.pack(">I", pos))   # ISO9660 size, both endians
        print(f"CRASH.BD {bd_size} -> {pos} bytes ({pos - bd_size:+d}), {room - pos} bytes of disc space left")

if __name__ == "__main__":
    args = sys.argv[1:]; out = os.path.join(HERE, "test.iso")
    if "--out" in args: i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    build(out, dict(a.split("=", 1) for a in args if "=" in a), fresh="--fresh" in args)
