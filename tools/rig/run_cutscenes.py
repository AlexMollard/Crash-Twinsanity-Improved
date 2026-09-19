"""Runs cutscene_test for every line of cutscenes.txt whose level state exists, and writes results/summary.txt.

  python run_cutscenes.py [NAME ...]"""
import io, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for line in open(os.path.join(HERE, "cutscenes.txt"), encoding="utf-8"):
    s = line.split("#", 1)[0].split()
    if len(s) >= 4: rows.append((s[0], s[1], s[2], s[3], line.split("#", 1)[1].strip() if "#" in line else ""))
only = set(sys.argv[1:])
out = open(os.path.join(HERE, "results", "summary.txt"), "a", encoding="utf-8")
for name, state, x, z, note in rows:
    if only and name not in only: continue
    if not os.path.exists(os.path.join(HERE, "states", state + ".p2s")):
        print(f"{name}: SKIPPED (no state for {state})", flush=True); continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "cutscene_test.py"), name, state, x, z, "--walk-timeout", "150"], capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if l.strip().startswith(("full", "skip", "=>"))] or r.stdout.splitlines()[-3:] + r.stderr.splitlines()[-3:]
    text = f"{name} ({note}):\n  " + "\n  ".join(tail)
    print(text, flush=True); out.write(text + "\n"); out.flush()
