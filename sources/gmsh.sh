#!/bin/bash

# convert .msh to .top
/home/pavery/bin/gmsh2top domain

# convert .top to .exo
/home/kratos/aero-f_rom_turorial/xp2exo domain.top domain.exo

