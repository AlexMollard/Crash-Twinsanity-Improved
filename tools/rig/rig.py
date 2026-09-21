"""Crash Twinsanity test rig: drives an isolated, portable PCSX2 (tools/pcsx2-test) over PINE.

  rig.py start [--level PATH] [--iso modded|original] [--speed X]   launch test PCSX2 (warp New Game to PATH)
  rig.py stop                                   close the test PCSX2
  rig.py warp PATH                              make the next New Game start in level PATH
  rig.py level NAME [PATH] [--fresh]            go to level: states/NAME.p2s, or warp to PATH (~20s)
  rig.py pos | state | tp X Y Z                  Crash's position / game-flow state + cutscene check / teleport
  rig.py goto X Z [RADIUS]                      walk him there on the stick - prefer this to tp (see goto())
  rig.py status                                 emulator status / game
  rig.py press BTN[+BTN..] [--frames N]         press buttons via the virtual pad (default 6 frames)
  rig.py hold BTN[+BTN..] | release             hold / release buttons
  rig.py stick LX LY                            left stick, -1..1 (release resets it)
  rig.py shot FILE.png                          screenshot of the test game window
  rig.py until REF.png [--press BTN]          press BTN until the screen matches ref/REF.png
  rig.py diff REF.png                           how far the screen is from ref/REF.png
  rig.py read ADDR [COUNT] | write ADDR VALUE   EE memory (hex), 32-bit words
  rig.py save SLOT | load SLOT                  PCSX2 save states (test instance only)
  rig.py seq FILE                               run commands from a file (one per line, 'wait S' allowed)

Buttons: cross circle square triangle start select up down left right l1 r1 l2 r2 l3 r3
Only the test instance is touched; the user's PCSX2 and settings are never modified."""
import argparse, ctypes, os, shutil, socket, struct, subprocess, sys, time, zlib
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
TEST = os.path.join(MOD, "tools", "pcsx2-test")
EXE = os.path.join(TEST, "pcsx2-qt.exe")
ISOS = {"modded": os.path.join(MOD, "Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It) [Modded].iso"),
        "original": os.path.join(MOD, "Crash Twinsanity (Europe, Australia) (En,Fr,De,Es,It).iso"),
        "test": os.path.join(HERE, "test.iso"),             # build_mod.py --out tools/rig/test.iso [--include ...]
        "re": os.path.join(MOD, "work", "re", "test_re.iso")}   # a second build to drive alongside it, without sharing a filename
PORT = 28012
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import testhooks as th
import isotools

# ---------------------------------------------------------------- PINE
class _Pine:
    def __init__(self, timeout=30.0):
        self.s = socket.create_connection(("127.0.0.1", PORT), timeout=timeout)
    def _call(self, payload):
        self.s.sendall(struct.pack("<I", len(payload) + 4) + payload)
        hdr = self._recv(4); size = struct.unpack("<I", hdr)[0]
        body = self._recv(size - 4)
        if body[0] != 0: raise RuntimeError("PINE call failed")
        return body[1:]
    def _recv(self, n):
        b = b""
        while len(b) < n:
            chunk = self.s.recv(n - len(b))
            if not chunk: raise ConnectionError("PINE closed")
            b += chunk
        return b
    def r8(self, a):  return self._call(struct.pack("<BI", 0, a))[0]
    def r32(self, a): return struct.unpack("<I", self._call(struct.pack("<BI", 2, a)))[0]
    def w8(self, a, v):  self._call(struct.pack("<BIB", 4, a, v & 0xFF))
    def w32(self, a, v): self._call(struct.pack("<BII", 6, a, v & 0xFFFFFFFF))
    def save(self, slot): self._call(struct.pack("<BB", 9, slot))
    def load(self, slot): self._call(struct.pack("<BB", 10, slot))
    def _str(self, op):
        d = self._call(struct.pack("<B", op)); n = struct.unpack("<I", d[:4])[0]
        return d[4:4 + n].rstrip(b"\0").decode(errors="replace")
    def title(self): return self._str(0x0B)
    def game_id(self): return self._str(0x0C)
    def status(self): return ["running", "paused", "shutdown"][struct.unpack("<I", self._call(b"\x0f"))[0]]

_conn = None
def Pine(timeout=30.0):
    """Shared PINE connection: PCSX2's PINE server serves one client at a time, so a second socket would block."""
    global _conn
    if _conn is None: _conn = _Pine(timeout)
    return _conn

