// Headless Ghidra script: decompiles every function into one C file (args[0]) for grepping.
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import java.io.PrintWriter;

public class DecompileAll extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);
        int n = 0;
        try (PrintWriter out = new PrintWriter(getScriptArgs()[0], "UTF-8")) {
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                DecompileResults r = dec.decompileFunction(f, 60, monitor);
                out.println("//// " + f.getEntryPoint() + " " + f.getName());
                out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// decompile failed: " + r.getErrorMessage());
                if (++n % 500 == 0) println("decompiled " + n);
            }
        }
    }
}
