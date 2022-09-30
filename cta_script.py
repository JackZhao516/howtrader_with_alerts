import sys
from time import sleep
from datetime import datetime, time
from logging import INFO

from howtrader.event import EventEngine
from howtrader.trader.setting import SETTINGS
from howtrader.trader.engine import MainEngine, LogEngine

from howtrader.gateway.binance import BinanceSpotGateway, BinanceUsdtGateway
from howtrader.app.cta_strategy import CtaStrategyApp, CtaEngine
from howtrader.app.cta_strategy.base import EVENT_CTA_LOG
# from strategy_4h1h import Strategy4h1h
from crawl_coingecko import get_coins, get_all_exchanges
from telegram_api import send_message

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True


usdt_gateway_setting = {
        "key": "ZaipNokA3CkFb0fQsp7D2mqmev9RAHPrgW0SnUXVhReXfgTujN7SJB0Wu4atl20M",
        "secret": "xD0eB0n0E47FQj9zKO4FinrjwKuCb7c3on9A9qv72bqM08QszCMYMkiCo7PntTYW",
        "proxy_host": "127.0.0.1",
        "proxy_port": 0,
    }

def run():
    """
    Running in the child process.
    """
    SETTINGS["log.file"] = True

    event_engine = EventEngine()
    main_engine: MainEngine = MainEngine(event_engine)
    main_engine.add_gateway(BinanceSpotGateway)
    cta_engine: CtaEngine = main_engine.add_app(CtaStrategyApp)
    main_engine.write_log("setup main engine")

    log_engine: LogEngine = main_engine.get_engine("log")
    event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
    main_engine.write_log("register event listener")

    main_engine.connect(usdt_gateway_setting, "BINANCE_SPOT")
    main_engine.write_log("connect binance spot gate way")
    exchanges = get_all_exchanges()
    sleep(2)

    cta_engine.init_engine()
    main_engine.write_log("set up cta engine")

    send_message("start cta strategy")
    num = 100
    count_usdt, count_eth = 0, 0
    for symbol in get_coins(200):
        setting = {}
        if count_usdt < num and f"{symbol}USDT" in exchanges:
            if symbol != "USDT":
                cta_engine.add_strategy("Strategy4h12h", f"{symbol}USDT_4h12h", f"{symbol.lower()}usdt.BINANCE", setting)
                count_usdt += 1
        if count_eth < num and f"{symbol}ETH" in exchanges:
            if symbol != "ETH":
                cta_engine.add_strategy("Strategy4h12h", f"{symbol}ETH_4h12h", f"{symbol.lower()}eth.BINANCE", setting)
                count_eth += 1
        if count_usdt >= num and count_eth >= num:
            break

    cta_engine.init_all_strategies()
    main_engine.write_log(cta_engine.print_strategy())
    sleep(8000)   # Leave enough time to complete strategy initialization
    main_engine.write_log("init cta strategies")

    cta_engine.start_all_strategies()
    main_engine.write_log("start cta strategies")

    while True:
        sleep(10)

if __name__ == "__main__":
    run()
