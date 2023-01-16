#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=04:00:00,mem=64GB 
#PBS -l ncpus=8
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/merge_data_40_YYYY.o
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/merge_data_40_YYYY.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40+gdata/rt52+gdata/hh5

#source activate wrfpython3.6
module use /g/data/hh5/public/modules
module load conda/analysis3

STATE="nsw"
RID="40"
SUMMARY="max"

for m in {1..12}; do
   python /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data.py -year YYYY -month $m -rid $RID -state $STATE -summary $SUMMARY
done
