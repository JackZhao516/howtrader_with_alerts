rm -rf alert_100.log
rm -rf alert_300_ETH.log
rm -rf alert_300_BTC.log
rm -rf alert_300_USDT.log
rm -rf alert_500.log

nohup python3 alert_system.py alert_100 > alert_100.log 2>&1 &
nohup python3 alert_system.py alert_300 ETH> alert_300_ETH.log 2>&1 &
nohup python3 alert_system.py alert_300 BTC> alert_300_BTC.log 2>&1 &
nohup python3 alert_system.py alert_300 USDT> alert_300_USDT.log 2>&1 &
nohup python3 alert_system.py alert_500 > alert_500.log 2>&1 &
