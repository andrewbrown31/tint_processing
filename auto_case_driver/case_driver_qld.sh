#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_qld.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver_qld.e
#PBS -l storage=gdata/eg3+gdata/rq0+scratch/w40
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 66 -t1 201012160000 -t2 201012162359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 66 -t1 201101180000 -t2 201101182359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 66 -t1 201311230000 -t2 201311232359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 66 -t1 201612180000 -t2 201612182359

python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201110070000 -t2 201110072359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201310180000 -t2 201310182359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201401230000 -t2 201401232359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201601290000 -t2 201601292359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201802130000 -t2 201802132359 --azi_shear False

#Post process tracks and combine with AWS gust data
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 66_20101216_20101216 --state qld --save True --min 10 --stns 40004
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 66_20110118_20110118 --state qld --save True --min 10 --stns 40004
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 66_20131123_20131123 --state qld --save True --min 10 --stns 40004
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 66_20161218_20161218 --state qld --save True --min 10 --stns 40004

python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20111007_20111007 --state qld --save True --min 10 --stns 41359
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20131018_20131018 --state qld --save True --min 10 --stns 41359
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20140123_20140123 --state qld --save True --min 10 --stns 41359
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20160129_20160129 --state qld --save True --min 10 --stns 41359
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20180213_20180213 --state qld --save True --min 10 --stns 41359
