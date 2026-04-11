#!/bin/bash

# convert .msh to .top
/home/pavery/bin/gmsh2top domain

# convert .top to .exo
/home/pavery/bin/xp2exo domain.top domain.exo

