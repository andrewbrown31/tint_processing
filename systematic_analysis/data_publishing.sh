#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=12:00:00,mem=32GB 
#PBS -l ncpus=16
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/data_publishing.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/data_publishing.e
#PBS -l storage=gdata/eg3+gdata/hh5+scratch/eg3
 
#Set up conda/shell environments 
module use /g/data/hh5/public/modules
module load conda/analysis3

python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/data_publishing.py

