import sys
import csv
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


TELEGRAM_CHAT_ID = "-804953236"    # PROD
# TELEGRAM_CHAT_ID = "-814886566"  # TEST

usdt_gateway_setting = {
        "key": "ZaipNokA3CkFb0fQsp7D2mqmev9RAHPrgW0SnUXVhReXfgTujN7SJB0Wu4atl20M",
        "secret": "xD0eB0n0E47FQj9zKO4FinrjwKuCb7c3on9A9qv72bqM08QszCMYMkiCo7PntTYW",
        "proxy_host": "127.0.0.1",
        "proxy_port": 0,
    }


last={"ETH":['BNBETH', 'XRPETH', 'SOLETH', 'MATICETH', 'TRXETH', 'UNIETH', 'WBTCETH', 'ATOMETH', 'LTCETH', 'LINKETH', 'ETCETH', 'XLMETH', 'FTTETH', 'XMRETH', 'ALGOETH', 'VETETH', 'APEETH', 'FILETH', 'EGLDETH', 'DASHETH', 'HOTETH', 'ROSEETH', 'GLMETH', 'IOTXETH', 'ONTETH', 'OPETH', 'VGXETH', 'LSKETH', 'PUNDIXETH', 'SNTETH', 'PEOPLEETH', 'GALETH', 'STEEMETH', 'DENTETH', 'RLCETH', 'STRAXETH', 'FUNETH', 'SSVETH', 'QKCETH', 'STMXETH', 'XVGETH', 'BONDETH', 'MFTETH', 'UNFIETH', 'WANETH', 'BELETH', 'BLZETH', 'LITETH', 'KEYETH', 'WINGETH', 'ADXETH', 'UFTETH', 'DEXEETH', 'PROSETH', 'VIBETH', 'BETHETH']
, "BTC": ['BNBBTC', 'XRPBTC', 'DOGEBTC', 'MATICBTC', 'TRXBTC', 'UNIBTC', 'ATOMBTC', 'LTCBTC', 'LINKBTC', 'XLMBTC', 'XMRBTC', 'ALGOBTC', 'BCHBTC', 'QNTBTC', 'APEBTC', 'EGLDBTC', 'CHZBTC', 'MKRBTC', 'CAKEBTC', 'PAXGBTC', 'NEXOBTC', 'ENSBTC', 'RVNBTC', 'COMPBTC', 'TWTBTC', 'CVXBTC', 'DCRBTC', 'GMXBTC', 'BTGBTC', 'GLMBTC', 'IOTXBTC', 'SUSHIBTC', 'YFIBTC', 'LPTBTC', 'POLYBTC', 'FLUXBTC', 'HIVEBTC', 'INJBTC', 'VGXBTC', 'RENBTC', 'COTIBTC', 'API3BTC', 'SNTBTC', 'SYSBTC', 'PROMBTC', 'PYRBTC', 'STRAXBTC', 'ARDRBTC', 'MBOXBTC', 'STEEMBTC', 'RADBTC', 'CTSIBTC', 'RLCBTC', 'SSVBTC', 'QKCBTC', 'CTKBTC', 'XVSBTC', 'STPTBTC', 'DOCKBTC', 'STMXBTC', 'ANTBTC', 'SANTOSBTC', 'STGBTC', 'FETBTC', 'AERGOBTC', 'DODOBTC', 'DUSKBTC', 'UTKBTC', 'NEBLBTC', 'ALPHABTC', 'AGIXBTC']
, "USDT": ['BNBUSDT', 'XRPUSDT', 'MATICUSDT', 'ATOMUSDT', 'LINKUSDT', 'XLMUSDT', 'ALGOUSDT', 'LUNCUSDT', 'QNTUSDT', 'CHZUSDT', 'MKRUSDT', 'CAKEUSDT', 'NEXOUSDT', 'ENSUSDT', 'RVNUSDT', 'LUNAUSDT', 'COMPUSDT', 'GMXUSDT', 'RSRUSDT', 'SUSHIUSDT', 'POLYUSDT', 'FLUXUSDT', 'INJUSDT', 'VGXUSDT', 'COTIUSDT', 'REEFUSDT', 'PYRUSDT', 'TRIBEUSDT', 'RLCUSDT', 'SANTOSUSDT', 'STGUSDT', 'ERNUSDT', 'ALPACAUSDT', 'SFPUSDT', 'FORTHUSDT', 'ALPINEUSDT', 'LAZIOUSDT', 'VITEUSDT', 'CITYUSDT', 'BARUSDT', 'LEVERUSDT', 'BEAMUSDT']}


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


def alert_300(cta_engine: CtaEngine, main_engine: MainEngine, op="USDT"):
    num = 300
    coins = ["USDT", "BTC"]
    # coins = ["ETH"]
    setting = {}

    for coin in coins:
        exchanges = get_exchanges(num, coin)
        name = "300/" + coin + ".csv"
        with open(name, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(exchanges)
            print("ETH exchanges count: ", len(exchanges))
        for exchange in exchanges:
            cta_engine.add_strategy("Strategy12h", f"300_{exchange}_12h", f"{exchange.lower()}.BINANCE", setting)

        cta_engine.init_all_strategies()
        main_engine.write_log(cta_engine.print_strategy())
        # sleep(40 * num * 3)  # Leave enough time to complete strategy initialization
        sleep(40 * num * 2)  # Leave enough time to complete strategy initialization


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


def get_300():
    # coins = ["USDT", "BTC", "ETH"]
    coins = ["ETH"]
    for coin in coins:
        # last_name = "300/" + coin + "_res.csv"
        # with open(last_name, 'r', encoding='UTF8', newline='') as f:
        #     reader = csv.reader(f)
        #     last_res = next(reader)

        # TODO: remove for next update
        last_res = last[coin]

        name = "300/" + coin + ".csv"
        res = []
        with open(name, 'r', encoding='UTF8', newline='') as f:
            reader = csv.reader(f)
            exchanges = next(reader)
            for exchange in exchanges:
                res = get_300_helper(exchange, res)

        newly_added = []
        newly_deleted = []
        for exchange in res:
            if exchange not in last_res:
                newly_added.append(exchange)
        for exchange in last_res:
            if exchange not in res:
                newly_deleted.append(exchange)

        send_message(f"Top 300 xxx{coin} exchanges spot over H12 MA200:\n{res}", TELEGRAM_CHAT_ID)
        send_message(f"Top 300 xxx{coin} exchanges spot over H12 MA200 newly added:\n{newly_added}", TELEGRAM_CHAT_ID)
        send_message(f"Top 300 xxx{coin} exchanges spot over H12 MA200 newly deleted:\n{newly_deleted}", TELEGRAM_CHAT_ID)

        with open("300/" + coin + "_res.csv", 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(res)


def get_300_helper(exchange, res):
    try:
        with open("300/" + exchange + ".csv", 'r', encoding='UTF8', newline='') as f_tmp:
            reader_tmp = csv.reader(f_tmp)
            data = next(reader_tmp)
            if data[0] == "1":
                res.append(exchange)
        return res
    except:
        return None

def run(mode="alert_100", option=None):
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
    elif mode == "alert_300":
        alert_300(cta_engine, main_engine, option)

    main_engine.write_log("init cta strategies")

    cta_engine.start_all_strategies()
    main_engine.write_log("start cta strategies")

    while True:
        sleep(10)


if __name__ == "__main__":
    # sys.argv[1] is the mode
    if sys.argv[1] == "get_300":
        get_300()
    elif sys.argv[1] == "alert_300":
        run(sys.argv[1], sys.argv[2])
    else:
        run(sys.argv[1])
