"""Put an object into a level that does not have one, and place instances of it.

This is the two halves of adding something to a level, in one step:

  * the object itself, with its scripts, animations, OGIs, models and skins, through the editor library's
    MergeObject (`twinsdump ... merge ... OBJID`). Object IDs mean the same thing in every level file, so 266
    is the checkpoint crate wherever you take it from.
  * one instance per position, spliced in with rm2splice.insert.

Verified in game: the Earth hub defines no checkpoint object at all, and with object 266 imported from the
beach the crates render with their own models and textures, have collision, and break when Crash lands on
them. What that run did *not* establish is whether a placed checkpoint actually saves progress - that needs a
death and a respawn, and is still open.

An instance is copied from one that already exists in the source level, so every field except the position is
whatever the developers used. That only works when the template instance refers to nothing level-specific;
the checkpoint crate's is empty on all of instances/positions/paths, which is why it travels cleanly. The
check below refuses a template that carries those references rather than writing dangling indices into
another level.

Write --at=X,Y,Z with the equals sign: a negative coordinate on its own looks like an option.

  python tools/place_object.py huba beach 266 --at=-76.2,0.02,114 --at=-84.2,0.02,114
  python tools/place_object.py huba beach 266 --at=-76.2,0.02,114 --out work/huba_cp.rm2
"""
import argparse, glob, os, re, struct, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "rig"))
import rm2splice as R

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EXTRACTED = os.path.join(ROOT, "work", "extracted")
INSTANCES, LAYER = 6, 0           # subsection 6 of a layer holds its instances; layer 0 is the usual one
INST_RE = re.compile(r"^inst\s+(\d+) Instance\[(\d+)\].*obj (\d+) ")


def find_level(name):
    hits = glob.glob(os.path.join(EXTRACTED, "**", name + ".rm2"), recursive=True)
    if not hits:
        raise SystemExit(f"no {name}.rm2 under {EXTRACTED} - run the extraction step first")
    return hits[0]


def template_instance(level_path, objid):
    """The bytes of an existing instance of `objid`, and its layer, to copy into the target."""
    out = subprocess.run([TWINSDUMP, level_path, "instances", ".", "-v"], capture_output=True, text=True).stdout
    lines = out.splitlines()
    for i, line in enumerate(lines):
        m = INST_RE.match(line)
        if not m or int(m.group(3)) != objid:
            continue
        detail = lines[i + 1] if i + 1 < len(lines) else ""
        refs = {k: re.search(rf"{k} \[([^\]]*)\]", detail) for k in ("instances", "positions", "paths")}
        carried = {k: v.group(1) for k, v in refs.items() if v and v.group(1).strip()}
        if carried:
            print(f"  skipping instance {m.group(1)}: it refers to {carried}, which mean nothing in another level")
            continue
        layer, inst_id = int(m.group(2)), int(m.group(1))
        buf = open(level_path, "rb").read()
        off, size = R.locate(buf, [layer, INSTANCES, inst_id])
        return bytearray(buf[off:off + size]), layer
    raise SystemExit(f"{os.path.basename(level_path)} has no self-contained instance of object {objid} to copy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="level to add the object to, e.g. huba")
    ap.add_argument("source", help="level to take it from, e.g. beach")
    ap.add_argument("objid", type=int, help="object id (the same number in every level file)")
    # --at rather than positional: a negative coordinate looks like an option to argparse
    ap.add_argument("--at", action="append", required=True, metavar="X,Y,Z",
                    help="where to place an instance, as --at=X,Y,Z; repeat for more than one")
    ap.add_argument("--layer", type=int, default=LAYER)
    ap.add_argument("--out")
    o = ap.parse_args()

    target, source = find_level(o.target), find_level(o.source)
    out = o.out or os.path.join(ROOT, "work", f"{o.target}_obj{o.objid}.rm2")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    spots = [tuple(float(v) for v in p.split(",")) for p in o.at]
    if any(len(s) != 3 for s in spots):
        raise SystemExit("each position must be X,Y,Z")

    r = subprocess.run([TWINSDUMP, target, "merge", source, out, str(o.objid)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"importing object {o.objid} failed:\n{r.stdout}{r.stderr}")
    print(r.stdout.strip())

    template, from_layer = template_instance(source, o.objid)
    was = struct.unpack_from("<fff", template, 0)          # the record opens with its x/y/z
    print(f"  copying an instance from {o.source} layer {from_layer}, {len(template)} bytes, "
          f"at ({was[0]:.2f}, {was[1]:.2f}, {was[2]:.2f})")

    data = open(out, "rb").read()
    for x, y, z in spots:
        inst = bytearray(template)
        struct.pack_into("<fff", inst, 0, x, y, z)
        base = R.locate(data, [o.layer, INSTANCES])[0]
        new_id = max(rec[2] for rec in R._records(data, base)[2]) + 1
        data, delta = R.insert(data, [o.layer, INSTANCES], bytes(inst), new_id)
        print(f"  instance {new_id} at ({x}, {y}, {z})  {delta:+d} bytes")
    R.check(data)                                          # the container still adds up
    open(out, "wb").write(data)

    before = os.path.getsize(target)
    print(f"\n{os.path.basename(target)} {before:,} -> {len(data):,} bytes "
          f"({len(data) - before:+,}, {100 * (len(data) - before) / before:+.1f}%)\nwrote {out}")


if __name__ == "__main__":
    main()
