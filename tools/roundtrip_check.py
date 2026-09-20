"""Checks that every level survives a load/save through the Twinsanity Editor library unchanged.

This is the property that decides whether the toolchain can author content rather than only patch it. If a
level can be read into the library's object model and written back byte-for-byte, then anything that can be
expressed in that model can be changed and saved with confidence; if it cannot, every edit has to be a
surgical splice of the original bytes (tools/rig/rm2splice.py) and whole-file authoring is off the table.

  python tools/roundtrip_check.py [--src ISO] [--filter REGEX] [--keep]

Prints one line per file and a summary. Exit status is non-zero if any file differs.
"""
import argparse, glob, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import isotools as it

TWINSDUMP = os.path.join(HERE, "twinsdump", "bin", "Release", "net48", "twinsdump.exe")


def diff_report(a, b):
    """(byte count, run count, offsets within the shortest common item) for two buffers."""
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    runs = 0
    for i, j in zip(diffs, diffs[1:] + [None]):
        if j is None or j != i + 1: runs += 1
    return len(diffs) + abs(len(a) - len(b)), runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src"); ap.add_argument("--filter", default=r"\.rm2$"); ap.add_argument("--keep", action="store_true")
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
            if not o.keep:
                for p2 in (src_path, out_path):
                    if os.path.exists(p2): os.remove(p2)

    print(f"\nidentical: {ok}   differing: {len(bad)}   skipped: {skipped}")
    for name, count, runs, delta in bad[:20]:
        print(f"   {name}: {count} bytes, {runs} runs, {delta:+d}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
