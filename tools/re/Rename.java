// Renames symbols that already carry a user-defined name.
//
// ImportDb deliberately will not do this: it keeps any existing non-auto name, so that re-importing the
// database never undoes work done in the GUI. That is the right default, and it means a name that turns out
// to be *wrong* cannot be corrected through the normal path - which matters, because a wrong name is worse
// than no name. An address with no name invites a lookup; an address with a confident wrong name does not.
//
// Arguments are consecutive address/name pairs. They are not key=value, because analyzeHeadless
// splits an argument on '=' before the script ever sees it.
//
//   python tools/re/ghidra.py run tools/re/Rename.java 001976a8 InitInstanceContextBase
//
// @category Twinsanity
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;

public class Rename extends GhidraScript
{
    @Override
    public void run() throws Exception
    {
        int done = 0, missed = 0;
        String[] args = getScriptArgs();
        if (args.length % 2 != 0) { println("need address/name pairs"); return; }
        for (int i = 0; i < args.length; i += 2) {
            String where = args[i], want = args[i + 1];
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace()
                                      .getAddress(Long.parseLong(where, 16));
            Function f = getFunctionAt(a);
            if (f != null) {
                println(String.format("%s  %s -> %s", where, f.getName(), want));
                f.setName(want, SourceType.USER_DEFINED);
                done++;
                continue;
            }
            Symbol[] syms = currentProgram.getSymbolTable().getSymbols(a);
            if (syms.length == 0) { println("no symbol at " + where); missed++; continue; }
            println(String.format("%s  %s -> %s (label)", where, syms[0].getName(), want));
            syms[0].setName(want, SourceType.USER_DEFINED);
            done++;
        }
        println("renamed " + done + ", missed " + missed);
    }
}
