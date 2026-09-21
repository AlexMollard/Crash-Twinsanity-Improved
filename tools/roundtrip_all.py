"""Load and re-save every level file through the Twinsanity library and report which come back changed.

A field the library reads but does not write back is silently lost the moment anyone saves a level through
the editor, and a field it writes at the wrong width corrupts everything after it - that is what
CollisionSurface did, writing four bytes where two were read. A byte-exact round trip is the cheap test that
catches both, and it is worth running over the whole disc rather than a sample, because the fields involved
only appear in the files that happen to use them.

The .rm2 side is at 135/135. The .sm2 scenery files have never been through this.

  python tools/roundtrip_all.py            # everything
  python tools/roundtrip_all.py sm2        # just the scenery
"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted")
LINE = re.compile(r"original (\d+) bytes, saved (\d+) bytes, identical=(\w+), firstDiff=(-?\d+)")


def main():
    want = sys.argv[1].lower() if len(sys.argv) > 1 else None
    paths = []
    for dirpath, _, names in os.walk(EXTRACTED):
        for n in names:
            ext = n.rsplit(".", 1)[-1].lower()
            if ext in ("rm2", "sm2") and (want is None or ext == want):
                paths.append(os.path.join(dirpath, n))
    paths.sort()
    if not paths:
        raise SystemExit(f"no files to test under {EXTRACTED}")

    bad, failed, ok = [], [], 0
    with tempfile.TemporaryDirectory() as work:
        out = os.path.join(work, "rt.bin")
        for p in paths:
            r = subprocess.run([TWINSDUMP, p, "roundtrip", out], capture_output=True, text=True)
            m = LINE.search(r.stdout)
            if not m:
                failed.append((os.path.basename(p), (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]))
                continue
            a, b, same, diff = int(m[1]), int(m[2]), m[3] == "True", int(m[4])
            if same: ok += 1
            else: bad.append((os.path.basename(p), a, b, diff))

    print(f"{len(paths)} files: {ok} byte-identical, {len(bad)} changed, {len(failed)} would not load\n")
    for name, a, b, diff in bad:
        where = f"first difference at 0x{diff:X}" if diff >= 0 else "same prefix, different length"
        print(f"  CHANGED  {name:16} {a} -> {b} bytes ({b - a:+d}), {where}")
    for name, msg in failed:
        print(f"  FAILED   {name:16} {msg[0][:110] if msg else ''}")
    if not bad and not failed:
        print("  every file survives a load and save unchanged")
    return 1 if bad or failed else 0


if __name__ == "__main__":
    sys.exit(main())
