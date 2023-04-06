#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=48:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/skill_test_in10km_nulls.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/skill_test_in10km_nulls.e
#PBS -l storage=gdata/eg3+gdata/hh5
 
#Set up conda/shell environments 
module use /g/data/hh5/public/modules
module load conda/analysis3

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/skill_test_in10km_nulls.py

