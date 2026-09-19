// twinsdump - command-line inspection of Crash Twinsanity PS2 level files (RM2) via the Twinsanity Editor library.
//   twinsdump <file.rm2> scripts <regex>        dump matching scripts (state machines, conditions, commands)
//   twinsdump <file.rm2> refs <id>[,<id>...]    find every reference to script IDs (objects, instances, triggers, scripts)
//   twinsdump <file.rm2> list                   list all script IDs and names
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Twinsanity;
using static Twinsanity.Script.MainScript;

static class Program
{
    static int Main(string[] args)
    {
        if (args.Length < 2) { Console.Error.WriteLine("usage: twinsdump <file.rm2> scripts <regex> | refs <ids> | list"); return 2; }
        Console.SetOut(new System.IO.StreamWriter(Console.OpenStandardOutput()) { AutoFlush = true });
        var file = new TwinsFile();
        var stdout = Console.Out; Console.SetOut(System.IO.TextWriter.Null);   // library prints load noise
        file.LoadFile(args[0], TwinsFile.FileType.RM2);
        Console.SetOut(stdout);

        var items = new List<(TwinsItem item, string path)>();
        Walk(file, "", items);
        var scripts = items.Where(i => i.item is Script).Select(i => (Script)i.item).ToList();

        switch (args[1])
        {
            case "list":
                foreach (var s in scripts) Console.WriteLine($"{s.ID,6}  {(s.Main != null ? "main  " + s.Main.name : "header " + HeaderText(s.Header))}");
                break;
            case "scripts":
                var re = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                foreach (var s in scripts.Where(s => re.IsMatch(ScriptName(s, scripts))))
                    DumpScript(s, scripts);
                break;
            case "refs":
                var ids = new HashSet<uint>(args[2].Split(',').Select(uint.Parse));
                FindRefs(items, scripts, ids);
                break;
            case "findid":                                 // twinsdump <rm2> findid <id> : every item with that record ID
                foreach (var (item, path) in items.Where(i => i.item.ID == uint.Parse(args[2])))
                    Console.WriteLine($"{path}  {item.GetType().Name}  size={item.Size}");
                break;
            case "objects":                                // twinsdump <rm2> objects <regex>  : game objects + script slots
            {
                var re4 = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                var scriptNames = scripts.ToDictionary(s => s.ID, s => ScriptName(s, scripts));
                foreach (var (item, path) in items.Where(i => i.item is GameObject))
                {
                    var o = (GameObject)item;
                    if (!re4.IsMatch(o.Name) && !re4.IsMatch(o.ID.ToString())) continue;
                    var slots = o.Scripts.Select((sid, k) => sid == 65535 ? null : $"{k}:{sid}({(scriptNames.TryGetValue(sid, out var n) ? n : ScriptEnum(sid) ?? "?")})").Where(x => x != null);
                    Console.WriteLine($"object {o.ID} {o.Name}\n   scripts: {string.Join("  ", slots)}\n   objects: {string.Join(",", o.Objects)}  anims: {string.Join(",", o.Anims)}  ogis: {string.Join(",", o.OGIs)}");
                }
                break;
            }
            case "instances":
            {
                var objNames = items.Where(i => i.item is GameObject).ToDictionary(i => i.item.ID, i => ((GameObject)i.item).Name);
                var re2 = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                foreach (var (item, path) in items.Where(i => i.item is Instance))
                {
                    var inst = (Instance)item;
                    objNames.TryGetValue(inst.ObjectID, out var on);
                    if (!re2.IsMatch(on ?? "")) continue;
                    Console.WriteLine($"inst {inst.ID,4} {path.Split('/')[1]}  pos=({inst.Pos.X:0.##}, {inst.Pos.Y:0.##}, {inst.Pos.Z:0.##})  obj {inst.ObjectID} {on}");
                }
                break;
            }
            case "triggers":
            {
                var objNames = items.Where(i => i.item is GameObject).ToDictionary(i => i.item.ID, i => ((GameObject)i.item).Name);
                var instObj = items.Where(i => i.item is Instance).GroupBy(i => (i.path.Split('/')[1], i.item.ID))
                                   .ToDictionary(g => g.Key, g => ((Instance)g.First().item).ObjectID);
                var re3 = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                foreach (var (item, path) in items.Where(i => i.item is Trigger))
                {
                    var t = (Trigger)item; var layer = path.Split('/')[1];
                    var targets = t.Instances.Select(id => instObj.TryGetValue((layer, id), out var oid) && objNames.TryGetValue(oid, out var n) ? $"{id}:{n}" : $"{id}:?").ToList();
                    if (!targets.Any(x => re3.IsMatch(x))) continue;
                    var c = t.Coords;
                    Console.WriteLine($"trig {t.ID,4} {layer} c0=({c[0].X:0.##},{c[0].Y:0.##},{c[0].Z:0.##},{c[0].W:0.##}) c1=({c[1].X:0.##},{c[1].Y:0.##},{c[1].Z:0.##},{c[1].W:0.##}) c2=({c[2].X:0.##},{c[2].Y:0.##},{c[2].Z:0.##},{c[2].W:0.##}) hdr=0x{t.Header:X} sh={t.SectionHead} en={t.Enabled} f={t.SomeFloat:0.##} args=({t.Arg1},{t.Arg2},{t.Arg3},{t.Arg4}) -> {string.Join(" ", targets)}");
                }
                break;
            }
            case "edit":                                   // twinsdump <rm2> edit <ops.txt> <outdir>
            {
                // ops (one per line): addbody, copybody, clearbodies, appendcmds, movebody, settarget, setarg (see each branch)
                // Writes <outdir>/<id>.bin (serialized script item) for every edited script.
                var outDir = args[3]; System.IO.Directory.CreateDirectory(outDir);
                var byId = scripts.ToDictionary(s => s.ID);
                var edited = new HashSet<uint>();
                foreach (var raw in System.IO.File.ReadAllLines(args[2]))
                {
                    var line = raw.Split('#')[0].Trim(); if (line == "") continue;
                    var t = line.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
                    var s = byId[uint.Parse(t[1])]; var st = StateAt(s.Main, int.Parse(t[2]));
                    if (t[0] == "addbody")
                    {
                        // addbody SCRIPT STATE COND PARAM TARGET [INTERVAL [THRESHOLD]]  (no commands; add them with appendcmds)
                        var inv = System.Globalization.CultureInfo.InvariantCulture;
                        float thr = t.Length > 7 ? float.Parse(t[7], inv) : 0.5f;
                        var body = new ScriptStateBody(s.Main.scriptGameVersion)
                        {
                            bitfield = 0x600, scriptStateListIndex = int.Parse(t[5]),
                            condition = new ScriptCondition { Interval = t.Length > 6 ? float.Parse(t[6], inv) : 0f, Threshold = thr, ThresholdInverse = 1f / thr }
                        };
                        body.condition.VTableIndex = ushort.Parse(t[3]); body.condition.Parameter = ushort.Parse(t[4]);
                        if (st.scriptStateBody == null) st.scriptStateBody = body;
                        else
                        {
                            var last = st.scriptStateBody; while (last.nextScriptStateBody != null) last = last.nextScriptStateBody;
                            last.nextScriptStateBody = body; last.bitfield |= 0x800;
                        }
                        int n = CountBodies(st); st.bitfield = (short)((st.bitfield & ~0x3FF) | (n << 5) | n | 0x800);   // 0x800: poll the conditions every frame, as the game's own skip-enabled states do
                    }
                    else if (t[0] == "copybody")
                    {
                        // copybody SCRIPT TOSTATE FROMSTATE BODYIDX TARGET COND PARAM INTERVAL
                        // appends a copy of body BODYIDX of FROMSTATE (its commands) to TOSTATE with a new condition/target
                        var src = StateAt(s.Main, int.Parse(t[3])).scriptStateBody; for (int k = 0; k < int.Parse(t[4]); k++) src = src.nextScriptStateBody;
                        var body = new ScriptStateBody(s.Main.scriptGameVersion)
                        {
                            bitfield = (src.bitfield & 0xFF) | 0x600, scriptStateListIndex = int.Parse(t[5]),
                            condition = new ScriptCondition { Interval = float.Parse(t[8], System.Globalization.CultureInfo.InvariantCulture),
                                                              Threshold = src.condition?.Threshold ?? 0.5f, ThresholdInverse = src.condition?.ThresholdInverse ?? 2.0f }
                        };
                        body.condition.VTableIndex = ushort.Parse(t[6]); body.condition.Parameter = ushort.Parse(t[7]);
                        if (src.command != null)
                            using (var ms = new System.IO.MemoryStream())
                            {
                                using (var w = new System.IO.BinaryWriter(ms, System.Text.Encoding.ASCII, true)) src.command.Write(w);
                                ms.Position = 0;
                                using (var r = new System.IO.BinaryReader(ms)) body.command = new ScriptCommand(r, s.Main.scriptGameVersion);
                            }
                        var last = st.scriptStateBody; while (last.nextScriptStateBody != null) last = last.nextScriptStateBody;
                        last.nextScriptStateBody = body; last.bitfield |= 0x800;
                        int n = CountBodies(st); st.bitfield = (short)((st.bitfield & ~0x3FF) | (n << 5) | n | 0x800);   // 0x800: poll the conditions every frame, as the game's own skip-enabled states do
                    }
                    else if (t[0] == "clearbodies")
                    {
                        st.scriptStateBody = null; st.bitfield = (short)(st.bitfield & ~0xFFF);
                    }
                    else if (t[0] == "appendcmds")
                    {
                        // appendcmds SCRIPT STATE BODYIDX FROMSCRIPT FROMSTATE FROMBODYIDX : append a copy of that body's commands
                        var body = BodyAt(st, int.Parse(t[3]));
                        var src = BodyAt(StateAt(byId[uint.Parse(t[4])].Main, int.Parse(t[5])), int.Parse(t[6]));
                        if (src.command == null) throw new Exception("source body has no commands: " + line);
                        ScriptCommand copy;
                        using (var ms = new System.IO.MemoryStream())
                        {
                            using (var w = new System.IO.BinaryWriter(ms, System.Text.Encoding.ASCII, true)) src.command.Write(w);
                            ms.Position = 0;
                            using (var r = new System.IO.BinaryReader(ms)) copy = new ScriptCommand(r, s.Main.scriptGameVersion);
                        }
                        if (body.command == null) body.command = copy;
                        else
                        {
                            var last = body.command; while (last.nextCommand != null) last = last.nextCommand;
                            last.nextCommand = copy; last.internalIndex |= 0x1000000;
                        }
                        int n = 0; for (var c = body.command; c != null; c = c.nextCommand) n++;
                        body.bitfield = (body.bitfield & ~0xFF) | n;
                    }
                    else if (t[0] == "movebody")
                    {
                        // movebody SCRIPT STATE FROMIDX TOIDX : reorder bodies (conditions are tried in order, so a new handler must precede an Else)
                        var list = new List<ScriptStateBody>(); for (var b = st.scriptStateBody; b != null; b = b.nextScriptStateBody) list.Add(b);
                        var moved = list[int.Parse(t[3])]; list.RemoveAt(int.Parse(t[3])); list.Insert(int.Parse(t[4]), moved);
                        for (int k = 0; k < list.Count; k++)
                        {
                            list[k].nextScriptStateBody = k + 1 < list.Count ? list[k + 1] : null;
                            list[k].bitfield = k + 1 < list.Count ? list[k].bitfield | 0x800 : list[k].bitfield & ~0x800;
                        }
                        st.scriptStateBody = list[0];
                    }
                    else if (t[0] == "settarget")
                    {
                        // settarget SCRIPT STATE BODYIDX TARGET
                        var b = BodyAt(st, int.Parse(t[3])); b.scriptStateListIndex = int.Parse(t[4]); b.bitfield |= 0x400;
                    }
                    else if (t[0] == "setarg")
                    {
                        // setarg SCRIPT STATE BODYIDX CMDIDX ARGIDX VALUE
                        var c = BodyAt(st, int.Parse(t[3])).command; for (int k = 0; k < int.Parse(t[4]); k++) c = c.nextCommand;
                        c.arguments[int.Parse(t[5])] = uint.Parse(t[6]);
                    }
                    else throw new Exception("unknown op " + t[0]);
                    edited.Add(s.ID);
                }
                foreach (var id in edited)
                {
                    using (var ms = new System.IO.MemoryStream())
                    using (var w = new System.IO.BinaryWriter(ms)) { byId[id].Save(w); System.IO.File.WriteAllBytes(System.IO.Path.Combine(outDir, $"{id}.bin"), ms.ToArray()); }
                    Console.WriteLine($"script {id} {byId[id].Main?.name}: {byId[id].Size} bytes");
                }
                break;
            }
            case "itembytes":                              // twinsdump <rm2> itembytes <scriptId> <out.bin>  (unmodified serialization)
            {
                var s = scripts.First(x => x.ID == uint.Parse(args[2]));
                using (var ms = new System.IO.MemoryStream())
                using (var w = new System.IO.BinaryWriter(ms)) { s.Save(w); System.IO.File.WriteAllBytes(args[3], ms.ToArray()); }
                break;
            }
            case "roundtrip":                              // load + save unchanged, report whether bytes are identical
            {
                var outPath = args[2];
                file.SaveFile(outPath);
                var a = System.IO.File.ReadAllBytes(args[0]); var b = System.IO.File.ReadAllBytes(outPath);
                int firstDiff = -1; for (int k = 0; k < Math.Min(a.Length, b.Length); k++) if (a[k] != b[k]) { firstDiff = k; break; }
                Console.WriteLine($"original {a.Length} bytes, saved {b.Length} bytes, identical={a.Length == b.Length && firstDiff < 0}, firstDiff={firstDiff}");
                break;
            }
            case "msg":                                    // twinsdump <rm2> msg <n> : every GotUserMessageEquals(n) handler, live or orphaned
            {
                var mid = ushort.Parse(args[2]);
                foreach (var s in scripts.Where(s => s.Main != null))
                {
                    var reach = Reachable(s.Main); int i = 0;
                    for (var st = s.Main.scriptState1; st != null; st = st.nextState, i++)
                        for (var body = st.scriptStateBody; body != null; body = body.nextScriptStateBody)
                            if (body.condition != null && body.condition.VTableIndex == 51 && body.condition.Parameter == mid)
                                Console.WriteLine($"{s.ID}\t{s.Main.name}\t{(reach.Contains(i) ? "LIVE" : "orphan")}\tstate {i} -> state {body.scriptStateListIndex}\tcmds={body.bitfield & 0xFF}");
                }
                break;
            }
            case "cond":
                var cid = ushort.Parse(args[2]);
                foreach (var s in scripts.Where(s => s.Main != null))
                {
                    int i = 0;
                    for (var st = s.Main.scriptState1; st != null; st = st.nextState, i++)
                        for (var body = st.scriptStateBody; body != null; body = body.nextScriptStateBody)
                            if (body.condition != null && body.condition.VTableIndex == cid)
                            {
                                string runs = st.scriptIndexOrSlot >= 0 && !st.IsSlot ? ScriptEnum((uint)st.scriptIndexOrSlot) ?? st.scriptIndexOrSlot.ToString() : "-";
                                string dest = (body.bitfield & 0x400) != 0 ? body.scriptStateListIndex.ToString() : "?";
                                var dst = s.Main.scriptState1; for (int k = 0; dst != null && k < body.scriptStateListIndex; k++) dst = dst.nextState;
                                string destRuns = dst != null && dst.scriptIndexOrSlot >= 0 && !dst.IsSlot ? ScriptEnum((uint)dst.scriptIndexOrSlot) ?? dst.scriptIndexOrSlot.ToString() : "-";
                                string live = Reachable(s.Main).Contains(i) ? "LIVE" : "orphan";
                                Console.WriteLine($"{s.ID}\t{s.Main.name}\t{live}\tstate {i} (runs {runs}) p={body.condition.Parameter} -> state {dest} (runs {destRuns})");
                            }
                }
                break;
        }
        return 0;
    }

