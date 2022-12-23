from time import sleep
from telegram_api import TelegramBot
import requests
import numpy as np
from pycoingecko import CoinGeckoAPI
import datetime


class CoinGecKo:
    COINGECKO_API_KEY = "CG-wAukVxNxrR322gkZYEgZWtV1"

    def __init__(self, prod=True):
        self.cg = CoinGeckoAPI(api_key=self.COINGECKO_API_KEY)
        self.tg_bot = TelegramBot(prod=prod, alert=False)

    def get_exchanges(self, num=300):
        exchanges = self.get_all_exchanges()
        res = []
        coingeco_coins = []
        coingeco_names = []

        if num == 300:
            market_list = self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=150, page=1,
                                                    sparkline=False)
            market_list += self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=150, page=2,
                                                     sparkline=False)
        else:
            market_list = self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=100, page=1,
                                                    sparkline=False)

        # ids = [market['id'].upper() for market in market_list]
        markets = [(market['symbol'].upper(), market['id']) for market in market_list]
        market_list = []
        market_set = set()
        for index, i in enumerate(markets):
            if i not in market_set:
                market_list.append(i)
                market_set.add(i)

        for i, coin in enumerate(market_list):
            symbol, coin_id = coin
            if f"{symbol}USDT" not in exchanges and f"{symbol}BTC" not in exchanges and f"{symbol}ETH" not in exchanges:
                coingeco_coins.append(coin_id)
                coingeco_names.append(symbol)
            else:
                if f"{symbol}USDT" in exchanges:
                    res.append(f"{symbol}USDT")
                if f"{symbol}BTC" in exchanges:
                    res.append(f"{symbol}BTC")
                if f"{symbol}ETH" in exchanges:
                    res.append(f"{symbol}ETH")

        # self.tg_bot.send_message(f"{datetime.datetime.now()}: Top 300 coins:\n {market_list}")
        self.tg_bot.send_message(f"{datetime.datetime.now()}: Top {num} coins that are not on Binance:\n {coingeco_names}")
        l, r = res[:len(res)//2], res[len(res)//2:]
        self.tg_bot.send_message(f"{datetime.datetime.now()}: Top {num} coin exchanges that are on Binance:\n {l}")
        self.tg_bot.send_message(f"{r}")

        return res, coingeco_coins, coingeco_names

    def get_all_exchanges(self):
        api_url = f'https://api.binance.com/api/v3/exchangeInfo'
        response = requests.get(api_url, timeout=10).json()
        exchanges = {exchange['symbol'] for exchange in response['symbols']}
        return exchanges

    def get_500_usdt_exchanges(self, market_cap=True):
        exchanges = self.get_all_exchanges()
        res = []
        if market_cap:
            ids = self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=1,
                                            sparkline=False)
            ids += self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=2,
                                             sparkline=False)
            ids = [id['symbol'].upper() for id in ids]
            for i, symbol in enumerate(ids):
                if f"{symbol}USDT" in exchanges:
                    res.append(f"{symbol}USDT")
        else:
            for i in exchanges:
                if i[-4:] == "USDT" or i[-4:] == "BUSD" or i[-3:] == "BTC":
                    res.append(i)
        return res

    def get_all_ids(self):
        ids = self.cg.get_coins_list()
        ids = [[id['id'], id['symbol'].upper()] for id in ids]
        return ids

    def get_coins_with_weekly_volume_increase(self, volume_threshold=1.3, usdt_only=False):
        ids = self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=1,
                                   sparkline=False)
        ids += self.cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=250, page=2,
                                    sparkline=False)
        ids = [[id['id'], id['symbol'].upper()] for id in ids]
        res = []

        for i, id in enumerate(ids):
            data = self.cg.get_coin_market_chart_by_id(id=id[0], vs_currency='usd', days=13, interval='daily')
            data = np.array(data['total_volumes'])
            if np.sum(data[:7, 1]) == 0:
                continue
            volume_increase = np.sum(data[7:, 1]) / np.sum(data[:7, 1])

            if volume_increase >= volume_threshold:
                res.append([volume_increase, id[1], id[0]])

        res = sorted(res, key=lambda x: x[0], reverse=True)
        exchanges = self.get_all_exchanges()
        coingeco_coins, coingeco_names, ex = [], [], []

        for volume_increase, symbol, coin_id in res:
            if f"{symbol}USDT" not in exchanges and f"{symbol}BTC" not in exchanges and f"{symbol}ETH" not in exchanges:
                coingeco_coins.append(coin_id)
                coingeco_names.append(symbol)
            else:
                if f"{symbol}USDT" in exchanges:
                    ex.append(f"{symbol}USDT")
                if not usdt_only:
                    if f"{symbol}BTC" in exchanges:
                        ex.append(f"{symbol}BTC")
                    if f"{symbol}ETH" in exchanges:
                        ex.append(f"{symbol}ETH")
        res = np.array(res)
        l, m1, m2, m3, m4, r = res[:len(res) // 6, :2], res[len(res) // 6: len(res) // 3, :2], res[len(res) // 3: len(res) // 2, :2], \
                               res[len(res) // 2: 2 * len(res) // 3, :2], res[2 * len(res) // 3: 5 * len(res) // 6, :2], \
                               res[5 * len(res) // 6:, :2]
        self.tg_bot.send_message(f"{datetime.datetime.now()}: Top 500 coins that has weekly volume increase > 30%:\n {l}")
        self.tg_bot.send_message(f"{m1}")
        self.tg_bot.send_message(f"{m2}")
        self.tg_bot.send_message(f"{m3}")
        self.tg_bot.send_message(f"{m4}")
        self.tg_bot.send_message(f"{r}")
        return ex, coingeco_coins, coingeco_names


if __name__ == '__main__':
    coin = CoinGecKo(prod=False)
    print(coin.get_all_exchanges())
