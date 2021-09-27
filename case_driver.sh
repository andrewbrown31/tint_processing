#!/bin/bash

#PBS -P eg3 
#PBS -q normal
#PBS -l walltime=06:00:00,mem=64GB 
#PBS -l ncpus=1
#PBS -o /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver.o 
#PBS -e /home/548/ab4502/working/ExtremeWind/jobs/messages/case_driver.e
#PBS -l storage=gdata/eg3+gdata/rq0
 
#Set up conda/shell environments 
source activate radar

#Run tracking
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 8 -t1 200612160000 -t2 200612162359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201003060000 -t2 201003062359 
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 50 -t1 201110070000 -t2 201110072359 --azi_shear False
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201502280000 -t2 201502282359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 71 -t1 201601140000 -t2 201601142359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 201611210000 -t2 201611212359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 202001310000 -t2 202001312359
python /home/548/ab4502/working/observations/tint_processing/tint_driver.py -rid 2 -t1 202008270000 -t2 202008272359

#Post process tracks and combine with AWS gust data
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 8_20061216_20061216 --state qld --save True --min 10 --plot True --plot_scan 200612160801 --plot_stn 40068 --stns 40068
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20100306_20100306 --state vic --save True --min 10 --plot True --plot_scan 201003060331 --plot_stn 86282 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 50_20111007_20111007 --state qld --save True --min 10 --plot True --plot_scan 201110071931 --plot_stn 41359 --stns 41359
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20150228_20150228 --state vic --save True --min 10 --plot True --plot_scan 201502280919 --plot_stn 86282 --stns 86282
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 71_20160114_20160114 --state nsw --save True --min 10 --plot True --plot_scan 201601140413 --plot_stn 66037 --stns 66037
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20161121_20161121 --state vic --save True --min 10 --plot True --plot_scan 201611210601 --plot_stn 87168 --stns 87168
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20200131_20200131 --state vic --save True --min 10 --plot True --plot_scan 202001310342 --plot_stn 90035 --stns 90035
python /home/548/ab4502/working/observations/tint_processing/post_process_tracks.py -fid 2_20200827_20200827 --state vic --save True --min 10 --plot True --plot_scan 202008270712 --plot_stn 87113 --stns 87113