    static void Walk(TwinsSection sec, string path, List<(TwinsItem, string)> acc)
    {
        foreach (var r in sec.Records)
        {
            var p = $"{path}/{(r is TwinsSection s ? s.Type.ToString() : r.GetType().Name)}[{r.ID}]";
            if (r is TwinsSection child) Walk(child, p, acc); else acc.Add((r, p));
        }
    }

    static string Cond(ushort id) => Enum.IsDefined(typeof(DefaultEnums.ConditionID), id) ? ((DefaultEnums.ConditionID)id).ToString() : $"Cond{id}";
    static string Cmd(ushort id) => Enum.IsDefined(typeof(DefaultEnums.CommandID), id) ? ((DefaultEnums.CommandID)id).ToString() : $"Cmd{id}";
    static string ScriptEnum(uint id) => Enum.IsDefined(typeof(DefaultEnums.ScriptID), (ushort)id) ? ((DefaultEnums.ScriptID)(ushort)id).ToString() : null;
    static string ObjName(uint id) => Enum.IsDefined(typeof(DefaultEnums.ObjectID), (ushort)id) ? ((DefaultEnums.ObjectID)(ushort)id).ToString() : $"Obj{id}";

    static string ScriptName(Script s, List<Script> all)
    {
        if (s.Main != null) return s.Main.name;
        return ScriptEnum(s.ID) ?? $"header#{s.ID}";
    }

