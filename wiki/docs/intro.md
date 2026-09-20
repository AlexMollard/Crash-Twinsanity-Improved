---
id: intro
title: Start here
sidebar_position: 1
slug: /
---

# Crash Twinsanity, from the inside

This is the working notebook for [Crash Twinsanity Improved](https://github.com/AlexMollard/Crash-Twinsanity-Improved),
a fix-and-polish mod for the PAL PlayStation 2 release. Everything here was worked out by taking the retail disc apart
and testing changes on a real emulator, so it is written the way it was found rather than the way a manual would put it.

![Crash on N. Sanity Beach, with HOLD TRIANGLE TO SKIP drawn in the letterbox bar at the bottom of the screen](/img/shots/skip-prompt-beach.png)

*The prompt the retail game never shows you, because the skip behind it was disabled before release. Captured from the
modded build on the test rig.*

It covers three things:

- **How the game works.** [What is on the disc](engine/overview), how levels are stored, how the
  [scripting](engine/scripts) that drives every cutscene, enemy and door is laid out, and where the interesting parts
  of [the executable](engine/executable) live.
- **How to change it.** [The build](modding/build) turns an untouched disc image into a patched one from
  [text recipes](modding/recipes); this explains how to write those recipes and how the
  [automated test rig](modding/rig) proves a change before it ships.
- **Where it came from.** [Who built Twinsanity](history/development) and under what conditions - a studio founded to
  make this one game, a project cancelled and restarted with the deadline intact, an engine inherited from *The Wrath
  of Cortex*, and an in-house scripting tool called AgentLab whose name is still sitting in the archive on your disc.
  Also [what was cut](history/cut-content), [how the six retail versions differ](history/versions), and
  [what two decades of speedrunners found](history/speedrunning). A surprising amount of what this mod fixes turns
  out to be a schedule problem rather than a bug.

## If you only read one page

[**Scripts**](engine/scripts) is the heart of it. Twinsanity has no scripting language in the usual sense - no Lua, no
bytecode, no text files on the disc. Every behaviour in the game is a small state machine stored as data inside the
level archive, and once you can read one, most of the game opens up.

## The short version

| | |
|---|---|
| **Disc** | ISO 9660 + UDF. One 887 MB archive, `CRASH.BD`, holds every level; `CRASH.BH` is its index. Movies are separate `.PSS` files. |
| **Levels** | One `.rm2` file each, a container of numbered *items* - models, animations, collision, objects, instances, scripts. |
| **Scripting** | Compiled state machines. Each state has rules (*condition → target state*) and each rule carries commands to run on the way out. Conditions and commands are engine functions picked by number. |
| **Cutscenes** | A *director* script plays a *scene* script; the actors have their own scripts and talk to each other with numbered user messages. |
| **Executable** | `SLES_525.68`, a 2 MB PS2 ELF loaded at `0x100000`. Patched word by word from a text file, with every original value checked first. |
| **Testing** | An isolated portable PCSX2 driven over the PINE protocol: virtual pad, RAM read/write, save states, screenshots, level warp. |

Three lookup pages sit behind all of it: every address quoted anywhere in this wiki is listed in
[Addresses](reference/addresses), every numbered condition and command in [Script ids](reference/script-ids), and the
vocabulary - *agent*, *body*, *instant state*, *orphan skip* - in the [Glossary](reference/glossary).

:::note What this is not
This is not a decompilation and not a complete map of the engine. It is the part that had to be understood to fix
specific bugs, written down so the next session - or the next person - does not have to find it again. Where something
is a guess, it says so.
:::

## Credits and prior art

The [Twinsanity Editor](https://github.com/Smartkin/twinsanity-editor) by Smartkin, NeoKesha and contributors is what
makes reading level files possible at all; this project uses its library. The
[twinsanity-reversed](https://github.com/Smartkin/twinsanity-reversed) Ghidra database gave names to a lot of the
engine functions referenced here.
