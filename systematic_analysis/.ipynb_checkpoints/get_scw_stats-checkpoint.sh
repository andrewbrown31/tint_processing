#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=32GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/get_scw_stats.o
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/get_scw_stats.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40+gdata/rt52+gdata/hh5

module use /g/data/hh5/public/modules
module load conda/analysis3

python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/get_scw_stats.py
