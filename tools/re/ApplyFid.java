// Headless Ghidra script: attaches the PS2 SDK Function ID databases and runs the Function ID analyzer,
// which names library functions (sceXxx, libc, libgraph ...) by matching their instruction hashes.
// Args: one or more .fidb paths.
//
// twinsanity-reversed ships the databases but the Ghidra project it distributes has only 148 sce* names,
// so most of the SDK was never matched.
import ghidra.app.script.GhidraScript;
import ghidra.app.services.Analyzer;
import ghidra.feature.fid.db.FidFileManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.classfinder.ClassSearcher;
import java.io.File;

public class ApplyFid extends GhidraScript {

    @Override
    public void run() throws Exception {
        FidFileManager fid = FidFileManager.getInstance();
        for (String path : getScriptArgs()) {
            File f = new File(path);
            if (!f.exists()) { println("missing: " + path); continue; }
            fid.addUserFidFile(f);
            println("attached " + f.getName());
        }
        fid.getFidFiles().forEach(ff -> { ff.setActive(true); println("  active: " + ff.getName()); });

        int before = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (f.getSymbol().getSource() != SourceType.DEFAULT) before++;

        Analyzer analyzer = null;
        for (Analyzer a : ClassSearcher.getInstances(Analyzer.class))
            if (a.getName().toLowerCase().contains("function id")) analyzer = a;
        if (analyzer == null) { println("no Function ID analyzer found"); return; }
        println("running " + analyzer.getName());
        analyzer.added(currentProgram, currentProgram.getMemory(), monitor, null);

        int after = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (f.getSymbol().getSource() != SourceType.DEFAULT) after++;
        println("named functions: " + before + " -> " + after);
    }
}
