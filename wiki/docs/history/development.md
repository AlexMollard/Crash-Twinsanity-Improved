---
id: development
title: How the game got made
sidebar_position: 1
---

# How the game got made

Everywhere else on this wiki, the game is taken apart from the outside. This page is the other half: who built it, what
they built it with, and why it is shaped the way it is. It is assembled from developer interviews and community
research rather than from the disc, so each claim is linked to where it came from.

It matters more than trivia. Several of the things this mod fixes are not mistakes - they are the visible edge of a
project that lost its funding, restarted from scratch, and shipped anyway.

## The studio existed to make this one game

Traveller's Tales set up an **Oxford studio for the sole purpose of reviving Crash Bandicoot** after Naughty Dog moved
on. It shipped exactly two games: *Crash Twinsanity* in 2004, and *Super Monkey Ball Adventure* in 2006, after which
the office was closed - reportedly because running a second site at that distance from the main Knutsford studio proved
awkward to manage.

For a lot of the team, Twinsanity was their **first commercial game**. Before they had PCs at their desks they spent
weeks playing the PS1 Crash games and reading Crash fan forums to work out what the series was supposed to feel like.

## It was a different game first

The project began as **Crash Bandicoot Evolution**, a markedly more serious game:

- The Evil Twins steal Crash's island and graft it onto a planet built from pieces of other worlds - Crash's home as
  one jigsaw piece in a larger sphere.
- An alien ant invasion spreading across the galaxy.
- **Foofie**, an alien sidekick riding on Crash's arm, used to solve puzzles.
- A structure closer to an RPG/platformer hybrid, with *The Legend of Zelda* cited as a reference.

Then *Ratchet & Clank* shipped in 2002 with a strikingly similar planet-hopping premise, and Traveller's Tales scrapped
Evolution and **restarted production**, this time aiming for the funniest possible Crash game rather than the most
epic one. The deadline did not move.

![Timeline: Crash Bandicoot Evolution runs from 2001 until Ratchet and Clank ships in late 2002, when the project restarts as Twinsanity against the same ship date, leaving under two years, with prototype milestones in 2003 and 2004](/img/twinsanity-schedule.svg)

:::note The restart is the root cause of a lot of this wiki
Starting again from near-scratch against an unchanged ship date is why so much was cut late, why some cutscenes
explain things that were never set up, and - most relevant here - why features like the cutscene skip ended up disabled
rather than finished. See [Cut and unshipped content](cut-content).
:::

### Sixteen chapters, storyboarded

The disc's Extras gallery contains **161 storyboard pages**, filed in sixteen sets numbered in the game's own chapter
order - a record of what Twinsanity was planned to be, chapter by chapter, preserved inside the shipped product.

![Bar chart of storyboard pages per chapter: the first eight chapters carry 103 pages between them and peak at 17 for Ice Climb, while the last eight carry 58, with the finale set the smallest of any chapter at five pages](/img/storyboard-pages.svg)

The distribution is lopsided. The first eight chapters have **103 pages** between them, several with fourteen to
seventeen each; the last eight have **58**, and `13-Twinsanity` - the finale - has the fewest of any set at five.

:::note How much weight this carries
Suggestive, not proven. Page counts are not effort, and a short sequence can legitimately need fewer boards than a
long one. But the shape matches everything else on this page: a project that spent its planning early and was
finishing against a deadline by the end. It is unusual to be able to point at that from inside the disc rather than
from an interview.
:::

## The name came out of a one-hour deadline

Working titles included *Unlimited*, *Fully Fluxed* and *Twinsane*. Publisher Vivendi eventually gave the team **one
hour** to produce a final title, failing which the game would ship as *Crash Bandicoot Unlimited*. Concept artist
**Keith Webb** came up with *Twinsanity* with about five minutes left.

## The technology

This is the part that connects directly to the rest of the wiki.

| | |
|---|---|
| **Engine** | **Nu2**, Traveller's Tales' in-house technology. Not written for this game: the team started from the build used for *Crash Bandicoot: The Wrath of Cortex* and "gradually added new stuff and improved various bits" - some subsystems were never replaced. |
| **Legacy code nickname** | Programmers referred to the inherited parts as **"Knutsford code"**, after Traveller's Tales' main studio. |
| **Languages** | "Mostly C++ with critical parts of the tech (like the renderer) hand written in assembler." |
| **Gameplay scripting** | An in-house tool called **AgentLab**. |
| **Engine afterlife** | *Super Monkey Ball Adventure*, the Oxford studio's next game, runs on the same engine and reuses some of Twinsanity's visuals and sound effects. |

