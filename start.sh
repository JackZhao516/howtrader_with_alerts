#!/bin/bash

while true;
do
    DATE=`date | cut -d' ' -f4`
    DATE1=`date | cut -d' ' -f5`

    if [[ $DATE == "16:45:00" || $DATE1 == "16:45:00" ]]
    then
#        conda activate mytrader
        rm -rf alert_100.log
        nohup python3 alert_system.py alert_100 > alert_100.log 2>&1 &

        echo "start"
        sleep 1s
    fi
done

