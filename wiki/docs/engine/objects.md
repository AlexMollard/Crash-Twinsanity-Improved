---
id: objects
title: Objects, instances and agents
sidebar_position: 4
---

# Objects, instances and agents

## Three layers

| | |
|---|---|
| **Game object** | A *type*: a name, script slots, and the models, animations and sounds it uses. One per kind of thing in the level. |
| **Instance** | A *placement*: a position, a rotation, and which object it is. The Tiki Mon boss is one instance of object 658. |
| **Trigger** | A box in the world. When the player enters it, it activates or messages the objects it points at. |

```text
object 658 |HubD|old__HubD|act_TIKI_MON
   scripts: 0:4026(TIKI_MON_INIT)  12:4116(CORTEX_TIKI_FIGHT_SUCKED)
   objects:   anims: 65535  ogis: 65535

inst 1 Instance[0]  pos=(10.74, 25.6, 44.16)  obj 658 |HubD|old__HubD|act_TIKI_MON

trig 1 c1=(-9.44,26.96,7.46) c2=(17.6,3.16,2.51) args=(87,0,4104,35) -> |HubD|old__HubD|act_TIKI_MON
```

`c1` is the centre of the trigger box and `c2` its half-extents, which is all you need to teleport the test rig into
one. A trigger's `args` carry the message number and whatever the target script expects.

## The agent flags

Every instance has a **creation helper** (at instance + 16), and that helper holds a flags word (at helper + 16) that
decides how the thing behaves physically. Scripts change those flags with one command, `SetAgent`, and the argument
packs a mask and a value:

```text
SetAgent(0x00400040)   mask 0x40, value 0x40   → turn bit 6 on
SetAgent(0x00000040)   mask 0x40, value 0      → turn bit 6 off
SetAgent(6)            mask 0x06, value 0      → turn bits 1 and 2 off
```

The low half is the mask - which properties to touch - and the high half is the value. Each mask bit selects a
different property:

| Agent bit | What it changes |
|:-:|---|
| 0 | Activate / deactivate the actor entirely |
| 1 | Instance flag `0x400` |
| 2 | Instance flag `0x10` |
| 3 | Instance flag `0x8` |
| 4 | Instance flag `0x1000` |
| 5 | Collision on/off (`modelCollisionData` bit 0) |
| **6** | **Hurts the player on contact** (helper flags bit 8) |
| 7 | Collision flag bit 10, inverted |
| 8 | Collision flag bit 12 |
| 9 | Collision flag bit 9 |

## Contact damage

Bit 6 is the one behind "why did that hurt me?". The engine's contact handler (`0x13E010`) reads the toucher's helper
flags and only hurts the player when **bit 8** is set:

```c
if ((helper->flags >> 8 & 1) != 0) {
    if ((helper->flags >> 10 & 1) != 0)  hurt_player();        // always
    else if (event == 3 && player_state == 3)  hurt_player();  // only in the right state
}
```

The hit itself is a flags word of `0x400` and a damage of 1 - one mask, or one life if you have none.

`SetAgent(64)` - mask bit 6, value 0 - is how the game turns contact damage off, and it does so in 718 places. The
Uka Uka ice monster's death script uses `SetAgent(582)`, which clears bits 1, 2, 6 and 9 in one go.

This is the engine's general "does this thing hurt you" switch, not something bosses have. Evil Crash turns his own
off with `SetAgent(64)` the moment the Bandicoot Pursuit chase starts, so that the thing chasing you cannot damage
you by brushing past, and back on with `SetAgent(4194368)` when the chase ends.

:::info The Tiki Mon bug
The Totem Hokum boss never clears it. His fight ends with `BossModeExit`, a defeat cutscene and nothing else, so the
wreck lying in the arena still hits anything that touches it - a mask, or a life and the whole fight again. The fix is
one line: add the game's own `SetAgent(64)` to the last step of his script. His collision is untouched, so you can
still climb on him. See `mod/levels/harmless_after_defeat.ops`.
:::

## Finding out what hit you

`tools/rig/hurthook.py` installs a live hook on the contact-damage call and logs, for each hit, the attacking
instance, its creation helper, and the helper's flags. That is how the Tiki Mon was pinned down and how the fix was
verified: 19 hits before the fight, none after the defeat.

```python
import rig, hurthook
rig.level("hubd"); p = rig.Pine(); hurthook.install(p)
rig.teleport(10.74, 27.6, 44.16); time.sleep(3)
print(hurthook.read(p))   # (hits, [(attacker, helper, flags, player), …])
```

`tools/rig/hurt_sweep.py` does the same thing across a whole level, teleporting onto every instance in turn, and prints
the ones that landed a hit.
