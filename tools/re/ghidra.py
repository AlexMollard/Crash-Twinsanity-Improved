"""Runs Query.java headless against the restored twinsanity-reversed Ghidra project (tools/ghidra/project).

  python tools/re/ghidra.py xref:0x309908 decomp:0x116ea8 callers:0x116ea8

Setup (not in git): Ghidra 11.2.1 in tools/ghidra/ghidra_11.2.1_PUBLIC with the ghidra-emotionengine-reloaded extension,
and tools/twinsanity-reversed/Twinsanity_2024_11_05.gar (git lfs pull) unpacked into tools/ghidra/project/Twinsanity.rep."""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GHIDRA = os.path.join(HERE, "..", "ghidra")

def query(*cmds):
    out = tempfile.mktemp(suffix=".txt")
    log = subprocess.run([os.path.join(GHIDRA, "ghidra_11.2.1_PUBLIC", "support", "analyzeHeadless.bat"),
                          os.path.join(GHIDRA, "project"), "Twinsanity", "-process", "SLES_525.68", "-noanalysis", "-readOnly",
                          "-scriptPath", HERE, "-postScript", "Query.java", out, *cmds],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if not os.path.exists(out): raise SystemExit(log.stdout[-3000:] + log.stderr[-3000:])
    text = open(out, encoding="utf-8").read(); os.remove(out)
    return text

if __name__ == "__main__":
    print(query(*sys.argv[1:]))
