"""Decode a gallery image out of the archive into a single PNG.

The disc's Extras gallery, loading screens and level cards are `.psm` files: a run of PTC records holding a grid of
128x256 textures that together make one picture. twinsdump's `psm` command decodes the tiles; this stitches them.

  python tools/psm_extract.py "Extras\\Unseen\\Unseen08.psm" out/           # straight from the archive
  python tools/psm_extract.py --list Extras                                  # what is in there
  python tools/psm_extract.py --cols 4 some_file.psm out/                    # a loose file

Tiles are laid out left to right, top to bottom. Eight 128x256 tiles make a 512x512 picture at four columns, which
is what the gallery art uses; --cols overrides it for anything shaped differently.
"""
import argparse, glob, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")

def source_iso():
    for name in sorted(glob.glob(os.path.join(ROOT, "*.iso"))):
        if "[Modded]" in name: continue
        try:
            if it.iso_crc(name) == "1510E1D1": return name
        except Exception: pass
    raise SystemExit("no original ISO found next to the repository")

def archive_names(iso):
    with open(iso, "rb") as f:
        idx = it.parse_bh(it.read_file(f, it.iso_files(f), "/CRASH6/CRASH.BH"))
    return list(idx) if isinstance(idx, dict) else [r[0] for r in idx]

def extract(iso, name, work):
    with open(iso, "rb") as f:
        data = it.archive_file(f, it.iso_files(f), name)
    path = os.path.join(work, name.replace("\\", "_"))
    open(path, "wb").write(data)
    return path

def decode(psm_path, work, cols, out_png):
    from PIL import Image
    tiles_dir = os.path.join(work, "tiles"); os.makedirs(tiles_dir, exist_ok=True)
    for old in glob.glob(os.path.join(tiles_dir, "*.png")): os.remove(old)
    r = subprocess.run([TWINSDUMP, psm_path, "psm", tiles_dir], capture_output=True, text=True)
    tiles = sorted(glob.glob(os.path.join(tiles_dir, "*.png")))
    if not tiles: raise SystemExit(f"no tiles decoded from {psm_path}:\n{r.stdout}{r.stderr}")
    ims = [Image.open(t) for t in tiles]
    tw, th = ims[0].size
    cols = cols or (4 if len(ims) % 4 == 0 else len(ims))
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGBA", (tw * cols, th * rows))
    for i, im in enumerate(ims): out.paste(im, ((i % cols) * tw, (i // cols) * th))
    out.save(out_png)
    return out.size, len(ims)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="archive entry (Extras\\...\\X.psm) or a loose .psm file")
    ap.add_argument("outdir", nargs="?", default=".")
    ap.add_argument("--list", action="store_true", help="list archive entries under NAME instead of decoding")
    ap.add_argument("--cols", type=int, default=0)
    o = ap.parse_args()

    if o.list:
        iso = source_iso()
        hits = [n for n in archive_names(iso) if n.lower().startswith(o.name.lower())]
        print(f"{len(hits)} entries under {o.name}")
        for n in hits: print("  ", n)
        return

    os.makedirs(o.outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        psm = o.name if os.path.exists(o.name) else extract(source_iso(), o.name, work)
        stem = os.path.splitext(os.path.basename(psm))[0]
        out_png = os.path.join(o.outdir, stem + ".png")
        size, n = decode(psm, work, o.cols, out_png)
        print(f"{out_png}  {size[0]}x{size[1]}  from {n} tiles")

if __name__ == "__main__":
    main()
