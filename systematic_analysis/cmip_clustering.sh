#!/bin/bash

#PBS -P eg3 
#PBS -q hugemem
#PBS -l walltime=48:00:00,mem=512GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/cmip_clustering.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/cmip_clustering.e
#PBS -l storage=gdata/eg3
 
#Set up conda/shell environments 
source activate wrfpython3.6

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/cmip_clustering.py

