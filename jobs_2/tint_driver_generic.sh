#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=02:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/tint_driver_2_YYYYMMDDHHMM1.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/tint_driver_2_YYYYMMDDHHMM1.e
#PBS -l storage=gdata/eg3+gdata/rq0
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 YYYYMMDDHHMM1 -t2 YYYYMMDDHHMM2
