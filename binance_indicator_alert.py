import os
import requests
import zipfile
import datetime
import glob
import csv
import logging
import numpy as np
from time import sleep
from telegram_api import TelegramBot
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client

class BinanceIndicatorAlert:
    """
    first download, then run a websocket
    """
    DATA_DOWNLOAD_ROOT_URL = "https://data.binance.vision/data/spot/daily/klines/"
    HTTP_URL = "https://api.binance.com/api/v3/klines?"
    MAX_ERROR = 5
    config_logging(logging, logging.INFO)

    def __init__(self, symbol, id_count, mode="100"):
        self.symbol = symbol.upper()
        self.mode = mode
        self.window = 200
        self.id_count = id_count

        self.close = {
            "4": None,
            "12": None,
            "24": None,
        }

        if mode == "100":
            self.close["4"] = np.zeros(200)
            self.close["12"] = np.zeros(200)

        self.last_close_1m = None

        # TODO for testing
        # self.tg_bot = TelegramBot("CG_ALERT")
        self.tg_bot = TelegramBot("TEST")

    def download_past_klines(self, time_frame):
        """
        Download and store all the kline data until last hour
        """
        days_delta = time_frame * self.window // 24 + 1
        start_time = datetime.datetime.now() - datetime.timedelta(days=days_delta)
        time_frame_str = f"{time_frame}h" if int(time_frame) < 24 else "1d"
        i = 0
        error = 0
        csv_dir = os.path.join(os.getcwd(), "klines_csv")
        cur_timestamp = None

        try:
            os.mkdir(csv_dir)
        except FileExistsError:
            pass

        while days_delta > 0:
            days_delta -= 1
            start_time_str = start_time.strftime("%Y-%m-%d")
            url = f"{self.DATA_DOWNLOAD_ROOT_URL}{self.symbol}/{time_frame_str}/" \
                  f"{self.symbol}-{time_frame_str}-{start_time_str}.zip"

            try:
                # download single day csv file
                response = requests.get(url)
                open("1.zip", "wb").write(response.content)
                with zipfile.ZipFile("1.zip", "r") as zip_ref:
                    zip_ref.extractall(csv_dir)

                files = glob.glob(f"{csv_dir}/*.csv")
                if len(files) != 1:
                    raise Exception("No csv file found")

                # process csv file and store kline information
                with open(files[0], "r") as f:
                    rows = [row for row in csv.reader(f)]
                    for row in rows:
                        start_timestamp, close_timestamp, close = int(row[0]), int(row[6]), float(row[4])
                        if cur_timestamp is None or start_timestamp == cur_timestamp + 1:
                            cur_timestamp = close_timestamp
                            i = self.update_close(time_frame, i, close)
                        else:
                            # missing data
                            while cur_timestamp + 1 < start_timestamp:
                                i = self.update_close(time_frame, i, copy=True)
                                cur_timestamp += time_frame * 3600 * 1000
                            cur_timestamp = close_timestamp
                            i = self.update_close(time_frame, i, close)

            except Exception as e:
                if error > self.MAX_ERROR:
                    return
                error += 1
                for count in range(24 // time_frame):
                    i = self.update_close(time_frame, i, copy=True)

        # using http request to download the latest day
        cur_timestamp += 1
        http_url = f"{self.HTTP_URL}symbol={self.symbol}&interval={time_frame_str}" \
                   f"&startTime={cur_timestamp}&limit=1000"
        latest = requests.get(http_url).json()
        if len(latest) == 0:
            return
        latest = latest[:-1]

        for candle in latest:
            start_timestamp, close_timestamp, close = int(candle[0]), int(candle[6]), float(candle[4])
            if cur_timestamp == start_timestamp:
                cur_timestamp = close_timestamp + 1
                i = self.update_close(time_frame, i, close)
            else:
                # missing data
                while cur_timestamp < start_timestamp:
                    i = self.update_close(time_frame, i, copy=True)
                    cur_timestamp += time_frame * 3600 * 1000
                cur_timestamp = close_timestamp
                i = self.update_close(time_frame, i, close)

    def update_close(self, time_frame, i, close=None, copy=False):
        if not copy:
            if i == self.window:
                self.close[time_frame] = np.roll(self.close[time_frame], -1)
                self.close[time_frame][-1] = close
            else:
                self.close[time_frame][i] = close
                i += 1
        else:
            if i != 0 and i < self.window:
                self.close[time_frame][i] = self.close[time_frame][i - 1]
                i += 1
            elif i == self.window:
                self.close[time_frame] = np.roll(self.close[time_frame], -1)
                self.close[time_frame][-1] = self.close[time_frame][-2]
        return i

    def run(self):
        """
        Run websocket
        """
        if self.mode == "100":
            self.download_past_klines(4)
            self.download_past_klines(12)

        client = Client()
        client.start()
        client.kline(
            symbol=self.symbol, id=self.id_count, interval="1m", callback=self.minute_alert
        )

        if self.mode == "100":
            client.kline(
                symbol=self.symbol, id=self.id_count + 1, interval="4h", callback=self.update_ma_4h
            )
            client.kline(
                symbol=self.symbol, id=self.id_count + 2, interval="12h", callback=self.update_ma_12h
            )

        sleep(86400 * 3)
        client.stop()

    def update_ma_4h(self, msg):
        if "k" in msg and msg["s"] == self.symbol and msg["k"]["x"] and msg["k"]["i"] == "4h":
            self.update_close("4", self.window, float(msg["k"]["c"]))

    def update_ma_12h(self, msg):
        if "k" in msg and msg["s"] == self.symbol and msg["k"]["x"] and msg["k"]["i"] == "12h":
            self.update_close("12", self.window, float(msg["k"]["c"]))

    def update_ma_24h(self, msg):
        if "k" in msg and msg["s"] == self.symbol and msg["k"]["x"] and msg["k"]["i"] == "1d":
            self.update_close("24", self.window, float(msg["k"]["c"]))

    def minute_alert(self, msg):
        if "k" in msg and msg["s"] == self.symbol and msg["k"]["x"] and msg["k"]["i"] == "1m":
            close = float(msg["k"]["c"])
            if self.last_close_1m is None:
                self.last_close_1m = close
                return
            self.alert_helper_1m(close, 4)
            self.alert_helper_1m(close, 12)
            self.last_close_1m = close

    def alert_helper_1m(self, close, timeframe):
        timeframe = str(timeframe)
        timeframe_str = f"H{timeframe}" if timeframe != "24" else "D1"
        if close > self.close[timeframe][-1] and self.last_close_1m < self.close[timeframe][-2]:
            self.tg_bot.safe_send_message(f"{self.symbol}_{self.mode} spot crossover {timeframe_str} ma200")
        elif close < self.close[timeframe][-1] and self.last_close_1m > self.close[timeframe][-2]:
            self.tg_bot.safe_send_message(f"{self.symbol}_{self.mode} spot crossunder {timeframe_str} ma200")
