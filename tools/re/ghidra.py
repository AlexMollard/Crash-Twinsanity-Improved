"""Drives the headless Ghidra project (tools/ghidra/project) that holds Crash Twinsanity's reversed executable.

  python tools/re/ghidra.py query xref:0x309908 decomp:0x116ea8 callers:0x116ea8
  python tools/re/ghidra.py export            # Ghidra project -> tools/re/db/  (symbols, comments, types)
  python tools/re/ghidra.py import [dry]      # tools/re/db/  -> Ghidra project
  python tools/re/ghidra.py decompile         # whole program -> tools/ghidra/SLES_525.68.c
  python tools/re/ghidra.py run Script.java [args...]

tools/re/db is the part that lives in git: the Ghidra project is a binary blob rebuilt from twinsanity-reversed's
.gar, so every name we work out has to be exported or it is lost on the next upstream update.

Setup (not in git): Ghidra 11.2.1 in tools/ghidra/ghidra_11.2.1_PUBLIC with the ghidra-emotionengine-reloaded
extension, and tools/twinsanity-reversed/Twinsanity_2024_11_05.gar (git lfs pull) restored into
tools/ghidra/project.  See wiki/docs/modding/reverse-engineering.md."""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GHIDRA = os.path.join(HERE, "..", "ghidra")
DB = os.path.join(HERE, "db")
PROGRAM = "SLES_525.68"


def headless(script, args=(), write=False, analyze=False, timeout=None):
    """Run one Ghidra script over the program. Returns the headless log (stdout and stderr together)."""
    cmd = [os.path.join(GHIDRA, "ghidra_11.2.1_PUBLIC", "support", "analyzeHeadless.bat"),
           os.path.join(GHIDRA, "project"), "Twinsanity", "-process", PROGRAM]
    if not analyze: cmd.append("-noanalysis")
    if not write: cmd.append("-readOnly")
    cmd += ["-scriptPath", HERE, "-postScript", script, *map(str, args)]
    p = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
    return p.stdout + p.stderr


def query(*cmds):
    """xref:ADDR / callers:ADDR / decomp:ADDR against the program, as one headless run."""
    out = tempfile.mktemp(suffix=".txt")
    log = headless("Query.java", [out, *cmds])
    if not os.path.exists(out): raise SystemExit(log[-4000:])
    text = open(out, encoding="utf-8").read(); os.remove(out)
    return text


def load_symbols(path=None):
    """{name: address} and {address: name} from db/symbols.tsv."""
    by_name, by_addr = {}, {}
    p = path or os.path.join(DB, "symbols.tsv")
    if not os.path.exists(p): return by_name, by_addr
    for line in open(p, encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        addr, kind, name = line.split("\t")[:3]
        a = int(addr, 16)
        by_name.setdefault(name, a)
        by_addr.setdefault(a, name)
    return by_name, by_addr


_FIELD = re.compile(r"^( *)undefined (field\d+)_0x([0-9a-f]+);$")


def collapse_undefined(path):
    """Ghidra writes one line per unknown byte in a struct; a few structs are thousands of lines of them.
    Fold each run into one array field so the exported header stays readable (and small enough for git)."""
    out, run = [], []
    def flush():
        if not run: return
        if len(run) < 3: out.extend(l for l, _ in run); return
        (first, m) = run[0]
        out.append(f"{m.group(1)}undefined {m.group(2)}_0x{m.group(3)}[{len(run)}];")
    for line in open(path, encoding="utf-8").read().splitlines():
        m = _FIELD.match(line)
        if m and (not run or run[-1][1].group(1) == m.group(1)):
            run.append((line, m)); continue
        flush(); run = [(line, m)] if m else []
        if not m: out.append(line)
    flush()
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(out)


def _tail(log, n=25):
    return "\n".join(l.strip() for l in log.splitlines() if l.strip())[-4000:] if "SCRIPT ERROR" in log or ".java:" in log \
        else "\n".join(l for l in log.splitlines() if "GhidraScript)" in l or "ERROR" in l)[-4000:]


def main(argv):
    if not argv: raise SystemExit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "query":
        print(query(*rest))
    elif cmd == "export":
        os.makedirs(DB, exist_ok=True)
        print(_tail(headless("ExportDb.java", [DB])))
        n = collapse_undefined(os.path.join(DB, "types.h"))
        print(f"types.h collapsed to {n} lines")
    elif cmd == "import":
        print(_tail(headless("ImportDb.java", [DB, *rest], write="dry" not in rest)))
    elif cmd == "decompile":
        out = os.path.join(GHIDRA, "SLES_525.68.c")
        print(_tail(headless("DecompileAll.java", [out], timeout=7200)))
        print(f"wrote {out}")
    elif cmd == "run":
        print(_tail(headless(rest[0], rest[1:], write=True)))
    else:
        print(query(*argv))                            # bare "xref:..." style, as the old script took


if __name__ == "__main__":
    main(sys.argv[1:])
