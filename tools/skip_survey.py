"""Which of the developers' own cutscene skips are still unreachable?

This mod's whole cutscene-skip feature is the restoration of skip branches the developers wrote and then cut:
a state holding a condition-572 rule that routes to a `..._CUTSCENE_SKIP` script, which nothing reaches any
more. Sixteen have been reconnected by recipes in `mod/levels/`. This asks what is left, by reading the built
mod rather than the original disc - so a skip a recipe has already restored comes back LIVE and only the
genuinely unreachable ones are listed.

`twinsdump <level> cond 572` marks each rule LIVE or orphan. That is the whole answer; the work here is
running it over every level in an image and not lying about which image.

The scan asserts a known-restored skip first. Pointed at the original disc by mistake, every restored skip
looks orphaned again and the report would read like a pile of new work - so if the Iceberg Lab skip, shipped
in mod/levels/icelab.ops, does not come back LIVE, this refuses to report.

  python tools/skip_survey.py                    # the built test.iso, or the original if there is none
  python tools/skip_survey.py --iso original     # the untouched disc: what the developers left behind
"""
import argparse, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import isotools as it
from psm_extract import source_iso, archive_names

TWINSDUMP = os.path.join(ROOT, "tools", "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
TEST_ISO = os.path.join(ROOT, "tools", "rig", "test.iso")
ROW = re.compile(r"^(\d+)\t(\S+)\t(LIVE|orphan)\t(.*)$")

def rules(path):
    r = subprocess.run([TWINSDUMP, path, "cond", "572"], capture_output=True, text=True)
    if "Unhandled Exception" in (r.stdout + r.stderr):
        raise RuntimeError(f"twinsdump cond crashed on {os.path.basename(path)}")
    out = []
    for line in r.stdout.splitlines():
        m = ROW.match(line)
        if m: out.append((int(m.group(1)), m.group(2), m.group(3), m.group(4).strip()))
    return out

def prompted(path, script_ids):
    """Of these scripts, which draw the hold-Triangle hint?

    A restored skip and its on-screen prompt are two separate recipes, and mod/skip_prompt.ops names the
    levels it covers by hand. Cover a scene in mod/levels and forget the prompt line and the player can skip
    the scene without ever being told - which is exactly what shipping roofcor2's skip did, because only
    roof01 was in the prompt list."""
    if not script_ids: return set()
    # `scripts <regex>` matches the script's *name*, not its id, so asking for "^(6375)$" silently matches
    # nothing and every skip looks unprompted. Dump them all and pick the ids out.
    r = subprocess.run([TWINSDUMP, path, "scripts", "."], capture_output=True, text=True)
    out, cur = set(), None
    for line in r.stdout.splitlines():
        m = re.match(r"^=== script (\d+) ", line)
        if m: cur = int(m.group(1))
        elif cur in script_ids and "BottomTextDisplay" in line: out.add(cur)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", default="built", choices=["built", "original"])
    ap.add_argument("levels", nargs="*")
    o = ap.parse_args()
    iso = TEST_ISO if (o.iso == "built" and os.path.exists(TEST_ISO)) else source_iso()
    print(f"reading {os.path.basename(iso)}\n", flush=True)

    wanted = [a.lower() for a in o.levels]
    names = [n for n in archive_names(iso) if n.lower().endswith(".rm2")]
    if wanted:
        names = [n for n in names if os.path.basename(n).lower().rsplit(".", 1)[0] in wanted]

    live, orphan, silent = [], [], []
    with open(iso, "rb") as f, tempfile.TemporaryDirectory() as work:
        files = it.iso_files(f)
        for n in sorted(names):
            level = os.path.basename(n).rsplit(".", 1)[0]
            p = os.path.join(work, os.path.basename(n))
            open(p, "wb").write(it.archive_file(f, files, n))
            try:
                rs = rules(p)
                for sid, script, status, detail in rs:
                    (live if status == "LIVE" else orphan).append((level, sid, script, detail))
                # Only states that actually play a cutscene want a prompt - that is the rule `skipprompt
                # auto` uses too. Condition 572 also appears in ordinary behaviour scripts as an alternative
                # transition: COM_CORTEX_DOCAMOK_EARTH_PHASE2 carries one in forty levels, and prompting
                # there would put "hold Triangle to skip" on top of normal play.
                plays = set()
                for sid, _, st, d in rs:
                    if st != "LIVE": continue
                    m = re.match(r"state \d+ \(runs ([^)]+)\)", d)
                    if m and m.group(1) != "-": plays.add(sid)
                have = prompted(p, plays)
                for sid, script, status, _ in rs:
                    if status == "LIVE" and sid in plays and sid not in have:
                        silent.append((level, sid, script))
            except RuntimeError as e:
                print(f"  !! {e}", flush=True)
            os.remove(p)

    if iso == TEST_ISO:
        ok = any(l == "labext" and "ICELAB_CUTSCENE_DIRECTOR" in s for l, _, s, _ in live)
        print(f"validation: the shipped Iceberg Lab skip reads {'LIVE' if ok else 'ORPHANED'} - "
              + ("this is the built mod\n" if ok else "this is NOT the built mod, every restored skip would look "
                 "unreachable again and the list below would be nonsense\n"))
        if not ok: return

    print(f"{len(live)} condition-572 rules are reachable, {len(orphan)} are orphaned\n")
    seen = set()
    for level, sid, script, detail in orphan:
        key = (level, script)
        if key in seen: continue
        seen.add(key)
        print(f"  {level:12s} {sid:5d}  {script}")
        print(f"               {detail}")
    if not orphan:
        print("  nothing left: every skip the developers wrote is reachable in this build")

    # A skip with no prompt is a skip the player never learns about. The two are separate recipes and
    # mod/skip_prompt.ops names its levels by hand, so one can ship without the other.
    print()
    print(f"{len(silent)} reachable skip(s) with no hold-Triangle prompt")
    seen2 = set()
    for level, sid, script in silent:
        if (level, script) in seen2: continue
        seen2.add((level, script))
        print(f"  {level:12s} {sid:5d}  {script}")
    if not silent:
        print("  none: every reachable skip tells the player it is there")

if __name__ == "__main__":
    main()
