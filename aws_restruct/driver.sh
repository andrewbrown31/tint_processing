#!/bin/bash

for i in $(seq 2021 1 2021); do
 
 cp /home/548/ab4502/working/observations/tint_processing/aws_restruct/generic.sh /home/548/ab4502/working/observations/tint_processing/aws_restruct/jobs/${i}.sh

 sed -i "s/YYYY/$i/g" /home/548/ab4502/working/observations/tint_processing/aws_restruct/jobs/${i}.sh
 qsub /home/548/ab4502/working/observations/tint_processing/aws_restruct/jobs/${i}.sh

 done


