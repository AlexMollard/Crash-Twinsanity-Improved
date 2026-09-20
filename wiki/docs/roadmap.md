---
id: roadmap
title: Roadmap
sidebar_position: 2
---

# Roadmap

What is shipped, what is next, and what has been ruled out. Nothing ships until the automated
[rig](modding/rig) has played it.

Most of the open list comes from bugs the community has documented for the PAL release, or from surveys of the level
data. Each line says where it stands and what is in the way.

| ✅ Shipped | 🔭 Next up | 🧱 Bigger projects | 🔬 Investigating | ✔️ Checked, fine here | ⛔ Not doing |
|:-:|:-:|:-:|:-:|:-:|:-:|
| **11** | **4** | **4** | **5** | **3** | **2** |

## ✅ Shipped

| | Fix | What you notice |
|:-:|---|---|
| ⏭️ | **Cutscene skip** | Hold △ and the scene ends. 16 scenes needed their cut branch rebuilt in the level data; the rest came back with the executable patch. [Status](modding/what-changed) |
| 💬 | **Skip prompt** | *HOLD △ TO SKIP* in the letterbox, in all five languages, only while a scene can actually be skipped. |
| 🎬 | **Movies answer △** | They only stopped for ✕ before; now they take the same hold-△ as everything else, logos included. |
| 🛡️ | **Invincibility that works** | Three masks now survive TNT, Nitro and bombs instead of dying to them. |
| 🗿 | **A beaten boss stays beaten** | The defeated Tiki Mon no longer hits you when you walk into it - a [long-standing report](https://crashtwinsanity.fandom.com/wiki/Tikimon). |
| 👻 | **Visible Crash** | Getting hurt just before a cutscene no longer leaves him invisible for the rest of the level ([reported here](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity/Cutscene_Glitches_List)). |
| 🌑 | **Shadows on crates** | Crash's shadow falls on crates, so you can see where you will land. |
| ⏱️ | **Faster loading** | Level loads 25-35% shorter from the ISO alone, 40-50% with Fast CDVD. |
| 📺 | **Steady 60 fps** | 480p / 60 Hz output with the game's own frame timing matched to it - no more hub judder. |
| 🎞️ | **Movies at their real speed** | 25 fps instead of 30, so they no longer run a fifth too fast. |
| 📦 | **One-step build** | `Build Modded ISO.bat` turns your own disc image into a patched one and sets PCSX2 up to match. |


## 🔭 Next up

| | Item | Where it stands |
|:-:|---|---|
| 🧭 | **Evil Crash runs in circles (Bandicoot Pursuit)** | The famous PAL one, and the cause is now pinned to the engine: his move script has no facing condition and no turn command at all - it sets a focus position and the engine steers him - so there is nothing in the script data to tune. **The blocker is reproduction.** The chase gate is known exactly: Evil Crash waits for user message **269**, then branches on **counter 26** (1/2/3 = the three phases), and the summoner only sends 269 once it has a focus object, otherwise it runs `COM_GENERIC_CREATURE_ERROR`. Neither teleporting into the trigger box nor moving inside it starts any of that. A test recipe that rewrites his conditions to enter PHASE1 on a timer does not start him either. His instance context is **not** disabled (the engine's ignore-all-events bit is clear, checked against objects that are demonstrably alive in the same level), and his object has only one script slot, so nothing can reach him with the "activated" event - his script has to be started at spawn.

:::danger Correction: he *is* woken
This page said for some time that Evil Crash was "wakeable but never woken". **That was wrong**, and it was the premise most of the investigation rested on. A hook on `ActivateObjectInstance` recording every activation on hardware shows **object 877 activated twice** during a warp into Bandicoot Pursuit, in chunks 8 and 11, both from `FindInstanceByChunkAndIndex+0x1cc` - which is the only caller that fires at all, in every level tested. His summoner, object 876, is activated too. The control is a warp into the beach, where 429 activations across 69 distinct object ids are recorded and 877 and 876 are **never activated**, so the record discriminates rather than reporting everything as present.

So he is woken, his spawn script does start, and the failure is downstream of activation. That moves the question onto the summoner's chain: it only sends user message **269** once it has a focus object, and otherwise runs `COM_GENERIC_CREATURE_ERROR`.

**Focus acquisition has now been traced too**, with hooks on both the assign path (`0x121480`) and the found-nothing path (`0x1214E8`). In Bandicoot Pursuit the found-nothing path fires **330 times in about sixteen seconds**, from two agents alternating; the same measurement in the Tiki boss level fires it **8 times**. Every call comes from the focus resolver at `0x113A18` - the symbol table misattributes it to `Command_PlayMovie_Read+0x15xx`, but `0x113fdc` is its call to the clear path and `0x113ff4` its call to the assign path. So something in that level is running a focus search continuously and finding no candidate, which is the "tried and found nothing" case rather than "never tried".

Those two agents are **not** Evil Crash or his summoner. Following `agent + 0x84` to the instance context and reading its object id gives **871** for both, where Evil Crash is 877 and the summoner 876. `agent + 0x7c` reads `0xFFFF`, which turns out to be the engine's own "no id assigned" marker (`SetUndefinedID_` writes -1) rather than a bad read.

**The id read is sound; the doubts about it were not.** The tracer reaches the id by two independent walks through memory - directly via `agent + 0x84`, and the long way the engine's own code goes - and they agree on every single entry. Two earlier objections have both dissolved:

- *"871 is defined in none of the Bandicoot Pursuit files"* - true, and meaningless. Every level's object listing is sparse to the point of saying nothing: `hubd` lists 50 objects across a range of 0-1163, `altdoc` 44 across 0-1131. About **96% of the id range is absent** from each. Absence is the norm, not a signal.
- *"the control resolved to a wumpa tree"* - this one was **correct and was wrongly retracted**. Object ids are game-wide, so a name from any file that declares an id is that id's name; only the per-file tables are partial. 299 really is a wumpa tree.

**And the lead is dead. Object 871 is `act_TWINTECH_BALL_DOCK`** - ambient scenery, declared in `alta`, `corea`, `coreb`, `coreent` and `pretreas`, and never in any Bandicoot Pursuit file. The other two are `act_WUMPA_TREE` (299) and `act_GLOBAL_SEAGULL` (567). So the 288 failed focus searches are scenery running "look for something" searches that find nothing, which is ordinary AI doing its job - exactly the base rate worth being suspicious of, and the thing that made the number look alarming was only that nobody had measured what normal looks like.

The name source is `tools/re/objindex.py`, which collects every (id, name) pair across all 141 level files. Its control is that objects 876 and 877 come back as the summoner and Evil Crash, in all three chunk files each - two answers already known, reproduced before the method was trusted on one that was not.

Worth keeping in view that "runs a failing focus search continuously" describes a lot of ordinary AI - a patrol looking for a target that is not there is doing its job. Until the agent is tied to the chase, 288 failures against 8 is a lead, not a bug.
::: The chunk-loading theory has been tested and **does not hold**: the loader's "wanted" set does change as Crash moves, but "done" trails "wanted" in every level checked, including ones where actors demonstrably run, so a trailing bit is normal rather than a stall. The **counter theory has now been tested too, and is also not the blocker**: all 48 script counters read zero after a warp, in every level checked, so counter 26 genuinely cannot select a phase on the rig - but writing it to 1 directly (it sticks; it reads back) moves him not at all, with Crash outside the trigger box and standing inside it. The counter is downstream of message 269, exactly as the gate order implies. The open question is no longer what activates him - that is answered above - but whether his summoner ever acquires a focus object, since that is what gates message 269. |
| 🦭 | **Rusty Walrus runs in circles** | [Reported for PAL](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity), and the walrus uses the same route-node steering as Evil Crash - very likely one bug behind two chases. It did not reproduce standing still (the walrus arrived and killed Crash 220 times in 32 s), so the repro needs the player actually running the route. |
| 🔒 | **Softlock after the Rusty Walrus chase** | Mashing jump through the cutscene skips the Brio/Tropy scene and strands Crash on the boss iceberg with no music. Squarely this mod's territory - the same family as the invisible-Crash fix. |
| 🗿 | **The rest of the contact-damage reports** | The Tiki Mon was the first. `tools/rig/hurthook.py` names whatever hit you, so the remaining reports get checked one at a time. |


## 🧱 Bigger projects

These are features rather than fixes, and each needs new tooling before it can even be attempted.

| | Item | What it would take |
|:-:|---|---|
| 🚩 | **Checkpoints in the long stretches** | A survey of every level file found 22 of the 93 substantial ones with no checkpoint crate placed at all, among them the biggest in the game - the Earth hub, the 10th-dimension lab exterior, the Rockslide start, the Academy hub. Some of those respawn you another way, so each needs checking by playing it. Adding one means adding an *instance* to a level, which `twinsdump` cannot do yet; that tooling is the actual work, and placements have to be chosen in-game rather than guessed from coordinates. |
| 🎥 | **Scenes that never play** | Ten cutscene directors are placed in levels with nothing pointing at them - among them `UKAUKA_DEFEATED`, `BR_CORTEX_PIPE`, `CAVERN`, `EARTH_HUB` and `HUB2_TO_HUB3`. Some are started another way (the Iceberg Lab's turned out to be a movie), so each has to be checked before claiming anything. Any that genuinely never run are scenes sitting unused on the retail disc, and restoring one is the same kind of edit as restoring a skip. |
| 💡 | **Lighting** | The levels have a real runtime lighting rig, and it is in the `.sm2` scenery files this mod has never opened: 140 ambient, 432 directional, 103 point and 11 negative lights across the game, evaluated per vertex. The Earth hub alone has a grey ambient, a warm key, a cool fill and four wide point lights. All of it is editable data that costs nothing at runtime, which makes it the one real lever for "better lit" - unlike Phong, which the PS2's hardware cannot do at all ([why](engine/lighting)). |
| 🎨 | **The rest of the rendering** | A survey of all 10,464 material shaders says the easy levers are already pulled: every one is gouraud-shaded with linear magnification and a slight sharpening LOD bias. Two findings came out of it - **no material in the game enables GS fog at all**, so the fog line is draw distance or vertex shading rather than a fog register; and the shadow-receiver set is finished, since a test build making all 3,218 remaining opaque materials receivers was indistinguishable from the shipped 580. What is left is code: draw distance and the shadow pass. The rig can A/B a rendering change with the framing locked (`RIG_GS`, plus a save state so only the rendering differs). |


## 🔬 Investigating

| | Item | Where it stands |
|:-:|---|---|
| 🌫️ | **The fog line** | A visible seam where the fog starts. Needs a level and a spot to reproduce before anything can be measured. |
| 🐌 | **Slow menus** | [Documented as a PAL trait](https://beyondtwinsanity.com/evolution/versions/). **This project has never actually measured it, and the 0.82 s figure published here previously was an artifact** - retracted. The harness timed how long after a press the screen first changed by more than a threshold, but the front end animates constantly: a control with **no input at all** crosses the same threshold every 0.71-0.73 s, five times out of five. So every reading near 0.8 s was the animation's own period, and one run produced 11.93 s, which is the attract demo starting rather than any response. A valid measurement needs a signal that only moves on input - the menu-selection variable in RAM, timed from press to change - in the same way that jump height had to come from the player object rather than from the screen. The harness now runs that control first and refuses to report if it fails. |
| 🧷 | **Cortex detaches from Crash at Farmer Ernest's fence** | [Reported for PAL](https://beyondtwinsanity.com/evolution/versions/). Not yet reproduced. |
| 🎭 | **Leftovers after being hurt into a cutscene** | The floating mask and Cortex's floating ray gun are the same family as the invisible-Crash bug, which is fixed; these are separate objects whose state is not reset. **Did not reproduce** on the rig: taking the mask from the Aku Aku crate, losing it to a worm and running straight into the beach training scene left nothing floating, at 0.15 s and 0.2 s between the hit and the scene. Either the window is tighter than that or the teleport-driven repro is not close enough to how it happens in play. |
| 🐜 | **Enemies that freeze solid** | The "undefeatable ant" in Cavern Catastrophe stays frozen until you lose a life. Sounds like a script state machine that stops stepping - the same shape as several things already fixed. |


## ✔️ Checked, fine here

| | Item | Finding |
|:-:|---|---|
| ✔️ | **Touching the stunned Coco** | Kills Crash on NTSC-U and Xbox, and it is the case people ask about most. It does not happen on PAL: two sources say so, and a rig sweep of the Psychetron room after the scene landed no hits at all. |
| ✔️ | **Skipping movies** | They were never unskippable - ✕ has always stopped them, about a second in. The mod adds △ for consistency; measured 54.3 s untouched, 7.0 s with ✕ on the original disc. |
| ✔️ | **60 Hz and the slide deviation bug** | This mod runs the 50 Hz game at 60 Hz, which is the combination the community blames for slides throwing Crash off his heading - so it was the one regression this mod could plausibly have introduced. Measured frame-exactly, two cold boots per build: slide jumps are **about 1% shorter** at 60 Hz (9.848 → 9.746) and **no directional deviation appears** (+0.65° against +1.02°). The caveat is on the [page](history/versions#measured-on-the-rig): the bug is intermittent and a deterministic replay cannot sample intermittency, so this shows 60 Hz does not force the deviation, not that it cannot happen. |


## ⛔ Not doing

| | Item | Why |
|:-:|---|---|
| ⛔ | **Skipping the falling-totem scene** | The skip drops Crash into the totem chase before it is set up and he dies. The developers cut that one for the same reason; it stays unskippable. |
| ⛔ | **New levels and new art** | This is a fix-and-polish mod: restoring what is on the disc, not adding to it. The *Beyond Twinsanity* mods (AnTime Agony, Lava Caves) add content - install them with [CrateModLoader](https://github.com/TheBetaM/CrateModLoader). |
