"""Surgical RM2 item replacement: swaps one item's bytes and fixes only the offset/size tables of the
sections that contain it. Every other byte of the original file is preserved (the Twinsanity Editor
library's full re-save zeroes a few unknown fields, so we avoid it).

Section header (PS2 RM2/SM2): u32 magic, u32 count, u32 content_size, then count x {u32 off, i32 size, u32 id};
offsets are relative to the section start (file start for the top level); items are stored back to back.

Layers are top-level sections and subsection 6 of a layer holds its Instances, so 0/6+44=x.bin adds an
instance to layer 0 - which is what placing anything new in a level (a checkpoint crate, a crate, an enemy)
comes down to.

  python rm2splice.py IN.rm2 OUT.rm2 10/1/6367=6367.bin [10/1/6365=6365.bin ...]   replace an item
  python rm2splice.py IN.rm2 OUT.rm2 0/6+44=inst.bin                                add one
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

def insert(buf, section, new, new_id):
    """Add a new item to a section. `section` is the path of record IDs naming the *section* that receives
    it ([] for the top level), unlike `splice`, whose path names an item.

    Replacing an item only moves bytes after it. Adding one also grows the section's record table by 12,
    which moves every item in that section - offsets are relative to the section start, so all of them have
    to be bumped, and the new record's own offset has to be computed after that growth. Items sit back to
    back with no padding (checked across the section tree of a real level), so the item goes at the end of
    the section's content and everything above it grows by 12 + len(new)."""
    buf = bytearray(buf)
    bases = [0]
    for rid in section:
        _, _, recs = _records(buf, bases[-1])
        bases.append(bases[-1] + next(r for r in recs if r[2] == rid)[0])
    base = bases[-1]
    count, content, recs = _records(buf, base)
    if any(r[2] == new_id for r in recs):
        raise ValueError(f"the section already holds an item with id {new_id}")
    table_end = 12 + 12 * count                          # where this section's item data starts
    buf[base + table_end:base + table_end] = b"\0" * 12   # room for one more record
    for r in recs: r[0] += 12                             # ... which pushed every item down
    new_off = table_end + 12 + content                    # after the last item
    buf[base + new_off:base + new_off] = new
    recs.append([new_off, len(new), new_id])
    struct.pack_into("<I", buf, base + 4, count + 1)
    _write_table(buf, base, content + len(new), recs)
    delta = 12 + len(new)
    for level in range(len(section) - 1, -1, -1):         # innermost parent first
        b, rid = bases[level], section[level]
        _, c, rs = _records(buf, b)
        target = next(r for r in rs if r[2] == rid)
        for r in rs:
            if r[0] > target[0]: r[0] += delta
        target[1] += delta
        _write_table(buf, b, c + delta, rs)
    return bytes(buf), delta


def check(buf, base=0, path=()):
    """Walk the section tree and assert it is self-consistent: every section's size is 12 + 12*count +
    content, its items are back to back with no gap or overlap, and they end exactly where it does.
    Returns the number of sections checked. An insert that passes this has not corrupted the container."""
    count, content, recs = _records(buf, base)
    size = 12 + 12 * count + content
    if base + size > len(buf):
        raise ValueError(f"section {path or 'top'} runs past the end of the file")
    for r in sorted(recs, key=lambda r: r[0]):
        if r[1] < 0: raise ValueError(f"section {path or 'top'}: item {r[2]} has negative size")
    order = sorted(recs, key=lambda r: r[0])
    if order and order[0][0] != 12 + 12 * count:
        raise ValueError(f"section {path or 'top'}: first item at {order[0][0]}, expected {12 + 12 * count}")
    for a, b in zip(order, order[1:]):
        if a[0] + a[1] != b[0]:
            raise ValueError(f"section {path or 'top'}: gap/overlap between items {a[2]} and {b[2]}")
    if order and order[-1][0] + order[-1][1] != size:
        raise ValueError(f"section {path or 'top'}: items end at {order[-1][0] + order[-1][1]}, section is {size}")
    n = 1
    for r in recs:
        # The magic alone does not identify a subsection - plenty of leaf items happen to start 0x00010001.
        # A real one also accounts for its whole record: 12 + 12*count + content has to be exactly its size.
        if r[1] < 12 or struct.unpack_from("<I", buf, base + r[0])[0] != 0x10001: continue
        sub_count, sub_content = struct.unpack_from("<II", buf, base + r[0] + 4)
        if sub_count > (r[1] - 12) // 12 or 12 + 12 * sub_count + sub_content != r[1]: continue
        n += check(buf, base + r[0], path + (r[2],))
    return n


if __name__ == "__main__":
    src, dst, *edits = sys.argv[1:]
    buf = open(src, "rb").read(); total = 0
    for e in edits:
        p, f = e.split("=")
        new = open(f, "rb").read()
        if "+" in p:                                    # 0/6+44=inst.bin : add item 44 to section 0/6
            sec, nid = p.split("+")
            path = [int(x) for x in sec.split("/")] if sec else []
            buf, d = insert(buf, path, new, int(nid))
            print(f"{sec or 'top'}: added item {nid}, {len(new)} bytes ({d:+d})")
        else:
            path = [int(x) for x in p.split("/")]
            _, old_size = locate(buf, path)
            buf, d = splice(buf, path, new)
            print(f"{p}: {old_size} -> {len(new)} bytes ({d:+d})")
        total += d
    print(f"container still consistent: {check(buf)} sections")
    open(dst, "wb").write(buf)
    print(f"wrote {dst}: size change {total:+d} bytes")
