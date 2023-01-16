#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=10:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/tint_driver_73_YYYYMMDDHHMM1.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/tint_driver_73_YYYYMMDDHHMM1.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 73 -t1 YYYYMMDDHHMM1 -t2 YYYYMMDDHHMM2 --azi_shear True

#Post process tracks
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 73_YYYYMMDD3_YYYYMMDD4 --state qld --save True --max_stn_dist 100

