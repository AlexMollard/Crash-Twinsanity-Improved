"""Builds the [Modded] ISO from the original PAL Crash Twinsanity disc (SLES-52568).

  python tools/build_mod.py [--src ORIGINAL.iso] [--out OUT.iso] [--include DIR ...]

Put the original ISO in the project folder (any file name - it is recognised by its PCSX2 CRC) and run this.
It applies, in order:
  1. mod/elf_patches.txt   executable patches (480p/60Hz, cutscene skip, ...)
  2. mod/levels/*.ops      level script edits (plus any --include DIR/*.ops, e.g. experimental recipes)
then writes "PCSX2 patches/SLES-52568_<CRC>.pnach" for the new build from mod/pcsx2/modded.pnach.
The source ISO is only read. The output is written to a temporary file and swapped in at the end."""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import isotools as it
sys.path.insert(0, os.path.join(HERE, "rig"))
import rm2splice

TWINSDUMP = os.path.join(HERE, "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EDITOR = os.path.join(HERE, "twinsanity-editor")
LIB_DLL = os.path.join(EDITOR, "Twinsanity", "bin", "Release", "Twinsanity.dll")
# Moved to the end of the image so CRASH.BD can grow (~13 MB instead of the original ~2 KB of slack). The game finds
# its files by name (sceCdSearchFile), so only the directory records change.
RELOCATE = ["/CRASH6/ENGLISH.MH", "/CRASH6/ENGLISH.MB"]

def step(msg): print(f"\n== {msg}", flush=True)

def find_source():
    found = []
    for p in sorted(glob.glob(os.path.join(ROOT, "*.iso"))):
        try:
            if it.iso_crc(p) == it.ORIGINAL_CRC: found.append(p)
        except Exception: pass
    if not found:
        raise SystemExit(f"No original PAL ISO found in {ROOT}.\nPut your Crash Twinsanity (Europe) SLES-52568 ISO there (PCSX2 CRC {it.ORIGINAL_CRC}).")
    return found[0]

def ensure_tools():
    src_newer = lambda out, *srcs: not os.path.exists(out) or any(os.path.getmtime(s) > os.path.getmtime(out) for s in srcs)
    if not os.path.exists(os.path.join(EDITOR, "Twinsanity", "Twinsanity.csproj")):
        print("fetching the Twinsanity Editor submodule...")
        subprocess.run(["git", "submodule", "update", "--init", "tools/twinsanity-editor"], cwd=ROOT, check=True)
    if not os.path.exists(LIB_DLL):
        vswhere = os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe")
        msbuild = subprocess.run([vswhere, "-latest", "-prerelease", "-requires", "Microsoft.Component.MSBuild", "-find", r"MSBuild\**\Bin\MSBuild.exe"],
                                 capture_output=True, text=True).stdout.strip().splitlines() if os.path.exists(vswhere) else []
        if not msbuild: raise SystemExit("Building the Twinsanity Editor library needs Visual Studio (MSBuild) with .NET Framework 4.8.")
        print("building the Twinsanity Editor library...")
        subprocess.run([msbuild[0], os.path.join(EDITOR, "Twinsanity", "Twinsanity.csproj"), "-p:Configuration=Release", "-v:minimal", "-nologo"], check=True)
    if src_newer(TWINSDUMP, os.path.join(HERE, "twinsdump", "Program.cs"), LIB_DLL):
        print("building twinsdump...")
        subprocess.run(["dotnet", "build", os.path.join(HERE, "twinsdump", "twinsdump.csproj"), "-c", "Release", "-nologo", "-v", "q"], check=True)

def read_elf_patches(path):
    patches, group = [], ""
    for line in open(path, encoding="utf-8"):
        s = line.split("#", 1)[0].strip()
        if s.startswith("["): group = s.strip("[]"); continue
        if s:
            a, o, n = s.split()[:3]; patches.append((int(a, 16), int(o, 16), int(n, 16), group))
    return patches

def level_edits(src_iso, recipe_files, work):
    """{archive name: new bytes} from twinsdump edit recipes applied to the original files."""
    by_file = {}
    for r in recipe_files:
        lines = open(r, encoding="utf-8").read().splitlines()
        target = next((l.split(None, 1)[1].strip() for l in lines if l.startswith("file ")), None)
        if not target: raise SystemExit(f"{r}: missing 'file <archive path>' line")
        by_file.setdefault(target, []).append((r, [l for l in lines if not l.startswith("file ")]))
    reps = {}
    with open(src_iso, "rb") as f:
        files = it.iso_files(f)
        for target, recipes in by_file.items():
            orig = it.archive_file(f, files, target)
            d = os.path.join(work, re.sub(r"[\\/:]", "_", target)); os.makedirs(d)
            orig_path = os.path.join(d, "original"); open(orig_path, "wb").write(orig)
            ops = os.path.join(d, "ops.txt")
            open(ops, "w", encoding="utf-8").write("\n".join(l for _, ls in recipes for l in ls) + "\n")
            out = subprocess.run([TWINSDUMP, orig_path, "edit", ops, d], capture_output=True, text=True)
            if out.returncode: raise SystemExit(f"twinsdump failed on {target}:\n{out.stdout}{out.stderr}")
            data = orig
            for binf in sorted(glob.glob(os.path.join(d, "*.bin"))):
                sid = int(os.path.splitext(os.path.basename(binf))[0])
                data, delta = rm2splice.splice(data, [10, 1, sid], open(binf, "rb").read())
            print(f"  {target}: {', '.join(os.path.basename(r) for r, _ in recipes)} ({len(data) - len(orig):+d} bytes)")
            reps[target] = data
    return reps

def write_pcsx2_files(crc):
    pdir = os.path.join(ROOT, "PCSX2 patches")
    template = open(os.path.join(ROOT, "mod", "pcsx2", "modded.pnach"), encoding="utf-8").read()
    new = os.path.join(pdir, f"SLES-52568_{crc}.pnach")
    open(new, "w", encoding="utf-8").write(template.replace("{CRC}", crc))
    for old in glob.glob(os.path.join(pdir, "SLES-52568_*.pnach")):
        c = os.path.basename(old)[11:19]
        if c not in (crc, it.ORIGINAL_CRC): os.remove(old); print(f"  removed stale {os.path.basename(old)}")
    print(f"  wrote {os.path.relpath(new, ROOT)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src"); ap.add_argument("--out"); ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--no-pcsx2-files", action="store_true", help="don't write PCSX2 patch files (used for test builds)")
    o = ap.parse_args()
    src = o.src or find_source()
    out = o.out or os.path.join(ROOT, os.path.splitext(os.path.basename(src))[0] + " [Modded].iso")
    if os.path.abspath(src) == os.path.abspath(out): raise SystemExit("output would overwrite the source ISO")
    print(f"source: {src}\noutput: {out}")

    step("Tools"); ensure_tools(); print("  ok")
    recipes = sorted(glob.glob(os.path.join(ROOT, "mod", "levels", "*.ops")))
    for d in o.include: recipes += sorted(glob.glob(os.path.join(d, "*.ops")))

    tmp = out + ".building"
    with tempfile.TemporaryDirectory() as work:
        step("Level edits"); reps = level_edits(src, recipes, work)
        step("Copying source ISO"); shutil.copyfile(src, tmp); print("  ok")
        with open(src, "rb") as s, open(tmp, "r+b") as d:
            files = it.iso_files(d)
            step("Executable patches")
            patches = read_elf_patches(os.path.join(ROOT, "mod", "elf_patches.txt")); it.patch_elf(d, files, patches)
            for g in dict.fromkeys(p[3] for p in patches): print(f"  {g}: {sum(1 for p in patches if p[3] == g)} words")
            step("Making room for the archive")        # the English speech bank sits right after CRASH.BD
            it.relocate_to_end(d, RELOCATE, log=print)
            step("Archive"); it.rebuild_archive(s, d, reps, log=print)
    crc = it.iso_crc(tmp)
    try: os.replace(tmp, out)
    except PermissionError:
        raise SystemExit(f"Could not replace {out} - close PCSX2 (or anything else using the ISO) and run again.\nThe new build is at {tmp}")
    step(f"Done: {os.path.basename(out)}  (PCSX2 CRC {crc})")
    if not o.no_pcsx2_files: write_pcsx2_files(crc)

if __name__ == "__main__":
    main()
