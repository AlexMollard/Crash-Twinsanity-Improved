"""Surgical RM2 item replacement: swaps one item's bytes and fixes only the offset/size tables of the
sections that contain it. Every other byte of the original file is preserved (the Twinsanity Editor
library's full re-save zeroes a few unknown fields, so we avoid it).

Section header (PS2 RM2/SM2): u32 magic, u32 count, u32 content_size, then count x {u32 off, i32 size, u32 id};
offsets are relative to the section start (file start for the top level); items are stored back to back.

  python rm2splice.py IN.rm2 OUT.rm2 10/1/6367=6367.bin [10/1/6365=6365.bin ...]
"""
import struct, sys

def _records(buf, base):
    magic, count, content = struct.unpack_from("<III", buf, base)
    return count, content, [list(struct.unpack_from("<IiI", buf, base + 12 + 12 * i)) for i in range(count)]

def _write_table(buf, base, content, recs):
    struct.pack_into("<I", buf, base + 8, content)
    for i, (off, size, rid) in enumerate(recs):
        struct.pack_into("<IiI", buf, base + 12 + 12 * i, off, size, rid)

def locate(buf, path):
    """Absolute offset and size of the item at PATH (list of record IDs)."""
    base, size = 0, len(buf)
    for rid in path:
        _, _, recs = _records(buf, base)
        rec = next(r for r in recs if r[2] == rid)
        base, size = base + rec[0], rec[1]
    return base, size

def splice(buf, path, new):
    buf = bytearray(buf)
    bases = [0]
    for rid in path[:-1]:
        _, _, recs = _records(buf, bases[-1])
        bases.append(bases[-1] + next(r for r in recs if r[2] == rid)[0])
    item_off, item_size = locate(buf, path)
    delta = len(new) - item_size
    buf[item_off:item_off + item_size] = new
    for level in range(len(path) - 1, -1, -1):          # innermost section first
        base, rid = bases[level], path[level]
        _, content, recs = _records(buf, base)
        target = next(r for r in recs if r[2] == rid)
        for r in recs:
            if r[0] > target[0]: r[0] += delta
        target[1] += delta
        _write_table(buf, base, content + delta, recs)
    return bytes(buf), delta

if __name__ == "__main__":
    src, dst, *edits = sys.argv[1:]
    buf = open(src, "rb").read(); total = 0
    for e in edits:
        p, f = e.split("=")
        path = [int(x) for x in p.split("/")]
        new = open(f, "rb").read()
        old_off, old_size = locate(buf, path)
        buf, d = splice(buf, path, new); total += d
        print(f"{p}: {old_size} -> {len(new)} bytes ({d:+d})")
    open(dst, "wb").write(buf)
    print(f"wrote {dst}: size change {total:+d} bytes")
