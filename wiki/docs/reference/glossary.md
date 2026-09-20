---
id: glossary
title: Glossary
sidebar_position: 3
---

# Glossary

**Agent** — the physical side of an object instance: whether it collides, whether it hurts you, whether it is active
at all. Changed by the `SetAgent` command. See [Objects](../engine/objects).

**Body** — the file format's name for a **rule** inside a state: a condition, a target state, and a list of commands.

**Chunk** — a piece of a level that the streaming loader pulls in and drops as you move.

**Code cave** — unused space in the executable used to hold new instructions. This mod's is the unreferenced debug
function at `0x116EA8`.

**COM_ script** — the item that holds a script's actual states. Behaviours come in pairs: a small header item and the
`COM_` item next to it.

**Creation helper** — a per-instance block at `instance + 16` holding the flags the engine checks: contact damage
(bit 8 of helper + 16), invincibility (bit 10), and so on.

**Director** — the script that conducts a cutscene: run the opening, play the scene, tidy up. Named
`*_CUTSCENE_DIRECTOR_ACTIVATED`.

**Flow state** — the game's top-level state machine: 12 is normal gameplay, 19 is the credits (which the rig's warp
borrows). Read from the game-flow object at `0x30988C`.

**FMV / movie** — a pre-rendered `.PSS` video, as opposed to an in-engine scene. Telling them apart matters; see
[Cutscenes](../engine/cutscenes).

**Instance** — a placement of an object in a level: position, rotation, object id.

**Instant state** — a state whose rules are checked once as it is entered, and which then steps straight on
(flag `0x0400`). Adding a polled rule to one hangs it.

**Key / mark** — a named position belonging to a cutscene, used by `SetFocusToKey` + `PosWarp`. Only resolvable while
that scene is running.

**Level recipe (`.ops`)** — a text file of script edits applied at build time. See [Level recipes](../modding/recipes).

**Orphan skip** — a cutscene whose skip branch was moved into a state nothing can reach, so the executable patch alone
is not enough to bring it back.

**PINE** — the protocol PCSX2 exposes for external tools: read and write RAM, save and load states. The rig speaks it
on port 28012.

**Polled state** — a state whose rules are re-checked every frame (flag `0x0800`).

**Script slot** — a numbered place on an object type where a script lives. Slot 0 is the default behaviour; a trigger
or another script switches the object to its `_ACTIVATED` script; higher slots hold cutscene actor scripts.

**Sub-script** — a script that a state runs to completion while that state is active. The `Next` condition fires when
it ends.

**User message** — a numbered message sent between objects. 207 is "carry on", 244 is "the scene was skipped".