def pine_reset():
    global _conn
    try: _conn and _conn.s.close()
    except OSError: pass
    _conn = None

# ---------------------------------------------------------------- virtual pad
# raw libpad bytes at controller+1398: [btn_hi, btn_lo] active-low, [rx, ry, lx, ly], 12 pressure bytes
HI = {"select": 0, "l3": 1, "r3": 2, "start": 3, "up": 4, "right": 5, "down": 6, "left": 7}
LO = {"l2": 0, "r2": 1, "l1": 2, "r1": 3, "triangle": 4, "circle": 5, "cross": 6, "square": 7}
PRESSURE = ["right", "left", "up", "down", "triangle", "circle", "cross", "square", "l1", "r1", "l2", "r2"]
STICK_ADDR = th.VPAD_RAW + 2

def pad_bytes(buttons, lx=0.0, ly=0.0, rx=0.0, ry=0.0):
    hi = lo = 0xFF
    for b in buttons:
        if b in HI: hi &= ~(1 << HI[b])
        elif b in LO: lo &= ~(1 << LO[b])
        else: raise SystemExit(f"unknown button {b}")
    stick = lambda v: max(0, min(255, int(round(128 + v * 127))))
    raw = bytes([hi & 0xFF, lo & 0xFF, stick(rx), stick(ry), stick(lx), stick(ly)])
    raw += bytes(255 if name in buttons else 0 for name in PRESSURE)
    return raw

def set_pad(p, buttons=(), lx=0.0, ly=0.0, rx=0.0, ry=0.0):
    raw = pad_bytes(buttons, lx, ly, rx, ry)
    for i in range(0, 18, 4):
        chunk = raw[i:i + 4].ljust(4, b"\0")
        p.w32(th.VPAD_RAW + i, struct.unpack("<I", chunk)[0])
    p.w32(th.VPAD_EN, 1)

# ---------------------------------------------------------------- screenshots (GDI, no extra packages)
user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
user32.SetProcessDPIAware()

def test_pid():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        f"(Get-Process pcsx2-qt -ErrorAction SilentlyContinue | Where-Object {{ $_.Path -eq '{EXE}' }}).Id"],
        capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None

def game_hwnd(pid):
    found = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        p = wintypes.DWORD(); user32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(h):
            n = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h, n, 256)
            r = wintypes.RECT(); user32.GetClientRect(h, ctypes.byref(r))
            if r.right * r.bottom > 0 and not n.value.startswith("PCSX2 v"): found.append((r.right * r.bottom, h, n.value))
        return True
    user32.EnumWindows(cb, 0)
    return max(found)[1] if found else None

def png(path, w, h, bgra):
    raw = bytearray()                                  # BGRA rows -> filtered RGB rows
    for y in range(h):
        line = bgra[y*w*4:(y+1)*w*4]
        rgb = bytearray(w * 3); rgb[0::3] = line[2::4]; rgb[1::3] = line[1::4]; rgb[2::3] = line[0::4]
        raw += b"\0" + rgb
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))

def load_png(path):
    d = open(path, "rb").read(); pos = 8; idat = b""; w = h = 0
    while pos < len(d):
        n = struct.unpack(">I", d[pos:pos+4])[0]; t = d[pos+4:pos+8]; body = d[pos+8:pos+8+n]; pos += 12 + n
        if t == b"IHDR": w, h = struct.unpack(">II", body[:8])
        if t == b"IDAT": idat += body
    raw = zlib.decompress(idat); bgra = bytearray(w * h * 4)
    for y in range(h):
        row = raw[y*(w*3+1)+1:(y+1)*(w*3+1)]          # rig PNGs use filter 0 only
        bgra[y*w*4+2:(y+1)*w*4:4] = row[0::3]; bgra[y*w*4+1:(y+1)*w*4:4] = row[1::3]; bgra[y*w*4:(y+1)*w*4:4] = row[2::3]
    return w, h, bytes(bgra)