    static string HeaderText(Script.HeaderScript h) =>
        h == null ? "" : string.Join("; ", h.pairs.Select(p => $"main={p.mainScriptIndex} obj={ObjName(p.ObjectID)} type={p.AssignType} loc={p.AssignLocality} status={p.AssignStatus} pref={p.AssignPreference}"));

    static string Arg(uint a)
    {
        float f = BitConverter.ToSingle(BitConverter.GetBytes(a), 0);
        bool plausibleFloat = a != 0 && Math.Abs(f) > 1e-4 && Math.Abs(f) < 1e6 && (a & 0x7F800000) != 0;
        var s = ScriptEnum(a);
        return plausibleFloat ? $"{f:0.###}f" : a < 0x10000 && s != null && a > 100 ? $"{a}({s})" : $"{a}";
    }

    static void DumpScript(Script s, List<Script> all)
    {
        Console.WriteLine($"\n=== script {s.ID} {ScriptName(s, all)}");
        if (s.Header != null) { Console.WriteLine($"  header: {HeaderText(s.Header)}"); return; }
        var m = s.Main;
        int i = 0;
        for (var st = m.scriptState1; st != null; st = st.nextState, i++)
        {
            string target = st.scriptIndexOrSlot == -1 ? "" : st.IsSlot ? $" slot={st.scriptIndexOrSlot}" : $" script={st.scriptIndexOrSlot}({ScriptEnum((uint)st.scriptIndexOrSlot) ?? "?"})";
            Console.WriteLine($"  state {i}{(i == m.StartUnit ? " [start]" : "")} bits=0x{(ushort)st.bitfield:X4}{target}{(st.type1 != null ? " +control" : "")}");
            int b = 0;
            for (var body = st.scriptStateBody; body != null; body = body.nextScriptStateBody, b++)
            {
                string cond = body.condition == null ? "always" :
                    $"{(body.condition.NotGate ? "NOT " : "")}{Cond(body.condition.VTableIndex)}(p={body.condition.Parameter}) int={body.condition.Interval:0.###} thr={body.condition.Threshold:0.###}";
                string go = (body.bitfield & 0x400) != 0 ? $" -> state {body.scriptStateListIndex}" : "";
                Console.WriteLine($"    [{b}] if {cond}{go}  (bits=0x{body.bitfield:X})");
                for (var c = body.command; c != null; c = c.nextCommand)
                    Console.WriteLine($"          {Cmd(c.VTableIndex)}({string.Join(", ", c.arguments.Select(Arg))})");
            }
        }
    }

