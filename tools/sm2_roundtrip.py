"""Can every scenery file be rewritten safely?

Lighting lives in the `.sm2` scenery files, and this mod has only ever edited `.rm2` levels. Before any lighting
change is worth designing, the toolchain has to be able to load a scenery file and write it back unchanged - if it
cannot, an edit would corrupt everything else in the file along with the lights.

Three files round-tripped byte-for-byte by hand, which is not enough to build on. This checks all of them, and
reports failures by name so a partial answer is still usable: a level that round-trips can be lit, one that does
not cannot, and the difference is per file rather than all-or-nothing.

  python tools/sm2_roundtrip.py
"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it
from psm_extract import source_iso, archive_names

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")

def main():
    iso = source_iso()
    names = sorted(n for n in archive_names(iso) if n.lower().endswith(".sm2"))
    print(f"{len(names)} scenery files", flush=True)
    ok = []; bad = []; broke = []
    with open(iso, "rb") as f, tempfile.TemporaryDirectory() as work:
        files = it.iso_files(f)
        for n in names:
            base = os.path.basename(n)
            src = os.path.join(work, base); dst = os.path.join(work, "rt_" + base)
            open(src, "wb").write(it.archive_file(f, files, n))
            r = subprocess.run([TWINSDUMP, src, "roundtrip", dst], capture_output=True, text=True)
            out = r.stdout + r.stderr
            if r.returncode != 0 or "Unhandled Exception" in out:      # a crash is not a pass
                broke.append((base, out.strip().splitlines()[0] if out.strip() else "no output"))
            elif "identical=True" in out:
                ok.append(base)
            else:
                m = re.search(r"firstDiff=(-?\d+)", out)
                bad.append((base, m.group(1) if m else "?"))
            for p in (src, dst):
                if os.path.exists(p): os.remove(p)

    print(f"\nidentical: {len(ok)}/{len(names)}")
    if bad:
        print(f"differ: {len(bad)}")
        for b, d in bad: print(f"    {b:20s} first difference at byte {d}")
    if broke:
        print(f"crashed: {len(broke)}")
        for b, e in broke: print(f"    {b:20s} {e}")
    if not bad and not broke:
        print("every scenery file can be rewritten unchanged, so a lighting edit risks only the lights")

if __name__ == "__main__":
    main()
