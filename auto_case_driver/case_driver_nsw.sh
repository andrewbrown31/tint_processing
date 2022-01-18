#!/bin/bash

#PBS -P eg3 
#PBS -q express
#PBS -l walltime=01:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_nsw.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_nsw.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201008020000 -t2 201008022359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201208100000 -t2 201208102359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201302230000 -t2 201302232359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201410140000 -t2 201410142359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201503010000 -t2 201503012359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201512160000 -t2 201512162359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201601140000 -t2 201601142359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201606040000 -t2 201606042359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201704090000 -t2 201704092359

#Post process tracks and combine with AWS gust data
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20100802_20100802 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20120810_20120810 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20130223_20130223 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20141014_20141014 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20150301_20150301 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20151216_20151216 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20160114_20160114 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20160604_20160604 --state nsw --save True --min 10 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20170409_20170409 --state nsw --save True --min 10 --stns 66037
