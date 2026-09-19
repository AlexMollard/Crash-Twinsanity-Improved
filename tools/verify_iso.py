"""Checks a built ISO against the original: every file's ISO9660 and UDF entries agree, UDF descriptor tags are
valid, the volume size and UDF anchor match the image, and every file the build doesn't change is byte-identical.

  python tools/verify_iso.py ORIGINAL.iso MODDED.iso"""
import hashlib, os, struct, sys
import isotools as it

CHANGED = {"/SLES_525.68", "/CRASH6/CRASH.BD", "/CRASH6/CRASH.BH"}

def digest(f, lba, size):
    h = hashlib.sha1(); f.seek(lba * it.SECTOR); left = size
    while left: b = f.read(min(left, 16 << 20)); h.update(b); left -= len(b)
    return h.hexdigest()

def tag_ok(d):
    n = struct.unpack_from("<H", d, 10)[0]
    return d[4] == sum(d[i] for i in range(16) if i != 4) & 0xFF and struct.unpack_from("<H", d, 8)[0] == it._udf_crc(d[16:16 + n])

def main(orig, mod):
    bad = []
    with open(orig, "rb") as o, open(mod, "rb") as m:
        of, mf = it.iso_files(o), it.iso_files(m)
        if set(of) != set(mf): bad.append(f"file lists differ: {set(of) ^ set(mf)}")
        m.seek(0, 2); sectors = m.tell() // it.SECTOR
        m.seek(16 * it.SECTOR + 80); vol = struct.unpack("<I", m.read(4))[0]
        if vol != sectors: bad.append(f"volume size {vol} != image {sectors} sectors")
        start, pds, fes = it.udf_layout(m)
        for s in pds + list(fes.values()) + [256, sectors - 1]:
            if not tag_ok(it._read_sector(m, s)): bad.append(f"UDF tag bad at sector {s}")
        if struct.unpack_from("<H", it._read_sector(m, sectors - 1), 0)[0] != 2: bad.append("no UDF anchor in the last sector")
        plen = struct.unpack_from("<I", it._read_sector(m, pds[0]), 192)[0]
        for p, (lba, size, _) in sorted(mf.items()):
            fe = fes.get(lba - start)
            if fe is None: bad.append(f"{p}: no UDF entry at sector {lba}"); continue
            d = it._read_sector(m, fe); l_ea = struct.unpack_from("<I", d, 168)[0]
            usize = struct.unpack_from("<Q", d, 56)[0]; alen, apos = struct.unpack_from("<II", d, 176 + l_ea)
            if (usize, alen & 0x3FFFFFFF, apos) != (size, size, lba - start): bad.append(f"{p}: UDF says {usize}/{alen}@{apos}, ISO9660 {size}@{lba - start}")
            if lba - start + -(-size // it.SECTOR) > plen: bad.append(f"{p}: outside the UDF partition")
            if p not in CHANGED and digest(o, *of[p][:2]) != digest(m, lba, size): bad.append(f"{p}: content differs from the original")
        print(f"{len(mf)} files, {sectors} sectors ({sectors * it.SECTOR / 2**30:.2f} GiB)")
    print("\n".join(bad) if bad else "OK: ISO9660 and UDF agree, tags valid, unchanged files identical")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
