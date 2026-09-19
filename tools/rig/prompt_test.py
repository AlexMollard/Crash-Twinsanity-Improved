"""Skip-prompt check: triggers a cutscene and screenshots it while it plays (the "hold triangle to skip" hint should be
on the bottom bar) and again after gameplay resumes (the hint should be gone), once skipped and once played in full.

  python prompt_test.py NAME STATE X Y Z SECONDS     (SECONDS: how long the full scene plays; see results/summary.txt)

Writes results/NAME_prompt_{skip,full}_{during,after}.png and a side-by-side results/NAME_prompt.png."""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

def bottom_text(img):
    """Mean brightness of the bar where the hint is drawn (rows 425-465, middle half of the width)."""
    w, h, b = img; tot = n = 0
    for y in range(425 * h // 480, 465 * h // 480):
        row = b[(y * w + w // 4) * 4:(y * w + 3 * w // 4) * 4]
        tot += sum(row[0::4]) + sum(row[1::4]) + sum(row[2::4]); n += 3 * (len(row) // 4)
    return tot / max(n, 1)

def run(name, state, x, y, z, secs, skip, out):
    tag = "skip" if skip else "full"
    rig.level(state); p = rig.Pine()
    rig.teleport(x, y + 1.0, z); t0 = time.time()
    while not rig.in_cutscene():
        if time.time() - t0 > 12: return {"started": False}
        time.sleep(0.2)
    t = time.time(); time.sleep(1.5)
    during = os.path.join(out, f"{name}_prompt_{tag}_during.png"); rig.screenshot(during)
    lit_during = bottom_text(rig.grab())
    if skip:
        rig.set_pad(p, ("triangle",)); time.sleep(1.5); rig.set_pad(p); wait = 6.0
    else:
        wait = secs + 3.0
    time.sleep(max(0.0, t + wait - time.time()))
    after = os.path.join(out, f"{name}_prompt_{tag}_after.png"); rig.screenshot(after)
    return {"started": True, "bar_during": round(lit_during, 1), "bar_after": round(bottom_text(rig.grab()), 1),
            "cutscene_after": rig.in_cutscene(), "shots": (during, after)}

def main():
    name, state, x, y, z, secs = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
    out = os.path.join(rig.HERE, "results"); os.makedirs(out, exist_ok=True)
    res = {tag: run(name, state, x, y, z, secs, tag == "skip", out) for tag in ("skip", "full")}
    for tag, r in res.items(): print(f"  {tag}: {r}")
    shots = [s for r in res.values() if r.get("started") for s in r["shots"]]
    if shots: subprocess.run([sys.executable, os.path.join(rig.HERE, "compare.py"), os.path.join(out, f"{name}_prompt.png"), *shots])

if __name__ == "__main__":
    main()
