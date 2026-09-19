// Headless Ghidra script: writes every function (address, name, signature) and every user-named label to the file in args[0].
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.PrintWriter;

public class DumpSymbols extends GhidraScript {
    @Override
    public void run() throws Exception {
        try (PrintWriter out = new PrintWriter(getScriptArgs()[0], "UTF-8")) {
            for (Function f : currentProgram.getFunctionManager().getFunctions(true))
                out.println("F " + f.getEntryPoint() + " " + f.getName(true) + " | " + f.getSignature().getPrototypeString());
            for (Symbol s : currentProgram.getSymbolTable().getAllSymbols(true)) {
                if (s.getSource() == SourceType.DEFAULT || s.getSymbolType() == SymbolType.FUNCTION) continue;
                out.println("L " + s.getAddress() + " " + s.getName(true) + " (" + s.getSymbolType() + ")");
            }
        }
    }
}
