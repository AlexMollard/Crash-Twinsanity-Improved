---
id: cut-content
title: Cut and unshipped content
sidebar_position: 2
---

# Cut and unshipped content

Twinsanity is famous for what is missing from it. The [restart](development#it-was-a-different-game-first) burned most
of the schedule, funding was reduced partway through, and the ship date did not move - so levels, characters and whole
mechanics were removed late, some of them after they were already playable.

This page is a survey of what is known to have been cut, and of what the developers left behind on the retail disc.
The second list is the interesting one for modding: those things are still in your ISO.

![Inventory of what was cut: eleven levels, six characters, five mechanics and two of the 10th-dimension islands, plus the things never removed from the retail disc - unused scripts, complete cutscenes with nothing to trigger them, unused voice lines and tips that never appear](/img/cut-inventory.svg)

## Before it was Twinsanity: *Crash Bandicoot Evolution*

The scrapped first version of the project. Its premise - the Evil Twins stealing Crash's island as one piece of a
patchwork planet, with an alien ant invasion spreading through the galaxy - was abandoned when *Ratchet & Clank*
arrived with much the same idea.

Bits of it survive in the shipped game if you know to look. The ants became **Ant Agony**. The Evil Twins kept their
name and their treasure. What did not survive was the tone, the scale, and **Foofie** - an alien sidekick who was to
ride on Crash's arm and be used to solve puzzles.

![Side by side: Evolution was serious and epic, with a patchwork planet, an alien ant invasion and Foofie the arm-riding sidekick, shaped as an RPG and platformer hybrid; Twinsanity is a comedy with Cortex carried as the tool and one open connected world](/img/evolution-vs-twinsanity.svg)

## The prototype trail

The community has a fairly precise build timeline, which is unusual for a game of this vintage:

| Build | Date | Notable |
|---|---|---|
| Evolution prototype, v2.613 | 6 Feb 2003 | One level only: `Levels/AIDemos/coop`, a test environment. 153 global particles in `StartUp/Default.ptl`. Debug text throughout the executable. |
| v8.016 | 4 Dec 2003 | Shown on GameHut. Early Wumpa Island and Jungle Bungle. |
| "Late February" build | Feb 2004 | Contains **The Bug Run** and High Seas Hi-Jinks. |
| v8.071 | 9 Mar 2004 | |
| Holiday demo | 7 Apr 2004 | |
| E3 demo | 8 Apr 2004 | NTSC-U demo. |
| *Unlimited* demo | 19 May 2004 | PAL demo - still carrying the fallback title. |
| Press preview | 19 Jul 2004 | |
| v9.279 | 30 Jul 2004 | |
| Review build | 3 Aug 2004 | |

The `AIDemos/coop` level name in the earliest prototype is a small mystery worth noting: the only level in the February
2003 build sits in a folder called **coop**.

## Cut levels

**The Bug Run** is the best documented, because Jon Burton showed the prototype on GameHut. It was an optional
underground route - reachable through a hole near the worm tutorial - where Crash is chased by bugs, played like the
boulder chases of the PS1 games, looping back to a second hole near where you entered. It was cut roughly six months
before launch for being too hard.

**Gone a Bit Coco** is the one the fandom will not let go. Cortex fights through the inside of Coco's mind, a place of
cuddly enemies and nonsensical cuteness. It was **playable but unfinished** - one area polished, with scripted
creatures - and was removed very late along with the character Capu Capu, specifically to stop the game crashing.

Others reported cut, in varying states of completeness:

- Rehab Lab
- Security Insanity
- Ocean Commotion
- Krazy Komodo Crash Course
- Wake Me Up Before You Coco
- A harbour bonus level
- An underwater scuba level
- A train / express level
- A hoverboard level

Two of the ten-dimension islands were also dropped.

## Cut characters

| Character | How far it got |
|---|---|
| **Coco as a playable character** | Planned as a full member of the party, with "Cyberspace" hacking levels in a *Tron* / *Matrix* style. |
| **N. Trance** | Modelled and textured; removed over cutscene loading problems. |
| **Evil Coco** | Model created, cutscene deleted. |
| **Good Cortex** | Possibly modelled; a counterpart to Evil Crash. |
| **Capu Capu** | Concept art only; cut alongside Gone a Bit Coco. |
| **Fake Crash** | A cameo, dropped. |

## Cut mechanics

- A **scissor kick**.
- **Controllable hoverboard** sequences - the hoverboard survives only as something that happens to you.
- A **punch** for Crash that destroyed scenery.
- **Lightsaber-style weapons**, originally conceived as something dropped by defeated ants that Crash could pick up and
  use.
- The classic **100-Wumpa extra life** animation, where the Crash icon floats from the fruit counter to the life
  counter.

Several cutscenes were also cut that would have explained how N. Tropy, N. Brio and Dingodile each learned about the
Evil Twins' treasure - which is why those characters turn up in the finished game already knowing things nobody told
them.

## What is still on the retail disc

This is the part that overlaps with the rest of this wiki. The developers did not strip the build; they stopped
referencing things.

- **Unused scripts and cutscenes.** A number of the game's own state machines are never triggered by anything, and
  several cutscenes exist in complete form without a path to them. Community members have got some of them running
  again.
- **Unused voice lines**, including alternate takes.
- **Tips that never appear**, inside the `Language\AgentLab\` text files.
- **An unused Extras image**, `McDonalds01.psm` - a group picture of the bosses, with a texture named `bosscomp`.
- **Cavern Catastrophe has no ambient track at all**, where every other level does.
- A **Spyro trailer**, present on some versions' discs but unreachable in-game - and missing entirely from the PAL PS2
  disc. See [Versions and regional differences](versions).

There is one more cross-game leftover: a test voice line in the *Crash Tag Team Racing* demo points at a different
version of the birthday cutscene, one that led straight into Mecha-Bandicoot's entrance.

:::tip If you want to restore something
Start with [Scripts](../engine/scripts) and [Cutscenes](../engine/cutscenes) to understand what a scene is made of,
then [Level recipes](../modding/recipes) for how to edit one. Restoring an orphaned cutscene means giving it a
trigger - the scene data is usually intact; what it has lost is the thing that starts it.
:::

## Where to actually see it

Almost none of this survives as text - it survives as screenshots, concept art and video, held by the people who did
the archival work. Those images belong to them or to the publisher, so this wiki links to them rather than re-hosting
them. If you want to *see* the cut content, these are the places:

| What you want to see | Where |
|---|---|
| **The Bug Run**, running, from the prototype | [Jon Burton's GameHut channel](https://www.youtube.com/watch?v=EFrJcxt-c_0) - he shows the December 2003 build himself |
| **Gone a Bit Coco** and the other cut levels | [Crash Mania's unused content galleries](https://www.crashmania.net/en/games/crash-twinsanity/unused-content/old-stuff/) |
| **Beta screenshots**, build by build | [Beyond Twinsanity's prototypes section](https://beyondtwinsanity.com/evolution/category/prototypes--early-builds) |
| **Cut characters and concept art** | [Keith Webb's own Crash concept portfolio](http://www.kokopolo.com/HOSTS/WEBBSTA/PROJECTS/UNIVERSAL/CRASH_CONCEPT/crash_concept.html) |
| **Deleted cutscenes** | [The Deleted Scenes playlist](https://www.youtube.com/playlist?list=PL9D33F6B9DDDBF83C) |
| **Unused scripts brought back** | [Beyond Twinsanity's retail unused-content pages](https://beyondtwinsanity.com/evolution/category/retail-game), where community members have got some of them running |

:::note Why there are no beta screenshots on this page
Everything visual here would be someone else's scan, capture or artwork. Linking costs you one click and credits the
people who preserved it; copying it into this repository would not. The screenshots this wiki *does* host are all
captures of the modded build from the project's own disc.
:::

## Sources

- [List of Crash Twinsanity pre-release and unused content - Crash Bandicoot Wiki](https://crashbandicootwiki.com/wiki/List_of_Crash_Twinsanity_pre-release_and_unused_content)
- [Crash Twinsanity unused content - Crash Mania](https://www.crashmania.net/en/games/crash-twinsanity/unused-content/near-final/)
- [The Bug Run - Crash Mania](https://www.crashmania.net/en/games/crash-twinsanity/unused-content/feb-2004-prototype/the-bug-run/)
- [Prototypes and early builds - Beyond Twinsanity](https://beyondtwinsanity.com/evolution/category/prototypes--early-builds)
- [Unused content, retail game - Beyond Twinsanity](https://beyondtwinsanity.com/evolution/category/retail-game)
- [Crash Twinsanity Development - The Crash Bandi-pedia](https://thecrashbandipedia.miraheze.org/wiki/Crash_Twinsanity_Development)
- [Interview with Keith Webb - Crash Mania](https://www.crashmania.net/en/backstage/interviews/keith-webb/)
