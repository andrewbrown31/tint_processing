#!/bin/bash

for y in $(seq 2014 1 2020); do
 for m in $(seq -w 1 1 12); do

 d=$y-$m-01
 e=$(date -d "$d + 1 month")
 e=$(date -d "$e - 1 minute")

 cp /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_generic.sh /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh

 sed -i "s/YYYYMMDDHHMM1/$(date -d "$d" +%Y%m%d%H%M)/g" /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh
 sed -i "s/YYYYMMDDHHMM2/$(date -d "$e" +%Y%m%d%H%M)/g" /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh
 sed -i "s/YYYYMMDD3/$(date -d "$d" +%Y%m%d)/g" /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh
 sed -i "s/YYYYMMDD4/$(date -d "$e" +%Y%m%d)/g" /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh

 qsub /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh
 rm /home/548/ab4502/working/observations/tint_processing/jobs_48/tint_driver_$y$m.sh

 done
done

