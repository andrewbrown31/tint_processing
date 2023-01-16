#!/bin/bash

for y in $(seq 2006 1 2020); do

   cp /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data_jobs/66/merge_data_generic.sh /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data_jobs/66/merge_data_$y.sh
   sed -i "s/YYYY/$y/g" /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data_jobs/66/merge_data_$y.sh

   qsub /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data_jobs/66/merge_data_$y.sh
   rm /home/548/ab4502/working/observations/tint_processing/systematic_analysis/merge_data_jobs/66/merge_data_$y.sh

done
