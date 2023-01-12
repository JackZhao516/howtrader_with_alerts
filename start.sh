#!/bin/bash

while true;
do
    DATE=`date | cut -d' ' -f4`
    DATE1=`date | cut -d' ' -f5`

    if [[ $DATE == "02:39:00" || $DATE1 == "02:39:00" ]]
    then
#        conda activate mytrader
        rm -rf alert_5min.log
        nohup python3 binance_websocket.py > alert_5min.log 2>&1 &

        echo "start"
        sleep 1s
    fi
done

