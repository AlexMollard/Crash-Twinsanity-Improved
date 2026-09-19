// Headless Ghidra queries against the restored twinsanity-reversed project (see tools/re/ghidra.py).
// Args: OUTFILE then commands:  xref:ADDR  (references to ADDR, with the calling function)
//                               decomp:ADDR (decompiled C of the function containing ADDR)
//                               callers:ADDR (functions calling the function containing ADDR)
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.PrintWriter;

public class Query extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                String[] c = args[i].split(":", 2);
                Address a = toAddr(Long.parseLong(c[1].replace("0x", ""), 16));
                out.println("===== " + args[i]);
                if (c[0].equals("xref")) {
                    for (Reference r : getReferencesTo(a)) {
                        Function f = getFunctionContaining(r.getFromAddress());
                        out.println(r.getFromAddress() + " " + r.getReferenceType() + " in " + (f == null ? "?" : f.getName() + "@" + f.getEntryPoint()));
                    }
                } else if (c[0].equals("callers")) {
                    Function f = getFunctionContaining(a);
                    for (Reference r : getReferencesTo(f.getEntryPoint())) {
                        Function g = getFunctionContaining(r.getFromAddress());
                        out.println(r.getFromAddress() + " " + r.getReferenceType() + " in " + (g == null ? "?" : g.getName() + "@" + g.getEntryPoint()));
                    }
                } else if (c[0].equals("decomp")) {
                    Function f = getFunctionContaining(a);
                    if (f == null) { out.println("no function"); continue; }
                    DecompileResults res = dec.decompileFunction(f, 120, monitor);
                    out.println(res.decompileCompleted() ? res.getDecompiledFunction().getC() : "decompile failed: " + res.getErrorMessage());
                }
            }
        }
    }
}
