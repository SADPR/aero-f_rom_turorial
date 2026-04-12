#!/bin/bash

NS=8

XP2EXO_EXECUTABLE=/home/kratos/aero-f_rom_turorial/xp2exo

# Convert fluid outputs to .exo format
$XP2EXO_EXECUTABLE ../../sources/domain.top fluid_solution.exo \
		   ../../sources/domain.top.dec.$NS \
		   postpro/Pressure.xpost postpro/Velocity.xpost \
                   postpro/Vorticity.xpost
