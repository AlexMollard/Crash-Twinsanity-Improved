"""Runs cutscene_test for every cutscene in a list file and appends the verdicts to results/summary.txt.

  python run_cutscenes.py LIST.txt [--full-only | --skip-only] [NAME ...]

LIST lines: NAME STATE X Y Z [extra cutscene_test options]  (# comments allowed); X Y Z is the trigger centre."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]; listfile = args.pop(0)
flags = [a for a in args if a.startswith("--")]; only = {a for a in args if not a.startswith("--")}
out = open(os.path.join(HERE, "results", "summary.txt"), "a", encoding="utf-8")
for line in open(os.path.join(HERE, listfile), encoding="utf-8"):
    s = line.split("#", 1)[0].split()
    if len(s) < 5 or (only and s[0] not in only): continue
    name, state = s[0], s[1]
    if not os.path.exists(os.path.join(HERE, "states", state + ".p2s")):
        print(f"{name}: SKIPPED (no state for {state})", flush=True); continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "cutscene_test.py"), name, state, *s[2:5], *s[5:], *flags], capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.strip().startswith(("full", "skip", "=>"))] or (r.stdout + r.stderr).splitlines()[-4:]
    text = f"{name}:\n  " + "\n  ".join(lines)
    print(text, flush=True); out.write(text + "\n"); out.flush()
