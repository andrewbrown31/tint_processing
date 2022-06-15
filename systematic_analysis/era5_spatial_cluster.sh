#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=64GB
#PBS -l ncpus=8
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/era5_spatial_cluster.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/era5_spatial_cluster.e
#PBS -l storage=gdata/eg3
 
#Set up conda/shell environments 
source activate wrfpython3.6

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/era5_spatial_cluster.py

