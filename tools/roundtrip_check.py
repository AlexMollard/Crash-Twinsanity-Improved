"""Checks that every level survives a load/save through the Twinsanity Editor library unchanged.

This is the property that decides whether the toolchain can author content rather than only patch it. If a
level can be read into the library's object model and written back byte-for-byte, then anything that can be
expressed in that model can be changed and saved with confidence; if it cannot, every edit has to be a
surgical splice of the original bytes (tools/rig/rm2splice.py) and whole-file authoring is off the table.

  python tools/roundtrip_check.py [--src ISO] [--filter REGEX] [--keep] [--explain]

Prints one line per file and a summary. Exit status is non-zero if any file differs. With --explain, each
differing byte is traced back to the section and the offset within the item that holds it, which turns "this
level loses 42 bytes" into "field +88 of every texture", i.e. something fixable.
"""
import argparse, collections, glob, os, re, struct, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rig"))
import rm2splice

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import isotools as it

TWINSDUMP = os.path.join(HERE, "twinsdump", "bin", "Release", "net48", "twinsdump.exe")


def diff_report(a, b):
    """(byte count, run count) for two buffers."""
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    runs = 0
    for i, j in zip(diffs, diffs[1:] + [None]):
        if j is None or j != i + 1: runs += 1
    return len(diffs) + abs(len(a) - len(b)), runs


def walk_items(buf, base=0, path=(), depth=0):
    """Every item in the RM2 tree as (path of record ids, absolute offset, size)."""
    try:
        count, _, recs = rm2splice._records(buf, base)
    except Exception:
        return
    if not 0 < count < 20000: return
    for off, size, rid in recs:
        start = base + off
        if size <= 0 or start + size > len(buf): continue
        yield (path + (rid,), start, size)
        if depth < 3:
            yield from walk_items(buf, start, path + (rid,), depth + 1)


def explain(original, saved):
    """{(section path, offset within item): count} for every differing byte."""
    items = list(walk_items(original))
    hits = collections.Counter()
    for i in range(min(len(original), len(saved))):
        if original[i] == saved[i]: continue
        best = None
        for p, start, size in items:
            if start <= i < start + size and (best is None or size < best[2]):
                best = (p, start, size)
        if best: hits[(best[0][:-1], i - best[1])] += 1
        else: hits[((), -1)] += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src"); ap.add_argument("--filter", default=r"\.rm2$"); ap.add_argument("--keep", action="store_true")
    ap.add_argument("--explain", action="store_true")
    o = ap.parse_args()

    src = o.src
    if not src:
        src = next(p for p in sorted(glob.glob(os.path.join(ROOT, "*.iso"))) if it.iso_crc(p) == it.ORIGINAL_CRC)
    if not os.path.exists(TWINSDUMP):
        raise SystemExit(f"{TWINSDUMP} missing - run tools/build_mod.py once, or build twinsdump")

    pattern = re.compile(o.filter, re.I)
    work = os.path.join(ROOT, "work", "re", "roundtrip")
    os.makedirs(work, exist_ok=True)

    bad, ok, skipped = [], 0, 0
    causes = collections.Counter()
    with open(src, "rb") as f:
        files = it.iso_files(f)
        bh = it.read_file(f, files, "/CRASH6/CRASH.BH")
        bd_lba = files["/CRASH6/CRASH.BD"][0]
        entries = [e for e in it.parse_bh(bh) if pattern.search(e[0])]
        print(f"{len(entries)} file(s) matching /{o.filter}/ in the archive\n")
        for name, off, size, _ in entries:
            f.seek(bd_lba * it.SECTOR + off)
            original = f.read(size)
            base = re.sub(r"[\\/:]", "_", name)
            src_path = os.path.join(work, base)
            out_path = os.path.join(work, base + ".out")
            open(src_path, "wb").write(original)
            p = subprocess.run([TWINSDUMP, src_path, "roundtrip", out_path], capture_output=True, text=True)
            if p.returncode != 0:
                print(f"  SKIP  {name}: twinsdump failed ({p.stderr.strip().splitlines()[-1][:70] if p.stderr.strip() else 'no output'})")
                skipped += 1
            else:
                saved = open(out_path, "rb").read()
                if saved == original:
                    ok += 1
                    print(f"  ok    {name}")
                else:
                    count, runs = diff_report(original, saved)
                    bad.append((name, count, runs, len(saved) - len(original)))
                    print(f"  DIFF  {name}: {count} bytes in {runs} run(s), size {len(saved) - len(original):+d}")
                    if o.explain:
                        for (path, rel), n in explain(original, saved).most_common(5):
                            where = "/".join(str(x) for x in path) or "(outside any item)"
                            print(f"          section {where}, offset +{rel} in the item: {n} byte(s)")
                            causes[(path, rel)] += n
            if not o.keep:
                for p2 in (src_path, out_path):
                    if os.path.exists(p2): os.remove(p2)

    print(f"\nidentical: {ok}   differing: {len(bad)}   skipped: {skipped}")
    for name, count, runs, delta in bad[:20]:
        print(f"   {name}: {count} bytes, {runs} runs, {delta:+d}")
    if causes:
        print()
        print("distinct causes, most damaging first:")
        for (path, rel), n in causes.most_common(12):
            where = "/".join(str(x) for x in path) or "(outside any item)"
            print(f"   section {where}, offset +{rel}: {n} bytes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
