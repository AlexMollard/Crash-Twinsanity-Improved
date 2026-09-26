"""Builds the [Modded] ISO from the original PAL Crash Twinsanity disc (SLES-52568).

  python tools/build_mod.py [--src ORIGINAL.iso] [--out OUT.iso] [--include DIR ...]

Put the original ISO in the project folder (any file name - it is recognised by its PCSX2 CRC) and run this.
It applies, in order:
  1. mod/elf_patches.txt   executable patches (480p/60Hz, cutscene skip, ...)
  2. mod/levels/*.ops      level script edits (plus any --include DIR/*.ops, e.g. experimental recipes)
  3. mod/skip_prompt.ops   the "hold triangle to skip" hint on every skippable cutscene
  4. mod/text.txt          game text lines (the hint's text)
  5. tools/materials.py    crate materials receive Crash's shadow
  6. disc layout           CRASH.BD (level data) moves to the end of the image, where the drive reads fastest
then writes "PCSX2 patches/SLES-52568_<CRC>.pnach" for the new build from mod/pcsx2/modded.pnach.
The source ISO is only read. The output is written to a temporary file and swapped in at the end."""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import isotools as it
import asmpatch
import elfpatch
sys.path.insert(0, os.path.join(HERE, "re"))
import ghidra as re_ghidra
sys.path.insert(0, os.path.join(HERE, "rig"))
import rm2splice
import materials

TWINSDUMP = os.path.join(HERE, "twinsdump", "bin", "Release", "net48", "twinsdump.exe")
EDITOR = os.path.join(HERE, "twinsanity-editor")
LIB_DLL = os.path.join(EDITOR, "Twinsanity", "bin", "Release", "Twinsanity.dll")

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

def patch_editor():
    """Apply tools/patches/*.patch to the Twinsanity Editor submodule if they are not in it yet.

    The library drops a few fields it reads (see tools/patches/texture-preserve-reserved.patch), which makes a
    full re-save lossy, and one of them is worse than lossy - CollisionSurface wrote four bytes where two were
    read, so every level saved through the editor came back with its collision data shifted.

    These now exist as three commits in the submodule, but the submodule is still pinned at upstream until
    that history is pushed to a fork (tools/fork_editor.py finishes that). Until then a fresh clone checks out
    upstream's code and needs the patches; afterwards the reverse-apply check below finds the fixes already
    present and this does nothing. Either way it is a no-op on an already-correct tree."""
    changed = False
    for patch in sorted(glob.glob(os.path.join(HERE, "patches", "*.patch"))):
        check = subprocess.run(["git", "apply", "--reverse", "--check", patch], cwd=EDITOR, capture_output=True)
        if check.returncode == 0: continue                # already applied
        applied = subprocess.run(["git", "apply", patch], cwd=EDITOR, capture_output=True, text=True)
        if applied.returncode:
            raise SystemExit(f"could not apply {os.path.basename(patch)} to the editor submodule:\n{applied.stderr}")
        print(f"  applied {os.path.basename(patch)} to the editor submodule")
        changed = True                                    # the library has to be rebuilt afterwards
    return changed


def update_editor():
    """Bring an older clone's editor submodule up to the pinned commit, which now lives on our fork.

    A clone made while the pin was on upstream still fetches from upstream and has tools/patches/*.patch applied
    on top, so a plain pull leaves it behind. Only a submodule strictly behind the pin is moved: one that is ahead
    (local editor work) is left alone."""
    git = lambda *a, cwd=EDITOR: subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True)
    pinned = git("ls-tree", "HEAD", "tools/twinsanity-editor", cwd=ROOT).stdout.split()
    current = git("rev-parse", "HEAD").stdout.strip()
    if len(pinned) < 3 or pinned[2] == current: return False
    print("updating the Twinsanity Editor submodule...")
    git("submodule", "sync", "--", "tools/twinsanity-editor", cwd=ROOT)
    git("fetch", "origin")
    if git("merge-base", "--is-ancestor", current, pinned[2]).returncode: return False
    for patch in sorted(glob.glob(os.path.join(HERE, "patches", "*.patch")), reverse=True):
        if git("apply", "--reverse", "--check", patch).returncode == 0:
            git("apply", "--reverse", patch)              # undo what patch_editor() applied, so the checkout is clean
    subprocess.run(["git", "submodule", "update", "tools/twinsanity-editor"], cwd=ROOT, check=True)
    return True

