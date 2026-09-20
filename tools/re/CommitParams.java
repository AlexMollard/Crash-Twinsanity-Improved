// Headless Ghidra script: gives a real signature to functions that have none.
// Args: [dry]
//
// Importing names creates functions at addresses Ghidra had never treated as functions, and a freshly created
// function has no parameters at all - it shows up as `undefined name(void)` however many arguments it really
// takes, which is worse than useless when you are reading a call site. The decompiler already works the
// arguments out every time it runs; this just commits what it found back to the database.
//
// Only functions whose signature Ghidra has never established are touched, so anything analysed earlier or
// set by hand is left exactly as it is.
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.pcode.HighFunction;
import ghidra.program.model.pcode.HighFunctionDBUtil;
import ghidra.program.model.symbol.SourceType;
import java.util.*;

public class CommitParams extends GhidraScript {

    @Override
    public void run() throws Exception {
        boolean dry = getScriptArgs().length > 0 && getScriptArgs()[0].equals("dry");

        List<Function> todo = new ArrayList<>();
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (f.getSignatureSource() == SourceType.DEFAULT && !f.isThunk()) todo.add(f);
        println("functions with no established signature: " + todo.size());
        if (dry) return;

        DecompInterface dec = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        dec.setOptions(options);
        dec.openProgram(currentProgram);

        int done = 0, failed = 0, params = 0;
        for (Function f : todo) {
            if (monitor.isCancelled()) break;
            DecompileResults res = dec.decompileFunction(f, 60, monitor);
            HighFunction high = res.getHighFunction();
            if (high == null) { failed++; continue; }
            try {
                HighFunctionDBUtil.commitParamsToDatabase(
                        high, true, HighFunctionDBUtil.ReturnCommitOption.COMMIT, SourceType.ANALYSIS);
                params += f.getParameterCount();
                done++;
            } catch (Exception e) {
                failed++;
            }
            if ((done + failed) % 250 == 0) println("  " + (done + failed) + " / " + todo.size());
        }
        dec.dispose();
        println("committed " + done + " signatures (" + params + " parameters), " + failed + " failed");
    }
}
