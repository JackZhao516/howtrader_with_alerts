rm -rf alert_100.log
rm -rf alert_300.log
rm -rf alert_500.log

nohup python3 alert_system.py alert_100 > alert_100.log 2>&1 &
nohup python3 alert_system.py alert_300 > alert_300.log 2>&1 &
nohup python3 alert_system.py alert_500 > alert_500.log 2>&1 &
