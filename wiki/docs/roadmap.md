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
| **11** | **4** | **4** | **5** | **2** | **2** |

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
| 🧭 | **Evil Crash runs in circles (Bandicoot Pursuit)** | The famous PAL one, and the cause is now pinned to the engine: his move script has no facing condition and no turn command at all - it sets a focus position and the engine steers him - so there is nothing in the script data to tune. **The blocker is reproduction.** The chase gate is known exactly: Evil Crash waits for user message **269**, then branches on **counter 26** (1/2/3 = the three phases), and the summoner only sends 269 once it has a focus object, otherwise it runs `COM_GENERIC_CREATURE_ERROR`. Neither teleporting into the trigger box nor moving inside it starts any of that. A test recipe that rewrites his conditions to enter PHASE1 on a timer does not start him either. His instance context is **not** disabled (the engine's ignore-all-events bit is clear, checked against objects that are demonstrably alive in the same level), and his object has only one script slot, so nothing can reach him with the "activated" event - his script has to be started at spawn. So he is wakeable but never woken. The chunk-loading theory has been tested and **does not hold**: the loader's "wanted" set does change as Crash moves, but "done" trails "wanted" in every level checked, including ones where actors demonstrably run, so a trailing bit is normal rather than a stall. The open question is still what calls `ActivateObjectInstance` for the others and skips him. |
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
| 🐌 | **Slow menus** | [Documented as a PAL trait](https://beyondtwinsanity.com/evolution/versions/), and measured: on the retail disc a menu button takes about **0.82 s** to produce any visible response. The modded build's figure is still missing - those runs were made against a test ISO another session had rebuilt with a different executable, so they measured nothing. The harness is `tools/rig/menu_time.py`. |
| 🧷 | **Cortex detaches from Crash at Farmer Ernest's fence** | [Reported for PAL](https://beyondtwinsanity.com/evolution/versions/). Not yet reproduced. |
| 🎭 | **Leftovers after being hurt into a cutscene** | The floating mask and Cortex's floating ray gun are the same family as the invisible-Crash bug, which is fixed; these are separate objects whose state is not reset. **Did not reproduce** on the rig: taking the mask from the Aku Aku crate, losing it to a worm and running straight into the beach training scene left nothing floating, at 0.15 s and 0.2 s between the hit and the scene. Either the window is tighter than that or the teleport-driven repro is not close enough to how it happens in play. |
| 🐜 | **Enemies that freeze solid** | The "undefeatable ant" in Cavern Catastrophe stays frozen until you lose a life. Sounds like a script state machine that stops stepping - the same shape as several things already fixed. |


## ✔️ Checked, fine here

| | Item | Finding |
|:-:|---|---|
| ✔️ | **Touching the stunned Coco** | Kills Crash on NTSC-U and Xbox, and it is the case people ask about most. It does not happen on PAL: two sources say so, and a rig sweep of the Psychetron room after the scene landed no hits at all. |
| ✔️ | **Skipping movies** | They were never unskippable - ✕ has always stopped them, about a second in. The mod adds △ for consistency; measured 54.3 s untouched, 7.0 s with ✕ on the original disc. |


## ⛔ Not doing

| | Item | Why |
|:-:|---|---|
| ⛔ | **Skipping the falling-totem scene** | The skip drops Crash into the totem chase before it is set up and he dies. The developers cut that one for the same reason; it stays unskippable. |
| ⛔ | **New levels and new art** | This is a fix-and-polish mod: restoring what is on the disc, not adding to it. The *Beyond Twinsanity* mods (AnTime Agony, Lava Caves) add content - install them with [CrateModLoader](https://github.com/TheBetaM/CrateModLoader). |