### Nu2, the engine with no name on the box

Twinsanity runs on **Nu2** - the engine Traveller's Tales built for themselves and then used for nearly twenty years.
Its reach is remarkable: every mainline Tt console and PC game from *The Wrath of Cortex* in 2001 through to *The Lego
Movie 2 Video Game* in 2019 is the same engine, iterated. The LEGO games that Traveller's Tales became famous for are
direct descendants of the thing Twinsanity is built on.

![Timeline of the Nu2 engine from 1997 to 2024: a Sonic R precursor, then the PlayStation 2 generation containing Crash Twinsanity in 2004, then the NUP, PS2-HD and Next-Gen branches carrying the LEGO games to 2019, then NTT and Unreal](/img/nu2-lineage.svg)

It is better described as a **framework than an engine** - a set of libraries rather than one monolith. The clearest
view of it comes from a sibling: *Haven: Call of the King*, Traveller's Tales' own 2002 PS2 game, shipped with symbol
names left in, and its executable is built from libraries called `nucore`, `nu3d`, `numath`, `nusound2`, `nups2`,
`mp2play`, `gamelib`, `edtools` and `coblib`. The source paths look like `..\nu2.ps2\nu3d\nuscene.c`: a library tree
named for the engine, postfixed with the target platform, which is how the same code reached PS2, Xbox, GameCube and
PSP.

