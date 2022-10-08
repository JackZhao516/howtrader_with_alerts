from time import sleep
from telegram_api import send_message
import requests
import numpy as np
from pycoingecko import CoinGeckoAPI
import datetime

TELEGRAM_CHAT_ID = "-804953236" # PROD
# TELEGRAM_CHAT_ID = "-814886566"  # TEST
def get_exchanges(num, exchange="BTC"):
    cg = CoinGeckoAPI()
    exchanges = get_all_exchanges()
    res = []
    n, coin_index, page = 0, 0, 2
    market_list = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=200, page=1,
                                       sparkline=False)
    market_list = [market['symbol'].upper() for market in market_list]
    while n < num:
        if coin_index == 200:
            market_list = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=200, page=page,
                                               sparkline=False)
            market_list = [market['symbol'].upper() for market in market_list]
            page += 1
            coin_index = 0
        if market_list[coin_index] != exchange and f"{market_list[coin_index]}{exchange}" in exchanges:
            res.append(f"{market_list[coin_index]}{exchange}")
            n += 1
        coin_index += 1
    send_message(f"{datetime.datetime.now()}: Top {num} exchanges with {exchange}:\n {res}", chat_id=TELEGRAM_CHAT_ID)
    return res


def get_all_exchanges():
    api_url = f'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(api_url, timeout=10).json()
    exchanges = {exchange['symbol'] for exchange in response['symbols']}
    return exchanges


def get_all_ids():
    cg = CoinGeckoAPI()
    ids = cg.get_coins_list()
    ids = [[id['id'], id['symbol'].upper()] for id in ids]
    return ids


def get_coins_with_weekly_volume_increase(volume_threshold=1.3):
    cg = CoinGeckoAPI()
    ids = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=1,
                               sparkline=False)
    ids += cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=2,
                                sparkline=False)
    ids = [[id['id'], id['symbol'].upper()] for id in ids]
    res = []

    for i, id in enumerate(ids):
        data = cg.get_coin_market_chart_by_id(id=id[0], vs_currency='usd', days=13, interval='daily')
        data = np.array(data['total_volumes'])
        print(i)
        if np.sum(data[:7, 1]) == 0:
            continue
        volume_increase = np.sum(data[7:, 1]) / np.sum(data[:7, 1])

        if volume_increase >= volume_threshold:
            res.append([volume_increase, id[1]])

    res = sorted(res, key=lambda x: x[0], reverse=True)
    coins = []
    with open("coins_with_weekly_volume_increase.txt", "w") as f:
        for coin in res:
            f.write(f"{coin[1]}: {coin[0]}\n")
            coins.append(coin[1])
    send_message(f"{datetime.datetime.now()}: Top 500 coins that has weekly volume increase > 30%:\n {res}", chat_id=TELEGRAM_CHAT_ID)
    return coins

# print(get_exchanges(100, "ETH"))
# print(get_coins_with_weekly_volume_increase())
