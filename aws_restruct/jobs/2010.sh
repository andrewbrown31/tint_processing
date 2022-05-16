#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/aws_restruct_2010.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/aws_restruct_2010.e 
#PBS -l storage=gdata/eg3

#Set up conda/shell environments 
source activate radar

python /home/548/ab4502/working/observations/aws_restruct/aws_restruct.py -y 2010

