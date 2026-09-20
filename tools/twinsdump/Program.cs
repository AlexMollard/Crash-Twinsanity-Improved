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
        file.LoadFile(args[0], args[0].EndsWith(".sm2", StringComparison.OrdinalIgnoreCase)
                                   ? TwinsFile.FileType.SM2 : TwinsFile.FileType.RM2);   // .sm2 holds the scenery, lights included
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
            case "materials":                              // twinsdump <rm2> materials [regex] : material id, draw layer (DMA chain slot), name
            {
                var rem = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                foreach (var (item, path) in items.Where(i => i.item is Material))
                {
                    var m = (Material)item;
                    if (!rem.IsMatch(m.Name)) continue;
                    Console.WriteLine($"{m.ID,10}  layer {m.Unknown,3}  header 0x{m.Header:X}  {m.Name.TrimEnd('\0')}");
                    if (args.Length > 3 && args[3] == "shaders")          // materials REGEX shaders : every shader field
                        foreach (var shd in m.Shaders)
                            Console.WriteLine("      " + string.Join(" ", typeof(TwinsShader).GetFields().Where(fi => fi.FieldType.IsEnum || fi.FieldType == typeof(bool) || fi.FieldType == typeof(byte))
                                .Select(fi => $"{fi.Name}={fi.GetValue(shd)}")) + $" ShaderType={shd.ShaderType}");
                }
                break;
            }
            case "types":                                  // twinsdump <rm2> types : how many of each item type the file holds
            {
                foreach (var g in items.GroupBy(i => i.item.GetType().Name).OrderByDescending(g => g.Count()))
                    Console.WriteLine($"{g.Count(),6}  {g.Key}   e.g. {g.First().path}");
                break;
            }
            case "lights":                                 // twinsdump <rm2> lights [-v] : the scenery's runtime lights, per chunk
            {
                bool verbose = args.Contains("-v");
                int ta = 0, td = 0, tp = 0, tn = 0;
                foreach (var (item, path) in items.Where(i => i.item is SceneryData))
                {
                    var s = (SceneryData)item;
                    ta += s.LightsAmbient.Count; td += s.LightsDirectional.Count;
                    tp += s.LightsPoint.Count; tn += s.LightsNegative.Count;
                    Console.WriteLine($"scenery {s.ID,6} {s.ChunkName?.TrimEnd('\0')}: ambient {s.LightsAmbient.Count}, directional {s.LightsDirectional.Count}, point {s.LightsPoint.Count}, negative {s.LightsNegative.Count}");
                    if (!verbose) continue;
                    void Show(string kind, IEnumerable<SceneryData.LightBase> ls)
                    {
                        foreach (var l in ls)
                            Console.WriteLine($"    {kind,-11} rgb ({l.Color_R:0.##}, {l.Color_G:0.##}, {l.Color_B:0.##}) a {l.Color_Unk:0.##}  radius {l.Radius:0.##}  at ({l.Position.X:0.#}, {l.Position.Y:0.#}, {l.Position.Z:0.#})");
                    }
                    Show("ambient", s.LightsAmbient); Show("directional", s.LightsDirectional);
                    Show("point", s.LightsPoint); Show("negative", s.LightsNegative);
                }
                Console.WriteLine($"total: ambient {ta}, directional {td}, point {tp}, negative {tn}");
                break;
            }
            case "objgfx":                                 // twinsdump <rm2> objgfx [regex] : object -> OGI (collision?) -> materials (layer, FBA)
            {
                var reo = new Regex(args.Length > 2 ? args[2] : ".", RegexOptions.IgnoreCase);
                T Find<T>(uint id) where T : TwinsItem => items.Select(i => i.item).OfType<T>().FirstOrDefault(i => i.ID == id);
                string Mat(uint id)
                {
                    var m = Find<Material>(id); if (m == null) return $"?{id}";
                    return $"{m.Name.TrimEnd('\0')}[L{m.Unknown} FBA {string.Join("", m.Shaders.Select(s => s.AlphaCorrectionValue ? "1" : "0"))}]";
                }
                bool idsOnly = args.Length > 3 && args[3] == "ids";   // objgfx REGEX ids : "objectname<TAB>materialID<TAB>name" per material
                foreach (var (item, path) in items.Where(i => i.item is GameObject))
                {
                    var o = (GameObject)item;
                    if (!reo.IsMatch(o.Name)) continue;
                    if (idsOnly)
                    {
                        foreach (var ogiId in o.OGIs.Concat(o.cOGIs).Distinct())
                        {
                            var gi = Find<GraphicsInfo>(ogiId); if (gi == null) continue;
                            var mids = gi.ModelIDs.Values.Select(l => Find<RigidModel>(l.ModelID)).Where(r => r != null).SelectMany(r => r.MaterialIDs).ToList();
                            var sk = gi.SkinID != 0 ? Find<Skin>(gi.SkinID) : null;
                            if (sk != null) mids.AddRange(sk.SubModels.Select(s => s.MaterialID));
                            foreach (var mid in mids.Distinct()) { var m = Find<Material>(mid); Console.WriteLine($"{o.Name}\t{mid}\t{m?.Name.TrimEnd('\0')}"); }
                        }
                        continue;
                    }
                    Console.WriteLine($"object {o.ID} {o.Name}");
                    foreach (var ogiId in o.OGIs.Concat(o.cOGIs).Distinct())
                    {
                        var gi = Find<GraphicsInfo>(ogiId); if (gi == null) { Console.WriteLine($"   ogi {ogiId}: ?"); continue; }
                        var mats = gi.ModelIDs.Values.Select(l => Find<RigidModel>(l.ModelID)).Where(r => r != null).SelectMany(r => r.MaterialIDs).Distinct().Select(Mat);
                        var skin = gi.SkinID != 0 && Find<Skin>(gi.SkinID) != null ? Find<Skin>(gi.SkinID).SubModels.Select(s => s.MaterialID).Distinct().Select(Mat) : Enumerable.Empty<string>();
                        Console.WriteLine($"   ogi {ogiId}: collision {gi.CollisionData.Length}, rigid {string.Join(" ", mats)}{(skin.Any() ? "  skin " + string.Join(" ", skin) : "")}{(gi.BlendSkinID != 0 ? "  blendskin" : "")}");
                    }
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
                    if (args.Contains("-v"))
                        Console.WriteLine($"      instances [{string.Join(",", inst.InstanceIDs)}]  positions [{string.Join(",", inst.PositionIDs)}]  paths [{string.Join(",", inst.PathIDs)}]  i321 [{string.Join(",", inst.UnkI321)}]  f [{string.Join(",", inst.UnkI322)}]  i323 [{string.Join(",", inst.UnkI323)}]");
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
                // ops (one per line): addbody, copybody, clearbodies, appendcmds, delcmd, movebody, settarget, setarg, skipprompt (see each branch)
                // Writes <outdir>/<id>.bin (serialized script item) for every edited script.
                var outDir = args[3]; System.IO.Directory.CreateDirectory(outDir);
                var byId = scripts.ToDictionary(s => s.ID);
                var edited = new HashSet<uint>();
                foreach (var raw in System.IO.File.ReadAllLines(args[2]))
                {
                    var line = raw.Split('#')[0].Trim(); if (line == "") continue;
                    var t = line.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
                    if (t[0] == "skipprompt")
                    {
                        // skipprompt auto [TEXT]              every reachable state that plays a cutscene (runs a script) with a live Triangle rule (cond 572)
                        // skipprompt SCRIPT STATE[,STATE] [TEXT]
                        // Shows hint TEXT (Language\AgentLab line index, default 24) on the bottom text bar while those states run.
                        bool auto = t[1] == "auto"; int ti = auto ? 2 : 3;
                        uint text = t.Length > ti ? uint.Parse(t[ti]) : 24;
                        var targets = auto
                            ? scripts.Where(x => x.Main != null).Select(x => (x, SkipStates(x.Main))).Where(x => x.Item2.Count > 0).ToList()
                            : new List<(Script, HashSet<int>)> { (byId[uint.Parse(t[1])], new HashSet<int>(t[2].Split(',').Select(int.Parse))) };
                        foreach (var (ps, states) in targets)
                        {
                            AddSkipPrompt(ps.Main, states, text);
                            edited.Add(ps.ID);
                            Console.Error.WriteLine($"skip prompt: {ps.ID} {ps.Main.name} states {string.Join(",", states)}");
                        }
                        continue;
                    }
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
                        // copybody SCRIPT TOSTATE FROMSTATE BODYIDX TARGET COND PARAM INTERVAL [THRESHOLD]
                        // appends a copy of body BODYIDX of FROMSTATE (its commands) to TOSTATE with a new condition/target
                        var src = StateAt(s.Main, int.Parse(t[3])).scriptStateBody; for (int k = 0; k < int.Parse(t[4]); k++) src = src.nextScriptStateBody;
                        float thrC = t.Length > 9 ? float.Parse(t[9], System.Globalization.CultureInfo.InvariantCulture) : (src.condition?.Threshold ?? 0.5f);
                        var body = new ScriptStateBody(s.Main.scriptGameVersion)
                        {
                            bitfield = (src.bitfield & 0xFF) | 0x600, scriptStateListIndex = int.Parse(t[5]),
                            condition = new ScriptCondition { Interval = float.Parse(t[8], System.Globalization.CultureInfo.InvariantCulture),
                                                              Threshold = thrC, ThresholdInverse = 1f / thrC }
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
                        AppendCmd(body, copy);
                    }
                    else if (t[0] == "delcmd")
                    {
                        // delcmd SCRIPT STATE BODYIDX CMDIDX : remove one command from a body
                        var body = BodyAt(st, int.Parse(t[3]));
                        var cmds = new List<ScriptCommand>(); for (var c = body.command; c != null; c = c.nextCommand) cmds.Add(c);
                        cmds.RemoveAt(int.Parse(t[4]));
                        for (int k = 0; k < cmds.Count; k++)
                        {
                            cmds[k].nextCommand = k + 1 < cmds.Count ? cmds[k + 1] : null;
                            cmds[k].internalIndex = k + 1 < cmds.Count ? cmds[k].internalIndex | 0x1000000 : cmds[k].internalIndex & ~0x1000000;
                        }
                        body.command = cmds.Count > 0 ? cmds[0] : null;
                        body.bitfield = (body.bitfield & ~0xFF) | cmds.Count;
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
    static uint F(float f) => BitConverter.ToUInt32(BitConverter.GetBytes(f), 0);

    static ScriptCommand Cmd(int ver, ushort vtable, params uint[] args)
    {
        var c = new ScriptCommand(ver) { VTableIndex = vtable };   // sizes the argument list for this command
        for (int k = 0; k < args.Length; k++) c.arguments[k] = args[k];
        return c;
    }

    static void AppendCmd(ScriptStateBody b, ScriptCommand c)
    {
        if (b.command == null) b.command = c;
        else
        {
            var last = b.command; while (last.nextCommand != null) last = last.nextCommand;
            last.nextCommand = c; last.internalIndex |= 0x1000000;
        }
        int n = 0; for (var x = b.command; x != null; x = x.nextCommand) n++;
        b.bitfield = (b.bitfield & ~0xFF) | n;
    }

    // States that play a cutscene (run a script) and can be skipped with Triangle (a condition-572 body), reachable from the start.
    static HashSet<int> SkipStates(Script.MainScript m)
    {
        var reach = Reachable(m); var result = new HashSet<int>(); int i = 0;
        for (var st = m.scriptState1; st != null; st = st.nextState, i++)
        {
            if (!reach.Contains(i) || st.scriptIndexOrSlot < 0 || st.IsSlot) continue;
            for (var b = st.scriptStateBody; b != null; b = b.nextScriptStateBody)
                if (b.condition != null && b.condition.VTableIndex == 572) { result.Add(i); break; }
        }
        return result;
    }

    // Hint text while STATES run: BottomTextDisplay(text) on every transition into the set, BottomTextClear on every transition out of it
    // (moving between two of its states keeps it up). A start state inside the set gets a new entry state.
    // Only the text is set: BottomTextShow would switch the bottom bar from the cutscene letterbox to the translucent hint strip, and
    // the letterbox would disappear. Without it the text is drawn inside the letterbox bar.
    static void AddSkipPrompt(Script.MainScript m, HashSet<int> states, uint text)
    {
        int ver = m.scriptGameVersion;
        Func<ScriptCommand> display = () => Cmd(ver, 603, text, F(0.5f), F(0.92f), F(1f), F(1f), F(1f), 0);   // BottomTextDisplay(line, x, y, scale, ...)
        Func<ScriptCommand> clear = () => Cmd(ver, 608);                                          // BottomTextClear()
        int i = 0; ScriptState lastState = null;
        for (var st = m.scriptState1; st != null; st = st.nextState, i++)
        {
            lastState = st;
            for (var b = st.scriptStateBody; b != null; b = b.nextScriptStateBody)
            {
                if ((b.bitfield & 0x400) == 0) continue;                                          // no transition
                bool from = states.Contains(i), to = states.Contains(b.scriptStateListIndex);
                if (!from && to) AppendCmd(b, display());
                else if (from && !to) AppendCmd(b, clear());
            }
        }
        if (states.Contains(m.StartUnit))
        {
            var entry = new ScriptState(ver) { bitfield = 0x0421, scriptIndexOrSlot = -1 };   // one "Next" body, like the game's pass-through states
            var body = new ScriptStateBody(ver)
            {
                bitfield = 0x600, scriptStateListIndex = m.StartUnit,
                condition = new ScriptCondition { Interval = 0f, Threshold = 0.5f, ThresholdInverse = 2.0f }
            };
            body.condition.VTableIndex = 0;                                                        // Next
            AppendCmd(body, display());
            entry.scriptStateBody = body;
            lastState.bitfield = (short)(lastState.bitfield | unchecked((short)0x8000)); lastState.nextState = entry;
            m.StartUnit = i;
        }
    }

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
