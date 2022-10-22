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


class Strategy4h1d(CtaTemplate):
    author = "Jack"

    sma = True
    # ma90
    window = 100

    # _0 is the current value, _1 is the last value
    ma4h_0 = 0.0
    ma4h_1 = 0.0
    ma4h_count = 0

    ma1d_0 = 0.0
    ma1d_1 = 0.0
    ma1d_count = 0

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
    variables = ["ma4h_0", "ma4h_1", "ma1d_0", "ma1d_1", "vwap_0", "vwap_1",  "ma4h_count", "ma1d_count", "vwap_count",
                 "vwap_timeframe_count", "trend_4h", "capital", "last_trade_condition", "close", "vwap_24", "sma",
                 "vwap_volume", "vwap_high", "vwap_low", "vwap_base", "vwap_base_volume", "close_0", "close_1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg1min = BarGenerator(self.on_bar, 1, self.on_1min_bar, Interval.MINUTE)
        self.am1min = ArrayManager()
        self.bg4h = BarGenerator(self.on_bar, 4, self.on_4h_bar, Interval.HOUR)
        self.am4h = ArrayManager()
        self.bg1d = BarGenerator(self.on_bar, 24, self.on_1d_bar, Interval.HOUR)
        self.am1d = ArrayManager()
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
        self.ma4h_0 = ma4h[-1]
        self.ma4h_1 = ma4h[-2]
        self.ma4h_count = 0

    def on_1d_bar(self, bar: BarData):
        """
        update ma90_1d
        """
        self.am1d.update_bar(bar)
        if not self.am1d.inited:
            return
        if self.sma:
            ma12h = self.am1d.sma(self.window, array=True)
        else:
            ma12h = self.am1d.ema(self.window, array=True)

        self.ma1d_0 = ma12h[-1]
        self.ma1d_1 = ma12h[-2]
        self.ma1d_count = 0

    def print(self, order, date, volume, price):
        """
        print and save the order information
        """
        # print(date + ": " + str(self.capital)+", "+str(volume) + ", " + str(price))
        with open('lines.csv', 'a+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date[:20], order, str(self.vwap_1), str(self.vwap_0),
                             str(self.ma1d_1), str(self.ma1d_0), str(self.ma4h_1),
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

        if self.ma1d_count != 0:
            self.ma1d_1 = self.ma1d_0
        else:
            self.ma1d_count += 1

        if self.ma4h_count != 0:
            self.ma4h_1 = self.ma4h_0
        else:
            self.ma4h_count += 1

        if self.close_0 > self.ma4h_0 and self.close_1 < self.ma4h_1:
            if self.inited:
                self.tg_bot.send_message(self.strategy_name + " spot crossover H4 ma100 "+str(bar.datetime)[:19])

        if self.close_0 > self.ma1d_0 and self.close_1 < self.ma1d_1:
            if self.inited:
                self.tg_bot.send_message(self.strategy_name + " spot crossover D1 ma100 "+str(bar.datetime)[:19])

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        # print(bar.datetime)
        self.bg4h.update_bar(bar)
        # self.bgvwap.update_bar(bar)
        self.bg1d.update_bar(bar)
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
