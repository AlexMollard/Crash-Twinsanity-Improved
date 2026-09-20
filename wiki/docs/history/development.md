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

:::note The restart is the root cause of a lot of this wiki
Starting again from near-scratch against an unchanged ship date is why so much was cut late, why some cutscenes
explain things that were never set up, and - most relevant here - why features like the cutscene skip ended up disabled
rather than finished. See [Cut and unshipped content](cut-content).
:::

## The name came out of a one-hour deadline

Working titles included *Unlimited*, *Fully Fluxed* and *Twinsane*. Publisher Vivendi eventually gave the team **one
hour** to produce a final title, failing which the game would ship as *Crash Bandicoot Unlimited*. Concept artist
**Keith Webb** came up with *Twinsanity* with about five minutes left.

## The technology

This is the part that connects directly to the rest of the wiki.

| | |
|---|---|
| **Engine** | Not written from scratch. The team started from the engine used for *Crash Bandicoot: The Wrath of Cortex* and "gradually added new stuff and improved various bits" - some subsystems were never replaced. |
| **Legacy code nickname** | Programmers referred to the inherited parts as **"Knutsford code"**, after Traveller's Tales' main studio. |
| **Languages** | "Mostly C++ with critical parts of the tech (like the renderer) hand written in assembler." |
| **Gameplay scripting** | An in-house tool called **AgentLab**. |
| **Engine afterlife** | *Super Monkey Ball Adventure*, the Oxford studio's next game, runs on the same engine and reuses some of Twinsanity's visuals and sound effects. |

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
