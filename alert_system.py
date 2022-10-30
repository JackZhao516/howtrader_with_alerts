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
from crawl_coingecko import CoinGecKo
from alert_coingecko import CoinGecKo12H
from telegram_api import TelegramBot

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

PROD = False
tg_bot = TelegramBot(PROD, alert=False)
cg = CoinGecKo(PROD)

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
    main_engine.write_log("init cta strategies")
    while True:
        num = 10
        coins = ["USDT", "BTC", "ETH"]
        # coins = ["USDT"]
        setting = {}

        for coin in coins:
            exchanges = cg.get_exchanges(num, coin)
            for exchange in exchanges:
                cta_engine.add_strategy("Strategy4h12h", f"100_{exchange}_4h12h", f"{exchange.lower()}.BINANCE", setting)

        cta_engine.init_all_strategies()
        main_engine.write_log(cta_engine.print_strategy())
        sleep(50 * num * len(coins))  # Leave enough time to complete strategy initialization

        cta_engine.start_all_strategies()
        main_engine.write_log("start cta strategies")
        sleep(300)  # 3 days
        cta_engine.close()
        main_engine.write_log("re-run alert_300")


def alert_300(cta_engine: CtaEngine, main_engine: MainEngine):
    while True:
        setting = {}
        exchanges = cg.get_exchanges_300()
        exchanges, coin_ids, coins_symbols = exchanges
        coins_csv_write = [[coin_ids[i], coins_symbols[i]] for i in range(len(coin_ids))]
        name = "300/300_exchanges.csv"
        with open(name, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(exchanges)
        name = "300/300_coins.csv"
        with open(name, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(coins_csv_write)

        print(f"coins len: {len(coin_ids)}, exchanges len: {len(exchanges)}")
        for exchange in exchanges:
            cta_engine.add_strategy("Strategy12h", f"300_{exchange}_12h", f"{exchange.lower()}.BINANCE", setting)

        cta_engine.init_all_strategies()
        main_engine.write_log(cta_engine.print_strategy())
        # sleep(40 * num * 3)  # Leave enough time to complete strategy initialization
        sleep(50 * len(exchanges))  # Leave enough time to complete strategy initialization
        cta_engine.start_all_strategies()
        main_engine.write_log("start cta strategies")
        sleep(10)
        get_300()
        sleep(300)
        cta_engine.close()
        # sleep(60 * 60 * 24 * 3)  # 3 days
        sleep(300)
        main_engine.write_log("re-run alert_300")


def alert_500(cta_engine: CtaEngine, main_engine: MainEngine):
    while True:
        coins = ["USDT", "BTC", "ETH"]
        setting = {}
        symbols = cg.get_coins_with_weekly_volume_increase()
        exchanges = cg.get_all_exchanges()
        # TODO： fot test
        symbols = symbols[:10]
        count = 0
        for coin in coins:
            for symbol in symbols:
                if f"{symbol}{coin}" in exchanges:
                    cta_engine.add_strategy("Strategy4h1d", f"500_{symbol}{coin}_4h1d", f"{symbol.lower()}{coin.lower()}.BINANCE", setting)
                    count += 1

        cta_engine.init_all_strategies()
        main_engine.write_log(cta_engine.print_strategy())
        sleep(50 * count * 3)  # Leave enough time to complete strategy initialization
        cta_engine.start_all_strategies()
        main_engine.write_log("start cta strategies")
        sleep(300)  # 3 days
        cta_engine.close()
        main_engine.write_log("re-run alert_500")


def get_300():
    last_name = "300/300_res.csv"
    with open(last_name, 'r', encoding='UTF8', newline='') as f:
        reader = csv.reader(f)
        last_res = next(reader)

    # TODO: remove for next update
    # last_res = []
    res = []
    new_coins = []
    name = "300/300_coins.csv"
    with open(name, 'r', encoding='UTF8', newline='') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            coin_id, coin_symbol = row
            cg_300 = CoinGecKo12H(coin_id, PROD)
            if cg_300.alert_spot():
                res.append(coin_symbol)
                if cg_300.less_90_days:
                    new_coins.append(coin_symbol)
            print(f"res: {len(res)}")
    name = "300/300_exchanges.csv"
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

    tg_bot.send_message(f"Top 300 coins/coin exchanges spot over H12 MA200:\n{res}")
    tg_bot.send_message(f"Top 300 coins spot over H12 MA180 but less than 90 days:\n{new_coins}")
    tg_bot.send_message(f"Top 300 coins/coin exchanges exchanges spot over H12 MA200 newly added:\n{newly_added}")
    tg_bot.send_message(f"Top 300 coins/coin exchanges exchanges spot over H12 MA200 newly deleted:\n{newly_deleted}")

    with open("300/300_res.csv", 'w', encoding='UTF8', newline='') as f:
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
    tg_bot.send_message(f"start {mode}")

    if mode == "alert_100":
        alert_100(cta_engine, main_engine)
    elif mode == "alert_500":
        alert_500(cta_engine, main_engine)
    elif mode == "alert_300":
        alert_300(cta_engine, main_engine)

    sleep(10)

    # if mode == "alert_100":
    #     sleep(10)
    #     main_engine.write_log("engine close")
    #     cta_engine.close()
    #     main_engine.close()
    #     run("alert_100")
    # elif mode == "alert_500":
    #     sleep(60 * 60 * 24 * 5)
    #     main_engine.write_log("engine close")
    #     cta_engine.stop_all_strategies()
    #     main_engine.close()
    #     run("alert_500")
    # elif mode == "alert_300":
    #     get_300()


if __name__ == "__main__":
    # sys.argv[1] is the mode
    if sys.argv[1] == "get_300":
        get_300()
    else:
        run(sys.argv[1])