def ensure_tools():
    src_newer = lambda out, *srcs: not os.path.exists(out) or any(os.path.getmtime(s) > os.path.getmtime(out) for s in srcs)
    if not os.path.exists(os.path.join(EDITOR, "Twinsanity", "Twinsanity.csproj")):
        print("fetching the Twinsanity Editor submodule...")
        subprocess.run(["git", "submodule", "update", "--init", "tools/twinsanity-editor"], cwd=ROOT, check=True)
    elif update_editor() and os.path.exists(LIB_DLL):
        os.remove(LIB_DLL)
    if patch_editor() and os.path.exists(LIB_DLL):
        os.remove(LIB_DLL)                                # force the rebuild below
    def msbuild(project):                                 # Visual Studio's MSBuild - no .NET SDK needed
        vswhere = os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe")
        found = subprocess.run([vswhere, "-latest", "-prerelease", "-requires", "Microsoft.Component.MSBuild", "-find", r"MSBuild\**\Bin\MSBuild.exe"],
                               capture_output=True, text=True).stdout.strip().splitlines() if os.path.exists(vswhere) else []
        if not found: raise SystemExit("Building the level tools needs Visual Studio (MSBuild) with .NET Framework 4.8.")
        subprocess.run([found[0], project, "-p:Configuration=Release", "-v:minimal", "-nologo"], check=True)
    if not os.path.exists(LIB_DLL):
        print("building the Twinsanity Editor library...")
        msbuild(os.path.join(EDITOR, "Twinsanity", "Twinsanity.csproj"))
    twinsdump = os.path.join(HERE, "twinsdump")
    if src_newer(TWINSDUMP, os.path.join(twinsdump, "Program.cs"), os.path.join(twinsdump, "twinsdump.csproj"), LIB_DLL):
        print("building twinsdump...")
        shutil.rmtree(os.path.join(twinsdump, "obj"), ignore_errors=True)  # left over from the old SDK-style build
        msbuild(os.path.join(twinsdump, "twinsdump.csproj"))

def read_elf_patches(path):
    patches, group = [], ""
    for line in open(path, encoding="utf-8"):
        s = line.split("#", 1)[0].strip()
        if s.startswith("["): group = s.strip("[]"); continue
        if s:
            a, o, n = s.split()[:3]; patches.append((int(a, 16), int(o, 16), int(n, 16), group))
    return patches

def build_elf(dst, files, include):
    """Patch the executable in DST: the raw word patches from mod/elf_patches.txt, then the assembly in
    mod/asm/*.s, which may both replace words in place and add code to the cave past the end of .bss."""
    elf = elfpatch.Elf(it.read_file(dst, files, it.ELF_PATH))
    patches = read_elf_patches(os.path.join(ROOT, "mod", "elf_patches.txt"))
    for va, orig, new, note in patches: elf.patch(va, orig, new, note)
    for g in dict.fromkeys(p[3] for p in patches): print(f"  {g}: {sum(1 for p in patches if p[3] == g)} words")

    symbols, _ = re_ghidra.load_symbols()
    dirs = [os.path.join(ROOT, "mod", "asm")] + [os.path.join(d, "asm") for d in include]
    cave, asm_patches, labels, paths = asmpatch.load([d for d in dirs if os.path.isdir(d)],
                                                     elfpatch.CAVE_CODE, symbols)
    for addr, originals, code, where in asm_patches:
        for i, original in enumerate(originals):
            elf.patch(addr + 4 * i, original, int.from_bytes(code[4 * i:4 * i + 4], "little"), where)
    elf.add_cave(cave)
    for p in paths: print(f"  {os.path.relpath(p, ROOT)}")
    print(f"  cave: {len(cave)} of {elfpatch.CAVE_SIZE - elfpatch.CAVE_GUARD} bytes used at {elfpatch.CAVE_CODE:08X}"
          f", {len(asm_patches)} hook(s), heap now starts at {elfpatch.CAVE_BASE + elfpatch.CAVE_SIZE:08X}")
    it.write_elf(dst, bytes(elf), log=print)


