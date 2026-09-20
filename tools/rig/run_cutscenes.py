"""Runs cutscene_test for every cutscene in a list file and appends the verdicts to results/summary.txt.

  python run_cutscenes.py LIST.txt [--full-only | --skip-only] [NAME ...]

LIST lines: NAME STATE X Y Z [extra cutscene_test options]  (# comments allowed); X Y Z is the trigger centre.

A line with too few fields used to be skipped in the same silent `continue` as a line filtered out by NAME, so a
list in the wrong format ran nothing and reported nothing - which is how every scene in cutscenes.txt (11 of them,
written as NAME STATE X Z with no Y) went untested without anyone noticing. Short lines are now reported and
counted, and the run ends by saying how many it could not parse."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]; listfile = args.pop(0)
flags = [a for a in args if a.startswith("--")]; only = {a for a in args if not a.startswith("--")}
out = open(os.path.join(HERE, "results", "summary.txt"), "a", encoding="utf-8")
unparsed = []
for lineno, line in enumerate(open(os.path.join(HERE, listfile), encoding="utf-8"), 1):
    s = line.split("#", 1)[0].split()
    if not s: continue
    if len(s) < 5:                                  # wrong format is an error, not a quiet skip
        unparsed.append((lineno, " ".join(s)))
        print(f"line {lineno}: needs NAME STATE X Y Z, got {len(s)} fields: {' '.join(s)}", flush=True)
        continue
    if only and s[0] not in only: continue
    name, state = s[0], s[1]
    if not os.path.exists(os.path.join(HERE, "states", state + ".p2s")):
        print(f"{name}: SKIPPED (no state for {state})", flush=True); continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "cutscene_test.py"), name, state, *s[2:5], *s[5:], *flags], capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.strip().startswith(("full", "skip", "=>"))] or (r.stdout + r.stderr).splitlines()[-4:]
    text = f"{name}:\n  " + "\n  ".join(lines)
    print(text, flush=True); out.write(text + "\n"); out.flush()

if unparsed:
    msg = (f"\n{len(unparsed)} line(s) in {listfile} could not be parsed and were NOT tested - "
           f"a run that reports nothing is not a run that passed:\n  "
           + "\n  ".join(f"line {n}: {t}" for n, t in unparsed))
    print(msg, flush=True); out.write(msg + "\n")
out.close()
