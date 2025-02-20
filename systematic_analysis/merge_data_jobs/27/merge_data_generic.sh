#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=32GB 
#PBS -l ncpus=8
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/merge_data_27_YYYY.o
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/merge_data_27_YYYY.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40+gdata/rt52

source activate wrfpython3.6

STATE="sa"
RID="27"
SUMMARY="max"

for m in {1..12}; do
   python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data.py -year YYYY -month $m -rid $RID -state $STATE -summary $SUMMARY
done