![Diagram of the Nu2 framework as a stack: the game's own code on top, then the Nu2 libraries nucore, nu3d, numath, nusound2, coblib, mp2play, edtools and gamelib, then the nups2 platform layer](/img/nu2-libraries.svg)

Two of those names are worth pausing on, because Twinsanity clearly has both: `mp2play` is MPEG-2 playback, which is
what the [`.PSS` movies](../engine/movies) are, and `edtools` is editor tooling living inside the framework itself -
the family AgentLab belongs to.

:::note How firmly do we know this?
Not from the binary. Twinsanity's retail executable is **stripped** - there is not a single `nu2` symbol or source
path left in it, unlike Haven's. The attribution rests on two things instead: the developers' own statement that they
started from the *Wrath of Cortex* engine, and *Wrath of Cortex* being the first game on the documented Nu2 list; plus
the shared vocabulary below. It is an inference from a very short chain, not a string you can grep for.
:::

### The console was full

One number from this project's own reverse engineering says more about the conditions than any interview does.
Twinsanity uses **essentially all 32 MB of the PlayStation 2's memory**: an 11.5 MB general pool and a 16.6 MB
streaming buffer, leaving **8 KB of headroom**. Adding 8 KB of new code to the executable does not shrink some slack -
it breaks the boot outright, because the second allocation then overruns the heap.

The disc is packed the same way: not one spare sector between files. A bigger executable pushes everything after it
along.

That is a game shipped exactly to the edge of its hardware, by a team that had already built it once and started
again. It is also why this mod's own changes have to be paid for rather than simply added - the working code cave is
funded by shrinking the streaming buffer by precisely the cave's size, so total memory use matches retail to the
byte. The regression suite bears that out in practice as well as on paper: with the cave in place, every shipped
cutscene skip behaves unchanged and load times are identical. The details are on
[The executable](../engine/executable).

### The Haven Rosetta stone

Haven is useful beyond its symbol names, because it shipped its scripts as **plain text with the developers' own
documentation still in them**. Its `.flo` files - "Game Flow" - are commented command scripts with semaphores used as
variables, `GoTo` / `GoSub` / `Return`, and commands like `PlayLevelCutScene`, `WaitFade`, `PlayFMV`, `LoadLevel`,
`PreLoadLevel`, `SetCheckPoint` and `PlacePlayer`.

Hold that next to Twinsanity and the family resemblance is hard to miss. This wiki's
[glossary](../reference/glossary) defines **flow state** as "the game's top-level state machine" - the same Nu2 term.
`PlayFMV` and `LoadLevel` are doing the jobs Twinsanity's `PlayMovie` and streaming loader do, and `PlacePlayer` /
`SetCheckPoint` are `PosWarp`'s relatives.

The difference is authoring, not architecture. Haven shipped human-readable text the engine parses at runtime.
Twinsanity shipped **compiled state machines** - AgentLab's output, conditions and commands reduced to numbers - which
is exactly why [Scripts](../engine/scripts) opens by saying the game has no scripting language. It had one; it just
did not put it on the disc.

### The formats travelled too

The file formats are the hardest evidence of continuity, because a single community tool reads two games' worth of
them. The [Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) supports *Crash Twinsanity* **and**
*Super Monkey Ball Adventure*, and its format list spells out what the extensions mean:

| Extension | What it is |
|---|---|
| `.RM2` / `.SM2` | PS2 level resources / PS2 scenery resources |
| `.RMX` / `.SMX` | the Xbox equivalents |
| `.RM` / `.SM` | the PSP versions, from *Super Monkey Ball Adventure* |
| `.BD` / `.BH` | the file archive and its index |
| `.MB` / `.MH` | the music archive and its index |

That is the same resource system surviving a change of platform *and* a change of franchise. It also settles a
question this wiki got wrong for a while: `.SM2` is **scenery**, not sound.

### What came after

Nu2's PS2 sub-engine was "purpose-built for the PlayStation 2, and then ported and modified for use on other
platforms" - it carried the LEGO games from *Lego Star Wars* through *Lego Batman*. When Traveller's Tales dropped PS2
support for *Lego Indiana Jones 2* the engine was revamped into the **Next-Gen (NXG)** branch, which ran until 2019.
Only with *Lego Star Wars: The Skywalker Saga* did they replace it, with a new engine called **NTT** - pronounced
"entity" - and the studio has since moved to Unreal.

So the direct line from the disc in your drive runs: *Wrath of Cortex* → **Twinsanity** → *Super Monkey Ball
Adventure* → *Lego Star Wars* → the entire LEGO catalogue.

### AgentLab is still on your disc

The scripting tool's name is not just an interview footnote - it is shipped in the retail build. The archive contains a
folder literally called `Language\AgentLab\`, holding the on-screen tip text in all five languages, and the executable
references a file named `Import\LevelAgents.axp`.

That is also where this wiki's vocabulary comes from. The engine calls a live object an **agent**, the command that
changes an object's physical flags is [`SetAgent`](../engine/objects), and the state machines described on the
[Scripts](../engine/scripts) page are what AgentLab was compiling. When you write a recipe that edits state 7 of
`COM_EARTH_WORM_START`, you are editing AgentLab's output.

:::tip Why the names survived
Because scripts, objects and instances kept the names the developers typed into AgentLab, the level files are far more
readable than a stripped binary has any right to be. Nearly everything on this wiki was found by reading those names.
:::

![A storyboard page drawn inside a film-strip frame with sprocket holes down both edges: an upper panel of Cortex in his N hat mid-action with motion lines and arrows marking the movement, and a lower close-up of the same figure, in greyscale marker over pencil](/img/shots/storyboard-nsanity.png)

*A storyboard from the N. Sanity set - the opening of the game being planned - as it ships in the disc's Extras
gallery. Developers' artwork, not a capture of the game.*

## Who did what

| Role | Person |
|---|---|
| Traveller's Tales founder, set up the Oxford studio | Jon Burton |
| Director / producer | David Robinson |
| Designer | Paul Gardner |
| Lead artist | Dan Tonkin |
| Concept art, and the game's title | Keith Webb |
| Level design and enemy AI | John "J Mac" McCann |
| Lead character modeller | Chris Abedelmassieh |
| Writer | Jordan Reichek, of *Ren & Stimpy* |
| Voice director | Chris Borders |
| Music | Spiralmouth |

John McCann's own account is worth reading if you work on enemies: hired as a level designer, he ended up designing
"about half of the levels in the game" and making "most of the core AI behaviours that drive all the enemies" - which
is to say, most of the scripts this wiki decodes.

Before professional voice acting was cast, lead artist Dan Tonkin voiced Cortex in the early demos.

![A pencil character design sheet on grey: a snarling, heavily muscled canine beast in a spiked collar, studded wristbands and a shoulder guard, drawn as two full-body poses with a large head study and a row of smaller head and expression sketches](/img/shots/concept-character-sheet.png)

*A character being worked out rather than a finished design - two poses, a head study, and a row of expressions.
Also from the disc's Extras gallery.*

### Cortex changed voice

Clancy Brown, Cortex's voice since the PS1 games, left over video game voice pay. **Lex Lang** replaced him and was
directed to play Cortex as flamboyant and self-absorbed rather than straightforwardly mean; Lang has cited *Monty
Python* as an influence. It is the single biggest reason Twinsanity's Cortex reads as a comic lead rather than a
villain.

## The soundtrack has no instruments in it

The score was composed, performed, arranged and produced by the a cappella group **Spiralmouth**: **every sound in the
music is a human voice**, with no instruments at all. It was recorded and mixed by Gabriel Mann at Asylum Recording
Studios in Los Angeles.

Composer Rebecca Kneubuhl has described being given loose per-level guidance that kept shifting as the game changed,
and an executive producer who never found anything too weird. Writing for voices instead of a band changes the
composition from the start, not just the timbre.

There was also a more conventional option: an unused theme, a remix of the Crash theme used since *Warped*, credited to
John McCann and later posted to Jon Burton's GameHut channel.

## How it landed

- Released **28 September 2004** in North America, **8 October 2004** in Europe, **28 October 2004** in Australia, and
  **9 December 2004** in Japan.
- PlayStation 2 and Xbox. A **GameCube port was cancelled**, reportedly on the back of other Vivendi titles
  underperforming on the platform.
- Two separate mobile games followed in late 2004: an I-play title, and *Crash Twinsanity 3D* for 3G handsets.
- Reviews were mixed, averaging in the mid-60s. The open, connected world was welcomed after the corridors of *The
  Wrath of Cortex*; the camera, the controls and the checkpoint spacing were not. The a cappella score split reviewers
  completely.
- In the UK it entered the charts at #25 and stayed in the top 40 through Christmas 2004.

## The sequel that never happened

There was no *Twinsanity 2*. Traveller's Tales pitched **Cortex Chaos**, in which a Cortex invention sucks Crash into
television programmes, each show supplying its own environment and enemies. It was not picked up; the series went to
Radical Entertainment and *Crash of the Titans*.

Paul Gardner's summary of Twinsanity is the one most of the team seem to share - a game "made with love", technically
rough, handmade, and built by people trying to do right by what Naughty Dog left them.

## Sources

- [Crash Twinsanity Development - The Crash Bandi-pedia](https://thecrashbandipedia.miraheze.org/wiki/Crash_Twinsanity_Development)
- [Crash Twinsanity - Wikipedia](https://en.wikipedia.org/wiki/Crash_Twinsanity)
- [J Mac (Design) interview - Beyond Twinsanity](https://beyondtwinsanity.com/evolution/interviews/jmac/)
- [Interview with Paul Gardner - Crash Mania](https://www.crashmania.net/en/backstage/interviews/paul-gardner/)
- [Interview with Keith Webb - Crash Mania](https://www.crashmania.net/en/backstage/interviews/keith-webb/)
- [Interview with Rebecca Kneubuhl - Crash Mania](https://www.crashmania.net/en/backstage/interviews/rebecca-kneubuhl/)
- [Unused Content - Beyond Twinsanity](https://beyondtwinsanity.com/evolution/category/unused-content)
- [Traveller's Tales Oxford Studio - MobyGames](https://www.mobygames.com/company/58833/travellers-tales-oxford-studio/games/)
- [Engine - Traveller's Tales Lego Game Modding Wiki](https://ttmodding.fandom.com/wiki/Engine) - the Nu2 lineage and
  its sub-engines
- [Poking and Prodding Haven - Mark Sowden, TalonBrave.info](https://talonbrave.info/2025/09/10/haven.html) - the Nu2
  library list, the Game Flow scripts and their documentation comments
- [Twinsanity Editor README](https://github.com/Smartkin/twinsanity-editor/blob/master/README.MD) - the format list
  across Twinsanity and *Super Monkey Ball Adventure*
