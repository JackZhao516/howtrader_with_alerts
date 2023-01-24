import sys
import csv
from time import sleep
from datetime import datetime, time
import threading
import logging

from howtrader.trader.setting import SETTINGS
from howtrader.trader.engine import MainEngine

from howtrader.app.cta_strategy import CtaEngine
from crawl_coingecko import CoinGecKo
from alert_coingecko import CoinGecKo12H, alert_coins, close_all_threads
from telegram_api import TelegramBot
from binance_indicator_alert import BinanceIndicatorAlert

tg_bot = TelegramBot("TEST")
cg = CoinGecKo("CG_SUM")

usdt_gateway_setting = {
        "key": "ZaipNokA3CkFb0fQsp7D2mqmev9RAHPrgW0SnUXVhReXfgTujN7SJB0Wu4atl20M",
        "secret": "xD0eB0n0E47FQj9zKO4FinrjwKuCb7c3on9A9qv72bqM08QszCMYMkiCo7PntTYW",
        "proxy_host": "127.0.0.1",
        "proxy_port": 0,
    }


def alert_indicator(alert_type="alert_100"):
    logging.info(f"{alert_type} start")
    if alert_type == "alert_100":
        exchanges, coin_ids, coin_symbols = cg.get_exchanges(num=100)
    else:
        exchanges, coin_ids, coin_symbols = cg.get_coins_with_weekly_volume_increase()
    logging.warning("start coingecko alert")
    tg_type = "CG_ALERT"
    coins_thread = alert_coins(coin_ids, coin_symbols, alert_type=alert_type, tg_type=tg_type)
    execution_time = 60 * 60 * 24 * 3 + 60 * 35
    logging.warning(f"start binance indicator alert")
    logging.warning(f"exchanges: {len(exchanges)}, coins: {len(coin_ids)}")
    BinanceIndicatorAlert(exchanges, alert_type=alert_type, execution_time=execution_time, tg_type=tg_type)

    close_all_threads(coins_thread)
    logging.warning(f"{alert_type} finished")


def alert_300(cta_engine: CtaEngine, main_engine: MainEngine):
    while True:
        setting = {}
        exchanges = cg.get_exchanges(num=300)
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

        sleep(70 * len(exchanges))  # Leave enough time to complete strategy initialization
        cta_engine.start_all_strategies()
        main_engine.write_log("start cta strategies")
        sleep(10)
        get_300()
        sleep(60 * 20)  # 20 minutes
        cta_engine.close()
        sleep(60 * 60 * 24 * 2)  # 2 days
        main_engine.write_log("re-run alert_300")


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
            cg_300 = CoinGecKo12H(coin_id, SETTINGS["PROD"])
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
    # print(res)
    newly_added = []
    newly_deleted = []
    for exchange in res:
        if exchange not in last_res:
            newly_added.append(exchange)
    for exchange in last_res:
        if exchange not in res:
            newly_deleted.append(exchange)

    l, r = res[:len(res)//2], res[len(res)//2:]
    tg_bot.send_message(f"Top 300 coins/coin exchanges spot over H12 MA200:\n{l}")
    tg_bot.send_message(f"{r}")
    tg_bot.send_message(f"Top 300 coins spot over H12 MA180 but less than 90 days:\n{new_coins}")
    # l, r = newly_added[:len(res) // 2], newly_added[len(res) // 2:]
    tg_bot.send_message(f"Top 300 coins/coin exchanges exchanges spot over H12 MA200 newly added:\n{newly_added}")
    # tg_bot.send_message(f"{r}")
    # l, r = newly_deleted[:len(res) // 2], newly_deleted[len(res) // 2:]
    tg_bot.send_message(f"Top 300 coins/coin exchanges exchanges spot over H12 MA200 newly deleted:\n{newly_deleted}")
    # tg_bot.send_message(f"{r}")

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
        return res


if __name__ == "__main__":
    # sys.argv[1] is the mode
    if sys.argv[1] == "get_300":
        get_300()
    else:
        alert_indicator(sys.argv[1])
