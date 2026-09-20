"""A small MIPS assembler for the executable patches, over Keystone.

The PlayStation 2's CPU is an R5900 ("Emotion Engine"), a MIPS III core with Sony's own 128-bit extensions.
Keystone assembles the MIPS III part; the 128-bit multimedia instructions (lq, sq, pextlw, mflo1 ...) it does
not know, so those have to be written as raw `.word` lines.

Three things about the LLVM assembler underneath are worth knowing, because all three silently change code:

  * it fills branch delay slots with a nop of its own unless `.set noreorder` is in force,
  * it expands "macro" forms - `lw $v0, 0x9908($v0)` with an offset that does not fit in a signed 16 bits
    becomes three instructions using a scratch register - and `.set nomacro` does not stop all of them,
  * `la` refuses to load a 64-bit address at all in MIPS64 mode.

And one from Keystone itself: a branch target that arrives through the symbol resolver is measured from the
branch instruction rather than from the delay slot after it, so every PC-relative branch lands one instruction
too far. Absolute jumps (j, jal) are not affected. BRANCH_FUDGE below is that correction.

So this module assembles one source line at a time and checks the result is the size it measured on the first
pass. Anything that expands unexpectedly is an error naming the line, rather than a patch that quietly writes
over the instruction after it.
"""
import re

import keystone as K

PRELUDE = ".set noreorder\n.set nomacro\n.set noat\n"
DUMMY = 0x003DB200          # stand-in for an unresolved symbol while measuring, big enough to need lui+ori
BRANCH_FUDGE = 4            # see the note above: PC-relative branch targets come out one instruction too far

_LABEL = re.compile(r"^([A-Za-z_.$][\w.$]*):\s*(.*)$")
_WORD = re.compile(r"^\.word\s+(.+)$", re.I)

# Two ways to write code that assembles cleanly and means something else. Both are rejected rather than
# guessed at, because both produce a driver that runs and quietly does the wrong thing.
_BARE_NUMBER = re.compile(r"(?<![\w$.])(\d{2,})(?![\w])")   # see _check
_ALIASED_REG = re.compile(r"\$t[4-7]\b")


def _check(text, where):
    """Reject the two literals that silently change meaning.

    Keystone reads an unprefixed number as *hexadecimal*, so `lw $t1, 12($t0)` loads from offset 18 and
    `sw $a2, 16($sp)` stores at 22 - which is not even 4-byte aligned. Single digits are the same in both
    bases, so only two digits and up are worth refusing.

    And in the MIPS64 register naming Keystone uses here, $t4-$t7 are not separate registers: they are
    r12-r15, the same four as $t0-$t3. Keystone warns on stderr and assembles them anyway, so a driver that
    keeps a pointer in $t0 and a scratch in $t4 is using one register for both."""
    bad = _BARE_NUMBER.search(text)
    if bad:
        raise AsmError(f"{where}: `{bad.group(1)}` has no 0x and Keystone reads bare numbers as hex, so this "
                       f"would assemble as {int(bad.group(1), 16)}. Write it as "
                       f"0x{int(bad.group(1)):x} if you meant {int(bad.group(1))}.\n    {text}")
    bad = _ALIASED_REG.search(text)
    if bad:
        alias = "$t%d" % (int(bad.group(0)[2]) - 4)
        raise AsmError(f"{where}: {bad.group(0)} is the same register as {alias} here (MIPS64 names r12-r15 "
                       f"as $t0-$t3). Use {alias}, or $t8/$t9, or a number like $12.\n    {text}")


def _is_branch(text):
    """True for the PC-relative branches. Every MIPS mnemonic starting with 'b' is one except `break`."""
    m = re.match(r"([a-z0-9.]+)", text.lower())
    return bool(m) and m.group(1).startswith("b") and m.group(1) != "break"


class AsmError(Exception):
    pass


class Assembler:
    def __init__(self, symbols=None):
        self.symbols = dict(symbols or {})
        self._ks = K.Ks(K.KS_ARCH_MIPS, K.KS_MODE_MIPS64 | K.KS_MODE_LITTLE_ENDIAN)
        self._table = {}
        self._fudge = 0
        self._ks.sym_resolver = self._resolve

    def _resolve(self, symbol, value):
        name = symbol.decode() if isinstance(symbol, bytes) else symbol
        if name not in self._table: return False
        value[0] = self._table[name] - self._fudge
        return True

    def _one(self, text, addr, where):
        """Assemble a single instruction line at ADDR."""
        _check(text, where)
        m = _WORD.match(text)
        if m:
            try:
                return b"".join(int(v.strip(), 0).to_bytes(4, "little") for v in m.group(1).split(","))
            except ValueError as e:
                raise AsmError(f"{where}: bad .word ({e})")
        self._fudge = BRANCH_FUDGE if _is_branch(text) else 0
        try:
            enc, _ = self._ks.asm(PRELUDE + text, addr)
        except K.KsError as e:
            raise AsmError(f"{where}: {e}\n    {text}")
        if enc is None:
            raise AsmError(f"{where}: cannot assemble\n    {text}")
        return bytes(enc)

    def assemble(self, source, base, where="<asm>"):
        """Assemble SOURCE (a string) starting at address BASE.

        Returns (bytes, {label: address}). Labels may be used before they are defined, and any name not
        defined in the source is looked up in the symbol table this assembler was built with."""
        lines = []
        for n, raw in enumerate(source.splitlines(), 1):
            text = raw.split("#", 1)[0].strip()
            while text:
                m = _LABEL.match(text)
                if not m: break
                lines.append(("label", m.group(1), n))
                text = m.group(2).strip()
            if text: lines.append(("insn", text, n))

        # pass 1: measure every instruction, with names standing in at a representative value. A branch target
        # has to stand in as something nearby or the offset would not fit in the 16 bits a branch has.
        labels, addr, sizes = {}, base, []
        self._ks.sym_resolver = lambda s, v: (v.__setitem__(0, self._near if self._fudge else DUMMY), True)[1]
        for kind, text, n in lines:
            if kind == "label":
                labels[text] = addr
                continue
            self._near = addr + BRANCH_FUDGE
            size = len(self._one(text, addr, f"{where}:{n}"))
            sizes.append(size)
            addr += size

        # pass 2: assemble for real, now that every label has an address
        self._table = {**self.symbols, **labels}
        self._ks.sym_resolver = self._resolve
        out, addr, i = bytearray(), base, 0
        for kind, text, n in lines:
            if kind == "label": continue
            code = self._one(text, addr, f"{where}:{n}")
            if len(code) != sizes[i]:
                raise AsmError(f"{where}:{n}: assembles to {len(code)} bytes here but {sizes[i]} when measured - "
                               f"write it as explicit instructions\n    {text}")
            out += code; addr += len(code); i += 1
        return bytes(out), labels


def assemble(source, base, symbols=None, where="<asm>"):
    return Assembler(symbols).assemble(source, base, where)
