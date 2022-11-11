from time import sleep
import numpy as np
import threading
from crawl_coingecko import CoinGecKo
from telegram_api import TelegramBot
from howtrader.trader.setting import SETTINGS


class CoinGecKo12H(CoinGecKo):
    def __init__(self, coin_id, prod=True):
        super().__init__(prod=prod)
        self.coin_id = coin_id
        self.less_90_days = False
        self.ma_180 = self.h12_sma_180()

    def h12_sma_180(self):
        try:
            price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=90)
            price = price['prices']
            if len(price) < 2150:
                self.less_90_days = True
            price = [i[1] for i in price]
            res = 0
            counter = 0
            for i in range(0, len(price), 12):
                res += price[i]
                counter += 1
            return res / counter
        except Exception as e:
            return 1000000

    def alert_spot(self):
        try:
            price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=1)
            price = price['prices'][-1][1]
            # price = Decimal(price)
            print(f"coin_id: {self.coin_id}, price: {price}, ma_180: {self.ma_180}, {price > self.ma_180}, new_coin: {self.less_90_days}")
            return price > self.ma_180
        except Exception as e:
            return False


class CoinGecKoAlert(CoinGecKo):
    def __init__(self, coin_id, symbol, prod=True):
        super().__init__(prod=prod)
        self.coin_id = coin_id
        self.symbol = symbol
        self.less_90_days = False
        self.less_34_days = False
        self.less_17_days = False

        self.tg_bot = TelegramBot(prod, alert=True)

        self.counter_12h = 0
        self.list_12h = None
        self.ma_12h = None
        self.spot_over_ma_12h = None

        self.counter_4h = 0
        self.list_4h = None
        self.ma_4h = None
        self.spot_over_ma_4h = None

        self.counter_4h_500 = 0
        self.list_4h_500 = None
        self.ma_4h_500 = None
        self.spot_over_ma_4h_500 = None

        self.counter_1d = 0
        self.list_1d = None
        self.ma_1d = None
        self.spot_over_ma_1d = None

    def h12_init(self):
        # try:
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=90)
        price = price['prices']
        if len(price) < 2150:
            self.less_90_days = True
        # price = [i[1] for i in price]
        self.list_12h = np.zeros(180, dtype=np.float64)
        price.reverse()
        counter = 0
        for i in range(0, len(price), 12):
            self.list_12h[counter] = price[i][1]
            counter += 1
            # self.current_time_12h = price[i][0]
        # self.current_time = price[-1][0]
        self.counter_12h = len(price) // 12
        self.ma_12h = np.sum(self.list_12h)/self.counter_12h
        self.spot_over_ma_12h = price[0][1] > self.ma_12h
        # print(f"h12 init: {self.coin_id}, ma_12h: {self.ma_12h}, spot_over_ma_12h: {self.spot_over_ma_12h}")
        # except Exception as e:
        #     sleep(60)
        #     self.h12_init()

    def h4_init(self):
        # try:
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=34)
        price = price['prices']
        if len(price) < 790:
            self.less_34_days = True

        self.list_4h = np.zeros(200, dtype=np.float64)
        price.reverse()
        counter = 0
        for i in range(0, min(len(price), 800), 4):
            self.list_4h[counter] = price[i][1]
            counter += 1

        self.counter_4h = min(len(price), 800) // 4
        self.ma_4h = np.sum(self.list_4h)/self.counter_4h
        self.spot_over_ma_4h = price[0][1] > self.ma_4h
        # print(f"h4 init: {self.coin_id}, ma_4h: {self.ma_4h}, spot_over_ma_4h: {self.spot_over_ma_4h}")
        # except Exception as e:
        #     print("h4 init error")
        #     sleep(60)
        #     self.h4_init()

    def h4_500_init(self):
        # try:
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=17)
        price = price['prices']
        if len(price) < 395:
            self.less_17_days = True

        self.list_4h_500 = np.zeros(100, dtype=np.float64)
        price.reverse()
        counter = 0
        for i in range(0, min(len(price), 400), 4):
            self.list_4h_500[counter] = price[i][1]
            counter += 1

        self.counter_4h_500 = min(len(price), 400) // 4
        self.ma_4h_500 = np.sum(self.list_4h_500)/self.counter_4h_500
        self.spot_over_ma_4h_500 = price[0][1] > self.ma_4h_500
        # print(f"h4 init: {self.coin_id}, ma_4h: {self.ma_4h_500}, spot_over_ma_4h: {self.spot_over_ma_4h_500}")
        # except Exception as e:
        #     print("h4 init error")
        #     sleep(60)
        #     self.h4_init()

    def d1_init(self):
        # try:
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=90)
        price = price['prices']
        if len(price) < 2150:
            self.less_90_days = True

        self.list_1d = np.zeros(90, dtype=np.float64)
        price.reverse()
        counter = 0
        for i in range(0, len(price), 24):
            self.list_1d[counter] = price[i][1]
            counter += 1

        self.counter_1d = len(price) // 24
        self.ma_1d = np.sum(self.list_1d)/self.counter_1d
        self.spot_over_ma_1d = price[0][1] > self.ma_1d
        # print(f"d1 init: {self.coin_id}, ma_1d: {self.ma_1d}, spot_over_ma_1d: {self.spot_over_ma_1d}")
        # except Exception as e:
        #     print("h4 init error")
        #     sleep(60)
        #     self.h4_init()

    def minute_update(self, update_ma_12=False, update_ma_4=False):
        price = self.cg.get_price(ids=self.coin_id, vs_currencies='usd', include_last_updated_at=True,
                                  precision="full")
        price = np.float64(price[self.coin_id]["usd"])
        if update_ma_12:
            self.list_12h = np.roll(self.list_12h, 1)
            self.list_12h[0] = price
            if self.counter_12h < 180:
                self.counter_12h += 1
            self.ma_12h = np.sum(self.list_12h)/self.counter_12h

        if update_ma_4:
            self.list_4h = np.roll(self.list_4h, 1)
            self.list_4h[0] = price
            if self.counter_4h < 200:
                self.counter_4h += 1
            self.ma_4h = np.sum(self.list_4h) / self.counter_4h
            # print(price, self.list_4h, self.counter_4h, self.ma_4h, np.sum(self.list_4h))

        if self.spot_over_ma_12h and price < self.ma_12h:
            self.tg_bot.safe_send_message(
                 f"100_{self.symbol} spot: {str(price)} crossunder H12 ma180: {str(self.ma_12h)}")
            self.spot_over_ma_12h = False
        elif not self.spot_over_ma_12h and price > self.ma_12h:
            self.tg_bot.safe_send_message(
                 f"100_{self.symbol} spot: {str(price)} crossover H12 ma180: {str(self.ma_12h)}")
            self.spot_over_ma_12h = True

        if self.spot_over_ma_4h and price < self.ma_4h:
            self.tg_bot.safe_send_message(
                f"100_{self.symbol} spot: {str(price)} crossunder H4 ma200: {str(self.ma_4h)}")
            self.spot_over_ma_4h = False
        elif not self.spot_over_ma_4h and price > self.ma_4h:
            self.tg_bot.safe_send_message(
                f"100_{self.symbol} spot: {str(price)} crossover H4 ma200: {str(self.ma_4h)}")
            self.spot_over_ma_4h = True

        # print(f"{self.symbol} spot: {str(price)} H12 ma180: {str(self.ma_12h)} H4 ma200: {str(self.ma_4h)}")
        # print(f"{self.coin_id} spot: {str(price)} H4 ma200: {str(self.ma_4h)}")

    def minute_update_500(self, update_ma_1d=False, update_ma_4=False):
        price = self.cg.get_price(ids=self.coin_id, vs_currencies='usd', include_last_updated_at=True,
                                  precision="full")
        price = np.float64(price[self.coin_id]["usd"])
        if update_ma_1d:
            self.list_1d = np.roll(self.list_1d, 1)
            self.list_1d[0] = price
            if self.counter_1d < 90:
                self.counter_1d += 1
            self.ma_1d = np.sum(self.list_1d)/self.counter_1d

        if update_ma_4:
            self.list_4h_500 = np.roll(self.list_4h_500, 1)
            self.list_4h_500[0] = price
            if self.counter_4h_500 < 100:
                self.counter_4h_500 += 1
            self.ma_4h_500 = np.sum(self.list_4h_500) / self.counter_4h_500
            # print(price, self.list_4h, self.counter_4h, self.ma_4h, np.sum(self.list_4h))

        if self.spot_over_ma_1d and price < self.ma_1d:
            self.tg_bot.safe_send_message(
                 f"500_{self.symbol} spot: {str(price)} crossunder D1 ma90: {str(self.ma_1d)}")
            self.spot_over_ma_1d = False
        elif not self.spot_over_ma_1d and price > self.ma_1d:
            self.tg_bot.safe_send_message(
                 f"500_{self.symbol} spot: {str(price)} crossover D1 ma90: {str(self.ma_1d)}")
            self.spot_over_ma_1d = True

        if self.spot_over_ma_4h_500 and price < self.ma_4h_500:
            self.tg_bot.safe_send_message(
                f"500_{self.symbol} spot: {str(price)} crossunder H4 ma100: {str(self.ma_4h_500)}")
            self.spot_over_ma_4h_500 = False
        elif not self.spot_over_ma_4h_500 and price > self.ma_4h_500:
            self.tg_bot.safe_send_message(
                f"500_{self.symbol} spot: {str(price)} crossover H4 ma100: {str(self.ma_4h_500)}")
            self.spot_over_ma_4h_500 = True
        # print(f"{self.symbol} spot: {str(price)} D1: {str(self.ma_1d)} H4 ma100: {str(self.ma_4h_500)}")

    def alert_spot(self, alert_100=True):
        # try:
        if alert_100:
            self.h12_init()
            self.h4_init()
        else:
            self.d1_init()
            self.h4_500_init()
        last_update = None
        minute_counter_12h = 1
        minute_counter_4h = 1
        minute_counter_1d = 1
        while SETTINGS["100"]:
            if last_update:
                last_update.join()
            last_update = threading.Thread(target=self.minute_update,
                                           args=(minute_counter_12h % 720 == 0,
                                                 minute_counter_4h % 240 == 0)) if alert_100 \
                else threading.Thread(target=self.minute_update_500,
                                           args=(minute_counter_1d % 1440 == 0,
                                                 minute_counter_4h % 240 == 0))
            last_update.start()
            minute_counter_12h %= 720
            minute_counter_12h += 1
            minute_counter_4h %= 240
            minute_counter_4h += 1
            minute_counter_1d %= 1440
            minute_counter_1d += 1
            sleep(60)
        # except Exception as e:
        #     pass


