#!/bin/bash

for i in $(seq 2000 1 2020); do
 
 cp /home/548/ab4502/working/observations/aws_restruct/generic.sh /home/548/ab4502/working/observations/aws_restruct/jobs/${i}.sh

 sed -i "s/YYYY/$i/g" /home/548/ab4502/working/observations/aws_restruct/jobs/${i}.sh
 qsub /home/548/ab4502/working/observations/aws_restruct/jobs/${i}.sh

 done


