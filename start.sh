#!/bin/bash

while true;
do
    DATE=`date | cut -d' ' -f5`

    if [[ $DATE == "02:05:00" ]]
    then
#        conda activate mytrader
        rm -rf alert_5min.log
#        rm -rf alert_5min_1.log
#        rm -rf alert_5min_2.log

        nohup python3 binance_websocket.py > alert_5min_0.log 2>&1 &
#        nohup python3 binance_websocket.py 1 > alert_5min_1.log 2>&1 &
#        nohup python3 binance_websocket.py 2 > alert_5min_2.log 2>&1 &
        echo "start"
        sleep 1s
    fi
done

