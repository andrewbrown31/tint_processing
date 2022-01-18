#!/bin/bash

#PBS -P eg3 
#PBS -q express
#PBS -l walltime=01:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_vic.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_vic.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 200609240000 -t2 200609242359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 200911200000 -t2 200911202359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201003060000 -t2 201003062359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201006170000 -t2 201006172359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201111180000 -t2 201111182359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201112250000 -t2 201112252359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201202260000 -t2 201202262359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201303210000 -t2 201303212359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201502280000 -t2 201502282359

#Post process tracks and combine with AWS gust data
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20060924_20060924 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20091120_20091120 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20100306_20100306 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20100617_20100617 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20111118_20111118 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20111225_20111225 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20120226_20120226 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20130321_20130321 --state vic --save True --min 10 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20150228_20150228 --state vic --save True --min 10 --stns 86282
