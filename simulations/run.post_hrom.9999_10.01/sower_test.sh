#!/bin/bash

# Sower executable
SOWER_EXECUTABLE=/home/kratos/aero-f_rom_turorial/sower

# Postprocess fluid solution
$SOWER_EXECUTABLE -fluid -merge -con ../../data/OUTPUT.con -mesh ../../data/OUTPUT.msh \
	-result references/Solution.bin -output postpro/Solution

