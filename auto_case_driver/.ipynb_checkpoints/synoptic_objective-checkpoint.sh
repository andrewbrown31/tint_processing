#!/bin/bash

#PBS -P eg3 
#PBS -q express
#PBS -l walltime=24:00:00,mem=64GB 
#PBS -l ncpus=8
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/synoptic_objective.o
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/synoptic_objective.e
#PBS -l storage=gdata/eg3+gdata/hh5+gdata/rt52
 
#Set up conda/shell environments 
module use /g/data/hh5/public/modules
module load conda/analysis3

python /home/548/ab4502/working/observations/tint_processing/auto_case_driver/synoptic_objective.py