    static ScriptState StateAt(Script.MainScript m, int index)
    {
        var st = m.scriptState1; for (int k = 0; k < index; k++) st = st.nextState;
        return st ?? throw new Exception($"state {index} not found in {m.name}");
    }
    static int CountBodies(ScriptState st) { int n = 0; for (var b = st.scriptStateBody; b != null; b = b.nextScriptStateBody) n++; return n; }
    static ScriptStateBody BodyAt(ScriptState st, int index)
    {
        var b = st.scriptStateBody; for (int k = 0; k < index && b != null; k++) b = b.nextScriptStateBody;
        return b ?? throw new Exception($"body {index} not found");
    }

    // States reachable from the start state by following body transitions.
    static HashSet<int> Reachable(Script.MainScript m)
    {
        var states = new List<ScriptState>();
        for (var st = m.scriptState1; st != null; st = st.nextState) states.Add(st);
        var seen = new HashSet<int>(); var todo = new Stack<int>(); todo.Push(m.StartUnit);
        while (todo.Count > 0)
        {
            int i = todo.Pop();
            if (i < 0 || i >= states.Count || !seen.Add(i)) continue;
            for (var body = states[i].scriptStateBody; body != null; body = body.nextScriptStateBody)
                if ((body.bitfield & 0x400) != 0) todo.Push(body.scriptStateListIndex);
        }
        return seen;
    }

