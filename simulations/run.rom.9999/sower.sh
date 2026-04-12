#!/bin/bash
set -euo pipefail

SOWER_EXECUTABLE="${SOWER_EXECUTABLE:-/home/kratos/aero-f_rom_turorial/sower}"

if [[ ! -x "$SOWER_EXECUTABLE" ]]; then
  echo "ERROR: sower executable not found or not executable: $SOWER_EXECUTABLE"
  exit 1
fi

mkdir -p postpro

"$SOWER_EXECUTABLE" -fluid -merge -con ../../data/OUTPUT.con -mesh ../../data/OUTPUT.msh \
  -result results/Pressure.bin -output postpro/Pressure

"$SOWER_EXECUTABLE" -fluid -merge -con ../../data/OUTPUT.con -mesh ../../data/OUTPUT.msh \
  -result results/Velocity.bin -output postpro/Velocity

"$SOWER_EXECUTABLE" -fluid -merge -con ../../data/OUTPUT.con -mesh ../../data/OUTPUT.msh \
  -result results/Vorticity.bin -output postpro/Vorticity


echo "Wrote xpost files in postpro/."
