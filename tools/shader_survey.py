"""What GS state do the game's own materials ask for? Surveys every level's shaders.

Shader settings block: ABlending +0, ShadingMethod +10, TextureMapping +11, Fogging +13,
TextureFilter (magnify) +23, AlphaCorrection/FBA +24, then LodParamK/L at +30.
"""
import collections, glob, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "rig"))
import rm2splice

PARAMS = {23: 12, 26: 20, 16: 4, 17: 4}

def shaders(buf):
    try: base, _ = rm2splice.locate(buf, [11, 1])
    except (StopIteration, struct.error): return
    _, _, recs = rm2splice._records(buf, base)
    for off, size, rid in recs:
        p = base + off; end = p + size
        _, _, nlen = struct.unpack_from("<QiI", buf, p); p += 16
        name = bytes(buf[p:p + nlen]); p += nlen
        (count,) = struct.unpack_from("<I", buf, p); p += 4
        out = []
        for _ in range(count):
            (kind,) = struct.unpack_from("<I", buf, p); p += 4 + PARAMS.get(kind, 0)
            out.append((p, bytes(buf[p:p + 34])))
            p += 24 + 6 + 4 + 48 + 8
        if p == end:
            for s, blob in out: yield rid, name, s, blob

tally = collections.Counter()
lodk = collections.Counter()
by_filter = collections.Counter()
levels = sorted(glob.glob(os.path.join(ROOT, "work", "extracted", "Levels", "**", "*.rm2"), recursive=True))
total = 0
for rm2 in levels:
    buf = bytearray(open(rm2, "rb").read())
    for rid, name, s, blob in shaders(buf):
        total += 1
        ablend, shd, txt, fog, filt, fba = blob[0], blob[10], blob[11], blob[13], blob[23], blob[24]
        k = struct.unpack_from("<H", blob, 30)[0]
        tally["opaque" if ablend == 0 else "blended"] += 1
        tally["flat shading" if shd == 0 else "gouraud"] += 1
        tally["textured" if txt else "untextured"] += 1
        tally["fog off" if fog == 0 else "fog on"] += 1
        tally["magnify NEAREST" if filt == 0 else "magnify LINEAR"] += 1
        tally["shadow receiver" if fba else "not a receiver"] += 1
        lodk[k] += 1
        if filt == 0 and txt: by_filter[name.decode("latin-1")[:28]] += 1

print(f"{total} shaders across {len(levels)} level files\n")
for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
    print(f"  {k:18s} {v:7d}  {100*v/total:5.1f}%")
print("\nLodParamK values:", dict(lodk.most_common(6)))
print("\nTextured materials using point magnification (top 25):")
for k, v in by_filter.most_common(25): print(f"  {v:5d}  {k}")