    static void FindRefs(List<(TwinsItem item, string path)> items, List<Script> scripts, HashSet<uint> ids)
    {
        foreach (var (item, path) in items)
        {
            switch (item)
            {
                case GameObject o:
                    for (int k = 0; k < o.Scripts.Count; k++)
                        if (ids.Contains(o.Scripts[k])) Console.WriteLine($"object {o.ID} {o.Name}: script slot {k} = {o.Scripts[k]}  ({path})");
                    foreach (var c in o.scriptCommands)
                        if (c.arguments.Any(a => ids.Contains(a))) Console.WriteLine($"object {o.ID} {o.Name}: instance-script command {Cmd(c.VTableIndex)}({string.Join(", ", c.arguments)})");
                    break;
                case Instance inst:
                    if (inst.ScriptID >= 0 && ids.Contains((uint)inst.ScriptID)) Console.WriteLine($"instance {inst.ID} obj={ObjName(inst.ObjectID)} ScriptID={inst.ScriptID}  ({path})");
                    if (inst.UnkI323.Any(a => ids.Contains(a))) Console.WriteLine($"instance {inst.ID} obj={ObjName(inst.ObjectID)} integer params contain id: {string.Join(",", inst.UnkI323)}  ({path})");
                    break;
                case Trigger t:
                    foreach (var a in new uint[] { t.Arg1, t.Arg2, t.Arg3, t.Arg4 })
                        if (ids.Contains(a)) Console.WriteLine($"trigger {t.ID} args=({t.Arg1},{t.Arg2},{t.Arg3},{t.Arg4}) instances=[{string.Join(",", t.Instances)}]  ({path})");
                    break;
            }
        }
        foreach (var s in scripts)
        {
            if (s.Header != null)
            {
                if (s.Header.pairs.Any(p => ids.Contains((uint)p.mainScriptIndex)) || ids.Contains(s.ID))
                    Console.WriteLine($"header {s.ID} {ScriptName(s, scripts)}: {HeaderText(s.Header)}");
                continue;
            }
            int i = 0;
            for (var st = s.Main.scriptState1; st != null; st = st.nextState, i++)
            {
                if (!st.IsSlot && st.scriptIndexOrSlot >= 0 && ids.Contains((uint)st.scriptIndexOrSlot))
                    Console.WriteLine($"script {s.ID} {s.Main.name}: state {i} runs script {st.scriptIndexOrSlot}");
                for (var body = st.scriptStateBody; body != null; body = body.nextScriptStateBody)
                    for (var c = body.command; c != null; c = c.nextCommand)
                        if (c.arguments.Any(a => ids.Contains(a)))
                            Console.WriteLine($"script {s.ID} {s.Main.name}: state {i} command {Cmd(c.VTableIndex)}({string.Join(", ", c.arguments.Select(Arg))})");
            }
        }
    }
}
