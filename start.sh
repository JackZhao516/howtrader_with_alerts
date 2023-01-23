#!/bin/bash

while true;
do
    DATE=`date | cut -d' ' -f4`
    DATE1=`date | cut -d' ' -f5`

    if [[ $DATE == "01:30:00" || $DATE1 == "01:30:00" ]]
    then
#        conda activate mytrader
        rm -rf "$1.log"
        nohup python3 alert_system.py "$1" > "$1.log" 2>&1 &

        echo "start"
        sleep 1s
    fi
done