def thumb(w, h, bgra, tw=40, th_=30):
    out = []
    for ty in range(th_):
        for tx in range(tw):
            x, y = tx * w // tw + w // (2 * tw), ty * h // th_ + h // (2 * th_)
            i = (y * w + x) * 4; out.append((bgra[i] + 2 * bgra[i+1] + bgra[i+2]) // 4)
    return out

def diff(a, b): return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

def screenshot(path):
    w, h, buf = grab()
    png(path, w, h, buf)
    print(f"saved {path} ({w}x{h})")

def grab():
    pid = test_pid(); hwnd = pid and game_hwnd(pid)
    if not hwnd: raise SystemExit("test game window not found")
    r = wintypes.RECT(); user32.GetClientRect(hwnd, ctypes.byref(r)); w, h = r.right, r.bottom
    hdc = user32.GetDC(hwnd); mdc = gdi32.CreateCompatibleDC(hdc); bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 3)            # PW_CLIENTONLY | PW_RENDERFULLCONTENT
    class BMI(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                    ("x", wintypes.LONG), ("y", wintypes.LONG), ("c1", wintypes.DWORD), ("c2", wintypes.DWORD)]
    bmi = BMI(ctypes.sizeof(BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = (ctypes.c_ubyte * (w * h * 4))()
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    if not ok: raise SystemExit("PrintWindow failed")
    return w, h, bytes(buf)

def until(ref, press=None, every=2.0, timeout=90.0, thr=12.0):
    """Press PRESS every EVERY seconds until the screen matches reference image REF (mean grey diff < THR)."""
    target = thumb(*load_png(ref)); t0 = time.time(); best = 999
    while time.time() - t0 < timeout:
        d = diff(thumb(*grab()), target); best = min(best, d)
        if d < thr: print(f"matched {os.path.basename(ref)} (diff {d:.1f}) after {time.time()-t0:.0f}s"); return True
        if press: run(["press", press, "--frames", "8"])
        time.sleep(every)
    raise SystemExit(f"timed out waiting for {os.path.basename(ref)} (best diff {best:.1f})")

# ---------------------------------------------------------------- instance setup / launch
FLOW_LEVEL_GUESS = 0x00B84DD0     # game-flow object's current-level string (flow+1296) on this build/boot path
PLAYER_CHAR = 0x003098FC          # global -> player character object; its position vector is at +0xD0
FLOW_PTR = 0x0030988C             # global -> game-flow object; state = (u32 at flow+12 >> 12) & 0x3F
LEVEL_START_STR = 0x0030BE90      # string object the end-of-credits code loads (Levels\Ice\Hub\LabExt)
STATE_PLAYING, STATE_CREDITS = 12, 19
MOVIE_DECODING = 0x0030A3C3       # movie player: non-zero while the loop is waiting on a decoded frame
# Credits handler (0x1751A0): "beq v0,zero,finished" after the per-frame credits update. Made unconditional
# during a warp so the game takes its own credits-finished path (level load, state 11 -> 12) immediately.
CREDITS_DONE_BRANCH, CREDITS_DONE_ORIG, CREDITS_DONE_ALWAYS = 0x001753A8, 0x10400036, 0x10000036
STATES_DIR = os.path.join(HERE, "states")

def fl(p, a): return struct.unpack("<f", struct.pack("<I", p.r32(a)))[0]
def pos(p):
    base = p.r32(PLAYER_CHAR) + 0xD0
    return fl(p, base), fl(p, base + 4), fl(p, base + 8)

def flow_state(p): return (p.r32(p.r32(FLOW_PTR) + 12) >> 12) & 0x3F

EE_RAM = 0x02000000               # PS2 main memory; a player pointer outside it means there is no player

def player_obj(p):
    """Crash's object, or None when there isn't one - between levels, on a menu, during a reload after a
    death. Reading through a stale pointer is how a sweep turns into an unpack error 400 instances in."""
    obj = p.r32(PLAYER_CHAR)
    return obj if 0x00100000 <= obj < EE_RAM - 0x200 else None

def teleport(x, y, z, tol=2e-3, mirrors=None):
    """Move Crash to (x, y, z), and return the addresses that were moved, to pass back as `mirrors`.

    His position is held in several structures (object, physics body, camera targets) whose layout varies by
    level, so every copy of his current x/z in RAM is shifted by the same offset (found with a RAM dump; each
    copy keeps its own height offset).

    That dump costs ~1.3s and is the entire cost of a sweep that teleports once per object instance - the
    PINE reads it replaces cost ~20us each. Pass `mirrors` from an earlier call on the same level and the
    copies that still track him are shifted directly, with no dump. The check is the same predicate the dump
    applies, just over known addresses instead of all 8M, so a copy that has drifted away (the camera target
    lagging behind a teleport) is skipped exactly as it would be; a fresh dump is only needed when almost
    nothing still tracks him, which means the structures themselves moved."""
    import array
    p = Pine(); f2u = lambda v: struct.unpack("<I", struct.pack("<f", v))[0]
    obj = player_obj(p)
    if obj is None:
        raise SystemExit(f"nothing to teleport: the player pointer reads 0x{p.r32(PLAYER_CHAR):08x}, which is "
                         f"not in EE RAM. The game is between levels, reloading after a death, or on a menu "
                         f"(flow state {flow_state(p)}); a teleport needs flow 12.")
    x0, y0, z0 = (fl(p, obj + 0xD0 + 4 * k) for k in range(3))
    tracks = lambda a, b, c: abs(a - x0) < tol and abs(c - z0) < tol and abs(b - y0) < 3.0

    if mirrors:
        here = [(a, fl(p, a), fl(p, a + 4), fl(p, a + 8)) for a in mirrors]
        keep = [m for m in here if tracks(*m[1:])]
        if len(keep) >= 2:                            # enough of the known copies are still his position
            for a, mx, my, mz in keep:
                for k, v in enumerate((mx + x - x0, my + y - y0, mz + z - z0)): p.w32(a + 4 * k, f2u(v))
            return mirrors                            # hand back the full candidate set, not just today's hits

    dump = os.path.join(TEST, "tp_ram.bin"); run(["ram", dump])
    f = array.array("f"); f.frombytes(open(dump, "rb").read())
    x0, y0, z0 = f[(obj + 0xD0) // 4:(obj + 0xD0) // 4 + 3]   # from the dump, so a moving Crash still matches
    hits = [i for i in range(len(f) - 2) if tracks(f[i], f[i + 1], f[i + 2])]
    for i in hits:
        for k, v in enumerate((f[i] + x - x0, f[i + 1] + y - y0, f[i + 2] + z - z0)): p.w32(i * 4 + 4 * k, f2u(v))
    return [i * 4 for i in hits]

def _band(w, h, b, y0, y1, x0=0, x1=None):
    tot = n = 0; x1 = w if x1 is None else x1
    for y in range(max(0, y0), min(h, y1), 2):
        row = b[(y * w + x0) * 4:(y * w + x1) * 4]; tot += sum(row[0::16]) + sum(row[1::16]) + sum(row[2::16]); n += 3 * len(row[0::16])
    return tot / max(n, 1)

def in_cutscene(img=None):
    """Cutscenes letterbox the picture: the top and bottom bands are pure black while the middle is lit.
    The middle of the bottom band is ignored - the skip prompt is drawn there."""
    w, h, b = img or grab()
    bottom = max(_band(w, h, b, h - 30, h, 0, w // 5), _band(w, h, b, h - 30, h, 4 * w // 5, w))
    return _band(w, h, b, 0, 60) < 2 and bottom < 2 and _band(w, h, b, h // 2 - 40, h // 2 + 40) > 8

def movie_playing(p):
    """Is a pre-rendered movie on screen, rather than an in-engine scene?

    `in_cutscene` reads the letterbox, and both kinds letterbox, so it cannot tell them apart - which lets a
    list entry whose coordinates sit on an FMV trigger report a passing skip for a level recipe that does
    nothing at all (the Iceberg Lab interior did exactly that: 55.7s -> 4.0s with the recipe, and 55.7s ->
    4.0s without it, because what was being skipped was the movie). The movie player's decoding flag is 1
    throughout a movie and 0 otherwise; measured 1 across the Iceberg Lab FMV and 0 across Classroom Chaos."""
    return p.r8(MOVIE_DECODING) != 0

def slot_file(slot):
    import glob
    hits = glob.glob(os.path.join(TEST, "sstates", f"*.{slot:02d}.p2s"))
    return max(hits, key=os.path.getmtime) if hits else None

def level(name, path=None, fresh=False, timeout=300):
    """Get the test instance into level NAME. Uses states/NAME.p2s when present; otherwise warps to PATH
    through the game's end-of-credits level load (flow state 19 loads LEVEL_START_STR; the credits are
    cut to one frame), waits for gameplay and stores the result as states/NAME.p2s.

    A warp that times out leaves the game *in* state 19 - the real credits - so every later warp starts from
    there and fails too. Building three level states in one command therefore costs three full timeouts and
    ends with nothing, which is how this was found. The wedge is checked for before warping and named in the
    timeout message, because the symptom on its own (PINE healthy, warp never arrives) looks like anything."""
    os.makedirs(STATES_DIR, exist_ok=True); lib = os.path.join(STATES_DIR, name + ".p2s"); p = Pine()
    if os.path.exists(lib) and not fresh:
        p.save(8); time.sleep(1.5)                       # make sure slot 8's file exists with the right name
        target = slot_file(8); shutil.copyfile(lib, target); p.load(8)
        for _ in range(60):                               # PINE is busy while a large state loads
            try: Pine().r32(PLAYER_CHAR); break
            except (OSError, RuntimeError): pine_reset(); time.sleep(0.5)
        time.sleep(1); print(f"loaded {name} from the state library"); return
    if not path: raise SystemExit(f"no saved state for {name}; give the level path to warp there")
    raw = path.replace("/", "\\").encode("ascii"); buf = raw + b"\0"; buf += b"\0" * (-len(buf) % 4)
    for i in range(0, len(buf), 4): p.w32(th.WARP_STR + i, struct.unpack("<I", buf[i:i + 4])[0])
    p.w32(LEVEL_START_STR, th.WARP_STR); p.w32(LEVEL_START_STR + 4, len(raw)); p.w32(LEVEL_START_STR + 8, 0x100)
    # Straight after rig.py start the executable is not in RAM yet, so the credits branch reads as something
    # else and the warp used to fail with "wrong build?" - which sends you looking at the ISO. Wait for it.
    t_boot = time.time()
    while p.r32(CREDITS_DONE_BRANCH) != CREDITS_DONE_ORIG:
        if time.time() - t_boot > 120:
            raise SystemExit("unexpected code at the credits branch after 120s - wrong build?")
        if time.time() - t_boot < 1: print("waiting for the game to boot...", flush=True)
        time.sleep(1)
    while flow_state(p) < 6:                             # still settling: warping here times out
        if time.time() - t_boot > 180: break
        time.sleep(1)
    # A warp only works from a settled game: the menu, the attract demo, or ordinary play. Excluding only
    # flow 19 was not enough. Warping into the same level twice in a row leaves the game at flow **14**, and
    # a warp from there times out and *then* leaves it at 19 - so the first failure manufactures the wedge
    # the old check was looking for, and every later warp in the run dies too. That is what kept killing the
    # Iceberg Lab arrival sweep: its throwaway warp succeeded, the first sampled one wedged, and the run
    # ended with a single useless sample. A whitelist fails fast instead, before anything is burned.
    before = flow_state(p)
    if before not in (6, 7, STATE_PLAYING):
        hint = (" - the game is wedged in the credits; only a restart clears it" if before == STATE_CREDITS
                else " - it is mid-transition or mid-scene; let it settle, or restart")
        raise SystemExit(f"refusing to warp from flow state {before}{hint}. A warp needs flow 6 (title), "
                         "7 (attract demo) or 12 (playing).")
    p.w32(CREDITS_DONE_BRANCH, CREDITS_DONE_ALWAYS)      # credits end on their first frame -> normal level-load path
    try:
        flow = p.r32(FLOW_PTR); hi = p.r32(flow + 12)
        p.w32(flow + 12, (hi & ~(0x3F << 12)) | (STATE_CREDITS << 12))
        print(f"warping to {path}...", flush=True); t0 = time.time()
        while flow_state(p) != STATE_PLAYING:
            if time.time() - t0 > timeout:
                raise SystemExit(f"warp to {path} timed out after {timeout:.0f}s at flow {flow_state(p)}. "
                                 "The game is now left in the credits, so every later warp in this run will "
                                 "time out the same way: restart the emulator before trying another.")
            time.sleep(0.5)
    finally:
        p.w32(CREDITS_DONE_BRANCH, CREDITS_DONE_ORIG)
    loaded = time.time() - t0
    import math                                          # level intros hold the camera: wait for real control
    t1 = time.time(); controllable = False
    while time.time() - t1 < 60:
        a = pos(p); set_pad(p, (), 0, -1); time.sleep(0.25); set_pad(p); b = pos(p)
        if math.dist(a, b) > 0.05: controllable = True; break
        time.sleep(0.5)
    time.sleep(1.5)
    # A state is only worth saving if the warp actually arrived. Both failures below have happened here and
    # both were saved into the library and used, because this only printed a warning and carried on: a state
    # that is wrong is worse than no state, since every test run off it looks like it ran.
    here = pos(p)
    if not controllable:
        raise SystemExit(f"warp to {path} left Crash uncontrollable at {tuple(round(v, 2) for v in here)} - "
                         "not saving. The usual cause is the first warp after a cold boot, which lands at a "
                         "default spawn (often the origin): warp once more and it will land properly.")
    if loaded < 2.0:
        raise SystemExit(f"warp to {path} reported loading in {loaded:.1f}s, which is too fast to be a real "
                         f"level load (6-9s here), and left Crash at {tuple(round(v, 2) for v in here)} - not "
                         "saving. Warping while the game is respawning (flow 18/21) does this; let him respawn "
                         "first. Note that two levels sharing a spawn is normal and is not this failure: "
                         "Cavern files with no start marker all land on the same default.")
    # Let the game reach ordinary play before the state is taken. Returning at flow 14 - which a repeat warp
    # into the same level does - hands the caller a game the *next* warp cannot start from, and a state
    # captured mid-transition besides.
    t2 = time.time()
    while flow_state(p) != STATE_PLAYING and time.time() - t2 < 20:
        time.sleep(0.5)
    settled = flow_state(p)
    p.save(8); time.sleep(2); shutil.copyfile(slot_file(8), lib)
    note = "" if settled == STATE_PLAYING else f", WARNING: still at flow {settled} rather than 12"
    print(f"arrived after {time.time() - t0:.0f}s (level loaded in {loaded:.1f}s), saved states/{name}.p2s{note}")

def goto(tx, tz, radius=1.5, timeout=60.0, burst=0.25):
    """Walk Crash to world (tx, tz) with closed-loop steering; the stick is camera-relative, so the
    world direction of 'stick up' and 'stick right' is re-measured every few steps.

    Prefer this to `teleport` wherever the test is about *being somewhere*. A teleport drops the player
    through whatever is not loaded, does not run a trigger's approach, and reads back correct while leaving
    him in a void - which is how the Evil Crash repro spent weeks measuring a place nobody can stand in.
    Walking also proves the route exists: in the Cavern it took Crash from the warp spawn to the throw-me
    trigger with his height unchanged the whole way, which is a floor check no teleport can give you."""
    import math
    p = Pine(); t0 = time.time()
    def step(lx, ly, dur):
        a = pos(p); set_pad(p, (), lx, ly); time.sleep(dur); set_pad(p); time.sleep(0.1); b = pos(p)
        return (b[0] - a[0], b[2] - a[2])
    calib = None; n = 0; still = 0
    while time.time() - t0 < timeout:
        x, _, z = pos(p); dx, dz = tx - x, tz - z; dist = math.hypot(dx, dz)
        if dist < radius: set_pad(p); print(f"arrived ({x:.1f}, {z:.1f})"); return True
        if calib is None or n % 6 == 0:
            up = step(0, -1, 0.2); right = step(1, 0, 0.2); calib = (up, right)
            if math.hypot(*up) < 0.05 and math.hypot(*right) < 0.05:
                still += 1
                if still >= 2:                        # stick does nothing: cutscene / dialog / pause
                    set_pad(p); print(f"blocked at ({x:.1f}, {z:.1f}) - Crash is not responding (cutscene?)"); return False
                calib = None; time.sleep(0.3); continue
            still = 0
        (ux, uz), (rx, rz) = calib
        det = ux * rz - uz * rx
        if abs(det) < 1e-4: calib = None; continue
        sy = (dx * rz - dz * rx) / det            # amount of 'up'
        sx = (ux * dz - uz * dx) / det            # amount of 'right'
        m = max(abs(sx), abs(sy), 1e-6)
        moved = step(sx / m, -sy / m, burst if dist > 4 else burst / 2); n += 1
        if math.hypot(*moved) < 0.02: calib = None      # re-measure; next pass decides if we're blocked
    set_pad(p); x, _, z = pos(p)
    raise SystemExit(f"goto timed out at ({x:.1f}, {z:.1f}), target ({tx}, {tz})")

def warp(p, level):
    """Point New Game at LEVEL (e.g. Levels\\Earth\\DocAmok\\DocAmok1). Takes effect on the next New Game.
    The start-level global and the game-flow object's level string share one heap buffer; both are repointed at
    WARP_STR with a 256-byte capacity so the game's string assign copies in place and never frees our buffer."""
    raw = level.replace("/", "\\").encode("ascii")
    path = raw + b"\0"; path += b"\0" * (-len(path) % 4)
    for i in range(0, len(path), 4): p.w32(th.WARP_STR + i, struct.unpack("<I", path[i:i+4])[0])
    shared = p.r32(th.START_LEVEL)
    objs = [th.START_LEVEL]
    if shared != th.WARP_STR:
        if p.r32(FLOW_LEVEL_GUESS) == shared: objs.append(FLOW_LEVEL_GUESS)
        else:
            dump = os.path.join(TEST, "warp_ram.bin"); run(["ram", dump]); import array
            words = array.array("I"); words.frombytes(open(dump, "rb").read())
            objs += [i * 4 for i, v in enumerate(words) if v == shared and i * 4 != th.START_LEVEL]
    elif p.r32(FLOW_LEVEL_GUESS) == th.WARP_STR: objs.append(FLOW_LEVEL_GUESS)
    for o in objs:
        p.w32(o, th.WARP_STR); p.w32(o + 4, len(raw)); p.w32(o + 8, 0x100)
    print("repointed level strings at", ", ".join(hex(o) for o in objs))

def write_test_config(level, iso):
    crc = isotools.iso_crc(ISOS[iso])
    src = os.path.join(MOD, "PCSX2 patches", f"SLES-52568_{crc}.pnach")
    if not os.path.exists(src):                        # test builds: same patch set as the current [Modded] build
        src = os.path.join(MOD, "mod", "pcsx2", "modded.pnach")
    base = open(src, encoding="utf-8").read().replace("{CRC}", crc).rstrip()
    rig = th.pnach_section()
    for item in filter(None, os.environ.get("RIG_PATCH", "").split(",")):   # experiments: RIG_PATCH=ADDR=WORD,ADDR=WORD (hex)
        a, v = item.split("="); rig += f"\npatch=1,EE,2{int(a, 16):07X},word,{int(v, 16):08X}"
    open(os.path.join(TEST, "patches", f"SLES-52568_{crc}.pnach"), "w", encoding="utf-8").write(base + "\n\n" + rig + "\n")
    renderer = os.environ.get("RIG_RENDERER")          # e.g. 13 = software, 12 = OpenGL, 14 = Vulkan (default: auto)
    open(os.path.join(TEST, "gamesettings", f"SLES-52568_{crc}.ini"), "w", encoding="utf-8").write(
        "[Patches]\nEnable = Cutscene Skip (Triangle)\nEnable = Test Rig\n\n[EmuCore/GS]\n"
        + f"upscale_multiplier = {os.environ.get('RIG_UPSCALE', '1')}\n"                                   # e.g. 6, the mod's preset
        + (f"Renderer = {renderer}\n" if renderer else "")
        + "".join(kv.strip() + "\n" for kv in filter(None, os.environ.get("RIG_GS", "").split(",")))   # RIG_GS="hw_mipmap = true,TriFilter = 2"
        + ("\n[EmuCore/Speedhacks]\n" if os.environ.get("RIG_EE_RATE") or os.environ.get("RIG_FASTCDVD") else "")
        + (f"EECycleRate = {os.environ['RIG_EE_RATE']}\n" if os.environ.get("RIG_EE_RATE") else "")      # -3..3 (3 = 300%)
        + (f"fastCDVD = {os.environ['RIG_FASTCDVD']}\n" if os.environ.get("RIG_FASTCDVD") else ""))    # true / false

def start(level, iso, speed):
    if test_pid(): raise SystemExit("test PCSX2 already running (rig.py stop)")
    write_test_config(level, iso)
    ini = os.path.join(TEST, "inis", "PCSX2.ini")
    txt = open(ini, encoding="utf-8").read()
    import re
    txt = re.sub(r"(?m)^NominalScalar = .*$", f"NominalScalar = {speed}", txt)
    open(ini, "w", encoding="utf-8").write(txt)
    subprocess.Popen([EXE, "-nofullscreen", "-fastboot", "--", ISOS[iso]], cwd=TEST,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(120):
        try:
            pine_reset(); p = Pine(timeout=1); st = p.status(); gid = p.game_id()
            if st == "running" and gid:
                warp(p, level); print(f"running {gid} ({p.title()}), New Game -> {level}"); return
        except (OSError, RuntimeError): pine_reset()    # socket not up yet / no game loaded yet
        time.sleep(0.5)
    raise SystemExit("PINE did not come up")

def stop():
    pid = test_pid()
    if pid: subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True); print("stopped")
    else: print("not running")

# ---------------------------------------------------------------- CLI
STATE = {"lx": 0.0, "ly": 0.0}

def run(argv):
    a = argv[0]; rest = argv[1:]
    if a == "start":
        ap = argparse.ArgumentParser(); ap.add_argument("--level", default="Levels\\Earth\\Hub\\Beach")
        ap.add_argument("--iso", default="modded", choices=ISOS); ap.add_argument("--speed", default="1")
        o = ap.parse_args(rest); start(o.level, o.iso, o.speed)
    elif a == "stop": stop()
    elif a == "warp": warp(Pine(), rest[0]); print("New Game ->", rest[0])
    elif a == "pos": x, y, z = pos(Pine()); print(f"crash at ({x:.2f}, {y:.2f}, {z:.2f})")
    elif a == "level": level(rest[0], rest[1] if len(rest) > 1 and not rest[1].startswith("--") else None, "--fresh" in rest)
    elif a == "state": print("flow state", flow_state(Pine()), "| cutscene" if in_cutscene() else "| gameplay")
    elif a == "tp": teleport(float(rest[0]), float(rest[1]), float(rest[2])); time.sleep(0.5); print("crash at", tuple(round(c, 2) for c in pos(Pine())))
    elif a == "goto": goto(float(rest[0]), float(rest[1]), float(rest[2]) if len(rest) > 2 else 1.5)
    elif a == "status":
        p = Pine(); print(p.status(), p.game_id(), p.title())
    elif a in ("press", "hold"):
        frames = int(rest[rest.index("--frames") + 1]) if "--frames" in rest else 6
        btns = rest[0].lower().split("+"); p = Pine(); set_pad(p, btns, STATE["lx"], STATE["ly"])
        if a == "press": time.sleep(frames / 60); set_pad(p, (), STATE["lx"], STATE["ly"])
    elif a == "release":
        STATE.update(lx=0.0, ly=0.0); p = Pine(); set_pad(p); p.w32(th.VPAD_EN, 0)
    elif a == "stick":
        STATE.update(lx=float(rest[0]), ly=float(rest[1])); set_pad(Pine(), (), STATE["lx"], STATE["ly"])
    elif a == "shot": screenshot(rest[0])
    elif a == "until":
        ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("--press"); ap.add_argument("--every", type=float, default=2.0)
        ap.add_argument("--timeout", type=float, default=90.0); ap.add_argument("--thr", type=float, default=12.0)
        o = ap.parse_args(rest); ref = o.ref if os.path.isabs(o.ref) else os.path.join(HERE, "ref", o.ref)
        until(ref, o.press, o.every, o.timeout, o.thr)
    elif a == "diff":
        print(f"{diff(thumb(*grab()), thumb(*load_png(os.path.join(HERE, 'ref', rest[0])))):.1f}")
    elif a == "read":
        p = Pine(); addr = int(rest[0], 16); n = int(rest[1]) if len(rest) > 1 else 1
        for i in range(n): print(f"{addr + 4*i:08X}: {p.r32(addr + 4*i):08X}")
    elif a == "write": Pine().w32(int(rest[0], 16), int(rest[1], 16))
    elif a == "ram":                                  # full 32MB EE RAM dump via a scratch save state (slot 9)
        import glob, zipfile
        pat = os.path.join(TEST, "sstates", "*.09.p2s"); old = {f: os.path.getmtime(f) for f in glob.glob(pat)}
        Pine().save(9)
        for _ in range(100):
            new = [f for f in glob.glob(pat) if os.path.getmtime(f) != old.get(f)]
            if new:
                time.sleep(0.5)
                try:
                    open(rest[0], "wb").write(zipfile.ZipFile(new[0]).read("eeMemory.bin"))
                    if not rest[0].endswith("tp_ram.bin"): print("RAM ->", rest[0])
                    break
                except (zipfile.BadZipFile, PermissionError): pass
            time.sleep(0.3)
        else: raise SystemExit("save state did not appear")
    elif a == "save": Pine().save(int(rest[0])); print("saved slot", rest[0])
    elif a == "load": Pine().load(int(rest[0])); print("loaded slot", rest[0])
    elif a == "wait": time.sleep(float(rest[0]))
    elif a == "seq":
        for line in open(rest[0], encoding="utf-8"):
            line = line.split("#", 1)[0].strip()
            if line: print(">", line); run(line.split())
    else: raise SystemExit(__doc__)

if __name__ == "__main__":
    run(sys.argv[1:] or ["help"])