def alert_100_function(coin_id, symbol, prod=True):
    cg100 = CoinGecKoAlert(coin_id, symbol, prod)
    cg100.alert_spot(True)


def alert_500_function(coin_id, symbol, prod=True):
    cg500 = CoinGecKoAlert(coin_id, symbol, prod)
    cg500.alert_spot(False)


def alert_coins(coin_ids, coin_symbols, alert_100=True):
    threads = []
    for i in range(len(coin_ids)):
        coin_id, coin_symbol = coin_ids[i], coin_symbols[i]
        t = threading.Thread(target=alert_100_function if alert_100 else alert_500_function,
                             args=(coin_id, coin_symbol, SETTINGS["PROD"]))
        t.start()
        threads.append(t)
        sleep(1)
    return threads


def close_all_threads(threads):
    count = 0
    SETTINGS["100"] = False
    for t in threads:
        t.join()
        count += 1
    SETTINGS["100"] = True
    return count

if __name__ == '__main__':
    t = threading.Thread(target=alert_100_function, args=("bitcoin", "BTC", True))
    t.start()
    sleep(200)
    SETTINGS["100"] = False
    t.join()
    print("done")
    # from pycoingecko import CoinGeckoAPI
    # cg = CoinGeckoAPI(api_key="CG-wAukVxNxrR322gkZYEgZWtV1")
    # price = cg.get_price(ids="bitcoin", vs_currencies='usd', include_last_updated_at=True,
    #                      precision="full")
    # price = np.float64(price["bitcoin"]["usd"])
    # print(price)
