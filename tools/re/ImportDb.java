// Headless Ghidra script: applies tools/re/db/symbols.tsv and comments.tsv to the program.
// Args: DIR [dry]   -  "dry" reports what would change without writing anything.
//
// The other half of ExportDb.java: it puts the names back after the Ghidra project has been re-restored from
// twinsanity-reversed's .gar, so naming work survives an upstream update.  A name already in the program wins
// only when Ghidra did not invent it; otherwise the .tsv is the source of truth.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class ImportDb extends GhidraScript {

    static boolean isAuto(String n) {
        return n.matches("(FUN|DAT|LAB|SUB|EXT|UNK|SWITCH|OFF|PTR|ARRAY|s|u)_[0-9a-fA-F]{4,}.*")
            || n.startsWith("caseD_") || n.startsWith("switchD_");
    }

    /** Reverses ExportDb's escaping: a backslash escapes itself, and \n stands for a newline. */
    static String unescape(String s) {
        StringBuilder b = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c != '\\' || i + 1 == s.length()) { b.append(c); continue; }
            char next = s.charAt(++i);
            b.append(next == 'n' ? '\n' : next);
        }
        return b.toString();
    }

    static BufferedReader open(String path) throws IOException {
        return new BufferedReader(new InputStreamReader(new FileInputStream(path), StandardCharsets.UTF_8));
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        boolean dry = args.length > 1 && args[1].equals("dry");
        int named = 0, kept = 0, made = 0, missed = 0, commented = 0;

        // symbols.tsv is hand-curated and goes first, so a name worked out by hand beats a generated one.
        for (String which : new String[]{"/symbols.tsv", "/read.tsv", "/generated.tsv", "/shapes.tsv"}) {
            File sf = new File(args[0] + which);
            if (!sf.exists()) continue;
            try (BufferedReader r = open(sf.getPath())) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#") || line.isBlank()) continue;
                    String[] c = line.split("\t", -1);
                    Address a = toAddr(c[0]);
                    if (a == null) { missed++; continue; }
                    if (c[1].equals("F")) {
                        Function f = getFunctionAt(a);
                        if (f == null) {
                            if (dry) { made++; continue; }
                            f = createFunction(a, c[2]);
                            made++;
                            if (f == null) { missed++; continue; }
                        }
                        if (!isAuto(f.getName()) && !f.getName().equals(c[2])) { kept++; continue; }
                        if (!dry) f.setName(c[2], SourceType.USER_DEFINED);
                        named++;
                    } else {
                        boolean have = false;
                        for (Symbol s : currentProgram.getSymbolTable().getSymbols(a))
                            if (s.getName().equals(c[2])) have = true;
                        if (have) { kept++; continue; }
                        if (!dry) currentProgram.getSymbolTable().createLabel(a, c[2], SourceType.USER_DEFINED);
                        named++;
                    }
                }
            }
        }

        File cf = new File(args[0] + "/comments.tsv");
        if (cf.exists()) {
            Listing listing = currentProgram.getListing();
            try (BufferedReader r = open(cf.getPath())) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#") || line.isBlank()) continue;
                    String[] c = line.split("\t", 3);
                    Address a = c.length < 3 ? null : toAddr(c[0]);
                    if (a == null) { missed++; continue; }
                    if (!dry) listing.setComment(a, Integer.parseInt(c[1]), unescape(c[2]));
                    commented++;
                }
            }
        }
        println((dry ? "[dry run] " : "") + "named " + named + ", kept " + kept + " existing, "
                + made + " functions created, " + commented + " comments, " + missed + " unresolved");
    }
}
