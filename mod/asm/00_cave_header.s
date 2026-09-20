# First bytes of the code cave. Nothing calls this; it is here so that anything looking at memory - the test
# rig, a save state, PCSX2's debugger - can tell at a glance that the second load segment made it into RAM.
#
#   tools/rig/rig.py read 0x3DB210 2      ->  53415243 ("CRAS")  00002000
#
# The cave is mapped at 0x3DB200 but code starts 16 bytes later: the boot-time bss clear runs one 128-bit
# store past the end of .bss, so 0x3DB200-0x3DB20F is wiped after the segment loads. See tools/elfpatch.py.

.cave cave_header
    .word 0x53415243              # 'CRAS'
    .word 0x00002000              # cave size, kept in step with elfpatch.CAVE_SIZE
