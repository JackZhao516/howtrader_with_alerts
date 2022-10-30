import datetime

from howtrader.app.cta_strategy import (
    CtaTemplate,
    StopOrder
)

from howtrader.trader.object import TickData, BarData, TradeData, OrderData, Interval
from howtrader.trader.utility import BarGenerator, ArrayManager
from decimal import Decimal
from telegram_api import TelegramBot
import csv

threshold = 0.001


class Strategy4h12h(CtaTemplate):
    author = "Jack"

    sma = True
    # ma90
    window = 200

    # _0 is the current value, _1 is the last value
    ma4h_0 = 0.0
    ma4h_1 = 0.0
    ma4h_count = 0

    ma12h_0 = 0.0
    ma12h_1 = 0.0
    ma12h_count = 0

    close_0 = 0.0
    close_1 = 0.0

    vwap_base = 0.0
    vwap_base_volume = 0.0
    vwap_volume = 0.0
    vwap_high = 0.0
    vwap_low = 10000.0
    vwap_0 = 0.0
    vwap_1 = 0.0
    vwap_count = 0

    vwap_24 = 0.0

    vwap_timeframe_count = 23
    trend_4h = 0  # 1 for bull, -1 for bear
    last_trade_condition = 0
    close = False

    capital = Decimal(10000)

    parameters = ["window"]
    variables = ["ma4h_0", "ma4h_1", "ma12h_0", "ma12h_1", "vwap_0", "vwap_1", "ma4h_count", "ma12h_count", "vwap_count",
                 "vwap_timeframe_count", "trend_4h", "capital", "last_trade_condition", "close", "vwap_24", "sma",
                 "vwap_volume", "vwap_high", "vwap_low", "vwap_base", "vwap_base_volume", "close_0", "close_1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg1min = BarGenerator(self.on_bar, 1, self.on_1min_bar, Interval.MINUTE)
        self.am1min = ArrayManager()
        self.bg4h = BarGenerator(self.on_bar, 4, self.on_4h_bar, Interval.HOUR)
        self.am4h = ArrayManager()
        self.bg12h = BarGenerator(self.on_bar, 12, self.on_12h_bar, Interval.HOUR)
        self.am12h = ArrayManager()
        self.tg_bot = TelegramBot()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log(f"Init")
        self.load_bar(101)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("Start")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("Stop")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg1min.update_tick(tick)

    def on_4h_bar(self, bar: BarData):
        """
        update ma90_4h
        """
        self.am4h.update_bar(bar)
        if not self.am4h.inited:
            return
        if self.sma:
            ma4h = self.am4h.sma(self.window, array=True)
        else:
            ma4h = self.am4h.ema(self.window, array=True)
        # print(self.am4h.close)
        self.ma4h_0 = ma4h[-1]
        self.ma4h_1 = ma4h[-2]
        self.ma4h_count = 0

    def on_12h_bar(self, bar: BarData):
        """
        update ma90_12h
        """
        self.am12h.update_bar(bar)
        if not self.am12h.inited:
            return
        if self.sma:
            ma12h = self.am12h.sma(self.window, array=True)
        else:
            ma12h = self.am12h.ema(self.window, array=True)

        self.ma12h_0 = ma12h[-1]
        self.ma12h_1 = ma12h[-2]
        self.ma12h_count = 0

    def print(self, order, date, volume, price):
        """
        print and save the order information
        """
        # print(date + ": " + str(self.capital)+", "+str(volume) + ", " + str(price))
        with open('lines.csv', 'a+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date[:20], order, str(self.vwap_1), str(self.vwap_0),
                             str(self.ma12h_1), str(self.ma12h_0), str(self.ma4h_1),
                             str(self.ma4h_0)])

    def on_1min_bar(self, bar: BarData):
        """
        trade on minute bar
        """
        self.am1min.update_bar(bar)
        if not self.am1min.inited:
            return

        close = self.am1min.close
        # print(close)
        self.close_0 = close[-1]
        self.close_1 = close[-2]

        if self.ma12h_count != 0:
            self.ma12h_1 = self.ma12h_0
        else:
            self.ma12h_count += 1

        if self.ma4h_count != 0:
            self.ma4h_1 = self.ma4h_0
        else:
            self.ma4h_count += 1

        # if str(bar.datetime) == "2021-10-28 00:01:00-04:00":
        #     print("0", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        # if str(bar.datetime) == "2021-10-28 00:59:00-04:00":
        #     print("1", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        # if str(bar.datetime) == "2021-10-28 01:00:00-04:00":
        #     print("2", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        # if self.inited:
        if self.close_0 > self.ma4h_0 and self.close_1 < self.ma4h_1:
            if self.inited:
                self.tg_bot.safe_send_message(self.strategy_name + " spot crossover H4 ma200 "+str(bar.datetime)[:19])
            # print(self.strategy_name + " spot crossover H4 ma200 ", str(bar.datetime)[:19])
        elif self.close_0 < self.ma4h_0 and self.close_1 > self.ma4h_1:
            if self.inited:
                self.tg_bot.safe_send_message(self.strategy_name + " spot crossunder H4 ma200 "+str(bar.datetime)[:19])
            # print(self.strategy_name + " spot crossunder H4 ma200 ", str(bar.datetime)[:19])
        if self.close_0 > self.ma12h_0 and self.close_1 < self.ma12h_1:
            if self.inited:
                self.tg_bot.safe_send_message(self.strategy_name + " spot crossover H12 ma200 "+str(bar.datetime)[:19])
            # print(self.strategy_name + " spot crossover H12 ma200 ", str(bar.datetime)[:19])
        elif self.close_0 < self.ma12h_0 and self.close_1 > self.ma12h_1:
            if self.inited:
                self.tg_bot.safe_send_message(self.strategy_name + " spot crossunder H12 ma200 "+str(bar.datetime)[:19])
            # print(self.strategy_name + " spot crossunder H12 ma200 ", str(bar.datetime)[:19])

        # with open('full_lines.csv', 'a+', encoding='UTF8', newline='') as f:
        #     writer = csv.writer(f)
        #     writer.writerow([str(bar.datetime)[:20], str(bar.close_price), str(bar.high_price),
        #                      str(bar.low_price), str(bar.volume), str(self.vwap_1),
        #                      str(self.vwap_0), str(self.ma1h_1), str(self.ma1h_0),
        #                      str(self.ma4h_1), str(self.ma4h_0), str(self.vwap_timeframe_count)])

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        # print(bar.datetime)
        self.bg4h.update_bar(bar)
        # self.bgvwap.update_bar(bar)
        self.bg12h.update_bar(bar)
        self.bg1min.update_bar(bar)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
