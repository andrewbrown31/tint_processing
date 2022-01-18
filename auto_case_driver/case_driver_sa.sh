#!/bin/bash

#PBS -P eg3 
#PBS -q express
#PBS -l walltime=01:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_sa.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_sa.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 200710270000 -t2 200710272359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 200812090000 -t2 200812092359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201012070000 -t2 201012072359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201109280000 -t2 201109282359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201111080000 -t2 201111082359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201201290000 -t2 201201292359 --azi_shear False --steiner True
#python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201211300000 -t2 201211302359 --azi_shear False --steiner False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201410310000 -t2 201410312359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201512070000 -t2 201512072359 --azi_shear False --steiner True
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 27 -t1 201712180000 -t2 201712182359 --azi_shear False --steiner True

#Note that 2012-11-30 and 2017-12-18 have the same gust value, so can be sorted differenly

#Post process tracks and combine with AWS gust data
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20071027_20071027 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20081209_20081209 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20101207_20101207 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20110928_20110928 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20111108_20111108 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20120129_20120129 --state sa --save True --min 10 --stns 16001
#python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20121130_20121130 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20141031_20141031 --state sa --save True --min 10 --stns 16001
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 27_20171218_20171218 --state sa --save True --min 10 --stns 16001
