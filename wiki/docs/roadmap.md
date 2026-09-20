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

| ✅ Shipped | 🔭 Next up | 🧱 Bigger projects | 🔬 Investigating | 📋 Reported | ✔️ Checked, fine here | ⛔ Not doing |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **11** | **4** | **4** | **5** | **5** | **3** | **2** |

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
| 🧭 | **Evil Crash runs in circles (Bandicoot Pursuit)** | The famous PAL one. Four candidate causes have been eliminated by measurement and one premise reversed, but **the chase has never been reproduced on the rig** - and the method everyone assumed was reproducing it turned out to put Crash in a void. [The full account is below](#evil-crash-what-has-actually-been-measured). |
| 🦭 | **Rusty Walrus runs in circles** | [Reported for PAL](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity), and the walrus uses the same route-node steering as Evil Crash - very likely one bug behind two chases. It did not reproduce standing still (the walrus arrived and killed Crash 220 times in 32 s), so the repro needs the player actually running the route. |
| 🔒 | **Softlock after the Rusty Walrus chase** | Mashing jump through the N. Gin cutscene stops the Brio/Tropy scene playing and strands Crash on the boss iceberg. **Not introduced by this mod**, and this mod's own skip of that scene is verified to leave the follow-on intact - but the vanilla bug has not been reproduced here. [Full account below](#the-softlock-after-the-walrus-chase). |
| 🗿 | **The rest of the contact-damage reports** | The Tiki Mon was the first. `tools/rig/hurthook.py` names whatever hit you, so the remaining reports get checked one at a time. |


### The softlock after the walrus chase

[The report](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity) says the jumping happens
*during the N. Gin TNT cutscene*, and that the effect is that the **following** Brio/Tropy scene never plays.
Nothing is skipped that lacks a skip path - scene A is disrupted and then fails to start scene B.

**Whose bug it is.** The Brio/Tropy scene is `act_HUB2_TO_HUB3_CUTSCENE_DIRECTOR1` in `gpa12`, the level that holds
`act_N_BRIO_MAN`, `act_N_BRIO_MONSTER` and `act_N_TROPY`. No recipe in `mod/levels/` touches `gpa11` or `gpa12`,
and `gpa12` contains no condition 572 and no message-244 handler anywhere in its 208 scripts - so this mod's
hold-△ cannot reach that scene at all.

**But scene A is a scene this mod does skip.** The Henchmania intro in `gpa11` has a developer skip:
`COM_HENCHMANIA_CUTSCENE_DIRECTOR_ACTIVATED` branches on condition 572 to `COM_HENCHMANIA_CUTSCENE_SKIP`, and this
mod's executable patch re-enables condition 572 game-wide. It was verified to skip; it had never been verified that
the next scene still plays.

| Run | First scene | Second scene starts | Ends at | Flow |
|---|---|---|---|---|
| Untouched | 15.0 s | after 2.5 s | `(-0.1, 0.0, -5.3)` | 13 |
| Hold △ (this mod's skip) | 1.5 s | after 2.5 s | `(-0.1, 0.0, -5.3)` | 13 |
| Mashing ✕ (the reported repro) | 14.9 s | after 2.5 s | `(-0.1, 0.0, -5.3)` | 13 |

**Both scenes were then identified from screenshots rather than assumed** - scene 1 shows Crash among exploding TNT
crates with this mod's *HOLD △ TO SKIP* prompt on it, scene 2 shows N. Tropy. The whole test rested on those two
identities and both had been taken from a name in a list. So for the case that matters, **this mod's skip leaves
the Brio/Tropy scene playing**, on direct evidence.

:::caution What this still does not show
Mashing ✕ did not shorten the first scene or break the hand-off, so **the original bug was never reproduced** and
this test has never been observed distinguishing a working hand-off from a broken one. The likely gap is context: a
plain warp into `gpa11` sets no story progress and skips the Rusty Walrus chase that precedes the scene in play.
The vanilla bug stays unconfirmed here.
:::

### Evil Crash: what has actually been measured

His move script has no facing condition and no turn command at all - it sets a focus position and the engine steers
him - so there is nothing in the script data to tune. The gate is known exactly: he waits for user message **269**,
then branches on **counter 26** (1/2/3 = the three phases), and his summoner only sends 269 once it has a focus
object, otherwise running `COM_GENERIC_CREATURE_ERROR`.

**Four causes eliminated, by measurement rather than argument:**

| | Finding |
|---|---|
| Chunk loading | The loader's "wanted" set does change as Crash moves, but "done" trails "wanted" in every level checked, including ones where actors demonstrably run. A trailing bit is normal, not a stall. |
| Counter 26 | All 48 script counters read zero after a warp, in every level, so the counter genuinely cannot select a phase on the rig. But writing it to 1 directly - it sticks, it reads back - moves him not at all. It sits downstream of message 269. |
| "Never woken" | **This was outright false**, and it was the premise most of the investigation rested on. A hook on `ActivateObjectInstance` shows **object 877 activated twice** in Bandicoot Pursuit, and his summoner too, both from `FindInstanceByChunkAndIndex+0x1cc` - the only caller that fires in any level tested. The control is a warp into the beach: 429 activations across 69 object ids, and 877 and 876 absent from both. |
| The failing focus searches | Hooks on the focus assign path (`0x121480`) and the found-nothing path (`0x1214E8`) showed the latter firing **330 times in sixteen seconds** against 8 in the Tiki boss level. Following the agents to their object ids gives `act_TWINTECH_BALL_DOCK`, `act_WUMPA_TREE` and `act_GLOBAL_SEAGULL` - scenery, running searches that find nothing, which is ordinary AI doing its job. |

:::danger The reproduction method never worked
Every test that claimed to put Crash inside the trigger used `(84.49, 4.2, -99.35)`. Sampling his position after a
teleport there shows him **falling continuously** - y runs 0.30, -0.77, -1.48, -3.28, then a respawn returns him and
he falls again, in a loop. There is no floor there. Walking instead reaches `(18.0, -58.4)`, stops responding, and
resets.

So "neither teleporting into the trigger box nor moving inside it starts the chase" was never a test of the chase.
It was a test of a void, and it was quoted as evidence for weeks.

**The coordinates were not invented, and the obstacle is now located exactly.** `twinsdump altdoc.rm2 triggers`
shows only two triggers in the level, and the first is the chase: centre `(84.49, 3.18, -99.35)`, extents
`(10.1, 6.01, 4.3)`, targeting `act_ALTEARTH_DOCAMOK_SUMMONER` through `act_MAP_ANY_MESSAGE_TO_TRIGGERED`. So that
coordinate is the trigger's own position, taken from the data rather than guessed.

What is missing is the **floor**. Walking north from the level's spawn at `(91.1, 0.0, -155.0)`, Crash covers about
33 units and then, at **z = -122**, his height drops to -3.5 and the game-flow state goes to 21 and then 18 -
death and respawn, not a cutscene - and he is returned to the spawn. The ground ends roughly **23 units short of
the trigger**. Teleporting straight to the trigger centre drops him through the same absence.

That is consistent with the pursuit's geometry streaming in during real play as Crash progresses through
`altdoc` / `altdoc_b` / `altdoc_c`, where a warp brings in only one file's chunk set. Which means the repro needs
either the missing chunk loaded deliberately or a save from a real playthrough - and no amount of instrumentation
aimed at the trigger will substitute, because the player cannot stand anywhere near it.

It went unnoticed because the position reads back *correct* immediately after the teleport - the rig's `teleport`
shifts every copy of Crash's x/z including respawn points, so he reappears at the same unreachable spot and a check
made once, or twice and slowly, agrees with itself. **A verification that only checks the moment after the action is
not a verification**, and a failure mode that makes repeated checks agree is more dangerous than one that makes them
disagree.
:::

**Where that leaves it.** `altdoc_b` and `altdoc_c` can be warped to directly and both put Crash on genuinely solid
ground - verified by sampling once a second for twelve seconds and seeing zero drift, the check the old coordinates
would have failed. In `altdoc_c` both the summoner and Evil Crash are **activated**, so they are alive there and
simply not searching; a focus trace from that spawn records only scenery and Cortex. So the remaining gap is
position or trigger, not which chunk file is loaded. Standing at a spawn is not being where the chase starts, and
reaching that place legitimately is the next piece of work.



## 🧱 Bigger projects

These are features rather than fixes, and each needs new tooling before it can even be attempted.

| | Item | What it would take |
|:-:|---|---|
| 🚩 | **Checkpoints in the long stretches** | A survey of every level file found 22 of the 93 substantial ones with no checkpoint crate placed at all, among them the biggest in the game - the Earth hub, the 10th-dimension lab exterior, the Rockslide start, the Academy hub. Some of those respawn you another way, so each needs checking by playing it. Adding one means adding an *instance* to a level, which `twinsdump` cannot do yet; that tooling is the actual work, and placements have to be chosen in-game rather than guessed from coordinates. |
| 🎥 | **Scenes that never play** | A survey said ten cutscene directors had nothing pointing at them. Redone with a method that validates itself, it is **five** - and none of them can be called unused yet, because how a trigger starts a scene turns out not to be understood. [Full account below](#scenes-that-never-play). |
| 💡 | **Lighting** | The levels have a real runtime lighting rig, and it is in the `.sm2` scenery files this mod has never opened: 140 ambient, 432 directional, 103 point and 11 negative lights across the game, evaluated per vertex. The Earth hub alone has a grey ambient, a warm key, a cool fill and four wide point lights. All of it is editable data that costs nothing at runtime, which makes it the one real lever for "better lit" - unlike Phong, which the PS2's hardware cannot do at all ([why](engine/lighting)). |
| 🎨 | **The rest of the rendering** | A survey of all 10,464 material shaders says the easy levers are already pulled: every one is gouraud-shaded with linear magnification and a slight sharpening LOD bias. Two findings came out of it - **no material in the game enables GS fog at all**, so the fog line is draw distance or vertex shading rather than a fog register; and the shadow-receiver set is finished, since a test build making all 3,218 remaining opaque materials receivers was indistinguishable from the shipped 580. What is left is code: draw distance and the shadow pass. The rig can A/B a rendering change with the framing locked (`RIG_GS`, plus a save state so only the rendering differs). |


### Scenes that never play

The original survey used `twinsdump refs`, which returns nothing for objects that plainly exist - including the
Henchmania director whose scene was later watched playing. `tools/scene_survey.py` replaces it by reading the
**trigger list**, and refuses to report at all unless it first finds that same director correctly marked as
triggered.

Across all **135** level files: 58 cutscene directors placed, **48 with a trigger targeting them**.

Of the ten without, three are untriggered *copies* of directors triggered elsewhere - `CAVERN` in four other
levels, `HUB2_TO_HUB3` in nine, `TOTEM_CUTSCENE_DIRECTOR1` in `docamok1`. A director sitting in a level that does
not trigger it is not an unused scene. **That leaves five with no trigger anywhere in the game:**

| Director | Level |
|---|---|
| `act_BR_CORTEX_PIPE_CUTSCENE_DIRECTOR` | `boiler_1` |
| `act_EARTH_HUB_CUTSCENE_DIRECTOR` | `hubd` |
| `act_ICELABINT_CUTSCENE_DIRECTOR` | `labint` |
| `act_UKAFIGHT_CUTSCENE_DIRECTOR` | `ukafight` |
| `act_UKAUKA_DEFEATED_CUTSCENE_DIRECTOR` | `ukafight` |

:::caution Five is a checklist, not a finding
A director without a trigger may still be started another way. `gpa11` holds an untriggered `HUB2_TO_HUB3` copy
whose scene plays anyway, 2.5 s after the Henchmania scene ends, so **scene chaining is real**; and `ICELABINT` was
already recorded as started by other events.

Two attempts to narrow this further both failed, and are recorded so they are not repeated:

- *"Their DEFAULT script is empty, so they are inert."* The working Henchmania director has the same empty
  `state 0 [start] bits=0x0000`. It distinguishes nothing.
- *"Warp in and idle, and see whether a scene plays."* That returns "no cutscene" in `gpa11` too, whose scene is
  confirmed playing, because Crash spawns short of the trigger and never reaches it.
:::

**And the mechanism is not what it looked like.** A hook on `ExecuteEvent` recording every dispatch shows the
Henchmania director receiving **event 0 at level load** from `RunObjectSpawnScript+0x6c` - identified by two id
routes agreeing and its name read as text out of memory - and **nothing at all afterwards**, including when the
trigger fires and its scene starts. So a trigger does not start its director with an activation event, and how it
does start one is now an open question rather than an assumption.

Anyone repeating this: **arm the tracer before the level loads**. The only dispatch a director gets happens during
the load, so arming after a state load records nothing and looks like a negative result.

## 🔬 Investigating

| | Item | Where it stands |
|:-:|---|---|
| 🌫️ | **The fog line** | A visible seam where the fog starts. Needs a level and a spot to reproduce before anything can be measured. |
| 🐌 | **Slow menus** | [Documented as a PAL trait](https://beyondtwinsanity.com/evolution/versions/). **This project has never actually measured it, and the 0.82 s figure published here previously was an artifact** - retracted. The harness timed how long after a press the screen first changed by more than a threshold, but the front end animates constantly: a control with **no input at all** crosses the same threshold every 0.71-0.73 s, five times out of five. So every reading near 0.8 s was the animation's own period, and one run produced 11.93 s, which is the attract demo starting rather than any response. A valid measurement needs a signal that only moves on input - the menu-selection variable in RAM, timed from press to change - in the same way that jump height had to come from the player object rather than from the screen. The harness now runs that control first and refuses to report if it fails. |
| 🧷 | **Cortex detaches from Crash at Farmer Ernest's fence** | [Reported for PAL](https://beyondtwinsanity.com/evolution/versions/). Not yet reproduced. |
| 🎭 | **Leftovers after being hurt into a cutscene** | The floating mask and Cortex's floating ray gun are the same family as the invisible-Crash bug, which is fixed; these are separate objects whose state is not reset. **Did not reproduce** on the rig: taking the mask from the Aku Aku crate, losing it to a worm and running straight into the beach training scene left nothing floating, at 0.15 s and 0.2 s between the hit and the scene. Either the window is tighter than that or the teleport-driven repro is not close enough to how it happens in play. |
| 🐜 | **Enemies that freeze solid** | The "undefeatable ant" in Cavern Catastrophe stays frozen until you lose a life, and a "frozen ant" report describes the same thing after sliding a lancer ant. It looked like a script state machine that stops stepping - the shape of several things already fixed - but the scripts say otherwise. The collector behaviour (`COM_ANT_SML_ECOLOGY_COLLECTOR`, the carrying-a-crate state the report names), the default behaviour and the attack behaviour contain **no death or damage references at all**, and nothing routes to `COM_ANT_SML_ECOLOGY_DEATH` from a state slot. So an ant's death is engine-driven through the creation-helper health system rather than script-driven, which means **a level recipe probably cannot fix this one** - unlike every fix shipped so far. Reclassifying it as engine work rather than script work, pending a rig repro. |


## 📋 Reported but not yet examined

The community's [glitch catalogue](https://glitchtopiathevideogameglitching.fandom.com/wiki/Crash_Twinsanity)
documents 37 bugs. Three of them are already on this page - the Evil Crash chase, the Rusty Walrus chase and the
undefeatable ant. These are the rest that look like this mod's territory, triaged but not investigated. They are
listed so the backlog comes from what players actually report rather than from what is convenient to find.

**Most promising: state left wrong when a cutscene ends.** This mod has already fixed one of these - Crash staying
invisible after being hurt into a scene - so the shape is familiar and the tooling exists.

| | Report | Why it looks tractable |
|:-:|---|---|
| 🕳️ | **Stuck in a pit** (Cavern Catastrophe) - double-jump over a pit and trigger the "We're friends right?" scene; when it ends Crash is far below and can only spin and turn | The scene does not reposition him, so wherever he was when it started is where he is left. Softlock-adjacent, and the same class of fix as the skips already shipped |
| 👤 | **Invisible Cortex** (Totem Hokum) - spin while entering the scene and Cortex stays invisible until Crash spins or slams | Directly the same family as the invisible-Crash fix already shipped, which was a visibility flag not being restored |
| 🏃 | **Non-animated walking Crash** (Cavern Catastrophe) - keep moving during the scene where Cortex warps out of Crash's hand, and Crash runs without his run animation afterwards | Animation state not reset on scene exit. Cosmetic, but the same mechanism and a cheap thing to confirm |
| ☠️ | **Instant dead Cortex at the Iceberg Lab** - on entry Cortex sometimes simply dies, in one of two poses | Reported as random, which usually means a race at level load. Worth a rig sweep because "random" is exactly what a rig is good at |
| 🐜 | **Frozen ant** (Cavern Catastrophe) - slide a lancer ant on the platform and it freezes in its slid animation | Sibling of the undefeatable ant already under investigation; likely one cause behind both |

Not this mod's territory, recorded so nobody re-triages them: out-of-bounds and geometry exploits (secret beaches,
getting inside Crash's house, out of Totem Hokum), deliberate glitch setups that need another glitch first, and
cosmetic oddities with no gameplay cost (bouncing chicken, frozen monkey, the extra Nina hand).

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