def level_edits(src_iso, recipe_files, work):
    """{archive name: new bytes} from twinsdump edit recipes applied to the original files."""
    by_file = {}                                          # a recipe may cover several levels: each "file" line starts a section
    for r in recipe_files:
        target = None
        for l in open(r, encoding="utf-8").read().splitlines():
            if l.startswith("file "):                     # grouped case-insensitively, as the archive names are
                name = l.split(None, 1)[1].strip()
                target = next((k for k in by_file if k.lower() == name.lower()), name); by_file.setdefault(target, []).append((r, [])); continue
            if not l.split("#", 1)[0].strip(): continue
            if target is None: raise SystemExit(f"{r}: ops before the first 'file <archive path>' line")
            by_file[target][-1][1].append(l)
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

def text_edits(src_iso, path):
    """{archive name: new bytes} from mod/text.txt: ARCHIVE_FILE <tab> LINE_INDEX <tab> EXPECTED <tab> NEW (Latin-1 in the game)."""
    edits = {}
    for l in open(path, encoding="utf-8").read().splitlines():
        if not l.strip() or l.startswith("#"): continue
        name, idx, expected, new = l.split("\t")
        edits.setdefault(name, []).append((int(idx), expected, new))
    reps = {}
    with open(src_iso, "rb") as f:
        files = it.iso_files(f)
        for name, changes in edits.items():
            lines = it.archive_file(f, files, name).split(b"\r\n")
            for idx, expected, new in changes:
                if lines[idx] != expected.encode("latin-1"):
                    raise SystemExit(f"{name} line {idx}: expected {expected!r}, found {lines[idx]!r} - wrong source disc?")
                lines[idx] = new.encode("latin-1")
            reps[name] = b"\r\n".join(lines)
            print(f"  {name}: {len(changes)} line(s)")
    return reps

def material_fixes(src_iso, reps):
    """Crate materials receive Crash's shadow (see tools/materials.py). Edits to files already in REPS are made there;
    the rest are returned as {archive name: {offset: byte}} for patch_archive_bytes after the archive is rebuilt."""
    later, total, count = {}, 0, 0
    if os.environ.get("CRASHMOD_NO_CRATE_SHADOWS"):     # A/B testing only: build without this fix
        print("  skipped (CRASHMOD_NO_CRATE_SHADOWS)"); return later
    with open(src_iso, "rb") as f:
        files = it.iso_files(f)
        bh = it.read_file(f, files, "/CRASH6/CRASH.BH"); bd_lba = files["/CRASH6/CRASH.BD"][0]
        for name, off, size, _ in it.parse_bh(bh):
            if not name.lower().endswith(".rm2"): continue
            key = next((k for k in reps if k.lower() == name.lower()), None)
            if key is not None:
                data = bytearray(reps[key]); offs = materials.crate_shadow_offsets(data)
                for o in offs: data[o] = 1
                reps[key] = bytes(data)
            else:
                f.seek(bd_lba * it.SECTOR + off); offs = materials.crate_shadow_offsets(f.read(size))
                if offs: later[name] = {o: 1 for o in offs}
            if offs: count += 1; total += len(offs)
    print(f"  crate materials receive shadows: {total} shaders in {count} level files")
    return later

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
    recipes.append(os.path.join(ROOT, "mod", "skip_prompt.ops"))   # last: it prompts on the skips the recipes above restore

    tmp = out + ".building"
    with tempfile.TemporaryDirectory() as work:
        step("Level edits"); reps = level_edits(src, recipes, work)
        step("Text"); reps.update(text_edits(src, os.path.join(ROOT, "mod", "text.txt")))
        step("Materials"); mat_patches = material_fixes(src, reps)
        step("Copying source ISO"); shutil.copyfile(src, tmp); print("  ok")
        with open(src, "rb") as s, open(tmp, "r+b") as d:
            files = it.iso_files(d)
            step("Executable patches")
            build_elf(d, files, o.include)
            step("Disc layout")                        # level data to the fast outer edge of the disc (and room to grow)
            it.archive_last(d, log=print)
            step("Archive"); it.rebuild_archive(s, d, reps, log=print)
            it.patch_archive_bytes(d, mat_patches)
    crc = it.iso_crc(tmp)
    try: os.replace(tmp, out)
    except PermissionError:
        raise SystemExit(f"Could not replace {out} - close PCSX2 (or anything else using the ISO) and run again.\nThe new build is at {tmp}")
    step(f"Done: {os.path.basename(out)}  (PCSX2 CRC {crc})")
    if not o.no_pcsx2_files: write_pcsx2_files(crc)

if __name__ == "__main__":
    main()
