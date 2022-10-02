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
from crawl_coingecko import get_exchanges, get_coins_with_weekly_volume_increase, get_all_exchanges
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


def alert_100(cta_engine: CtaEngine, main_engine: MainEngine):
    num = 100
    coins = ["USDT", "BTC", "ETH"]
    setting = {}

    for coin in coins:
        exchanges = get_exchanges(num, coin)
        for exchange in exchanges:
            cta_engine.add_strategy("Strategy4h12h", f"100_{exchange}_4h12h", f"{exchange.lower()}.BINANCE", setting)

    cta_engine.init_all_strategies()
    main_engine.write_log(cta_engine.print_strategy())
    sleep(40 * num * 3)  # Leave enough time to complete strategy initialization


def alert_500(cta_engine: CtaEngine, main_engine: MainEngine):
    coins = ["USDT", "BTC", "ETH"]
    setting = {}
    symbols = get_coins_with_weekly_volume_increase()
    exchanges = get_all_exchanges()
    count = 0
    for coin in coins:
        for symbol in symbols:
            if f"{symbol}{coin}" in exchanges:
                cta_engine.add_strategy("Strategy4h1d", f"500_{symbol}{coin}_4h1d", f"{symbol.lower()}{coin.lower()}.BINANCE", setting)
                count += 1

    cta_engine.init_all_strategies()
    main_engine.write_log(cta_engine.print_strategy())
    sleep(40 * count * 3)  # Leave enough time to complete strategy initialization


def run(mode="alert_100"):
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
    sleep(2)

    cta_engine.init_engine()
    main_engine.write_log("set up cta engine")
    send_message("start cta strategy")

    if mode == "alert_100":
        alert_100(cta_engine, main_engine)
    elif mode == "alert_500":
        alert_500(cta_engine, main_engine)

    main_engine.write_log("init cta strategies")

    cta_engine.start_all_strategies()
    main_engine.write_log("start cta strategies")

    while True:
        sleep(10)


if __name__ == "__main__":
    # sys.argv[1] is the mode
    run(sys.argv[1])
