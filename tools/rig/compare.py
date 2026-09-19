"""Side-by-side sheet of result screenshots: python compare.py OUT.png A.png B.png [C.png ...] (half size)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig
out, *ins = sys.argv[1:]
imgs = [rig.load_png(p) for p in ins]; W, H = 320, 240
sheet = bytearray(W * len(imgs) * H * 4)
for c, (w, h, b) in enumerate(imgs):
    for y in range(H):
        for x in range(W):
            si = ((y * h // H) * w + (x * w // W)) * 4; di = (y * W * len(imgs) + c * W + x) * 4
            sheet[di:di + 4] = b[si:si + 4]
rig.png(out, W * len(imgs), H, bytes(sheet)); print("saved", out)
