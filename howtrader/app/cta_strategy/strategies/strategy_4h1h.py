import datetime

from howtrader.app.cta_strategy import (
    CtaTemplate,
    StopOrder
)

from howtrader.trader.object import TickData, BarData, TradeData, OrderData, Interval
from howtrader.trader.utility import BarGenerator, ArrayManager
from decimal import Decimal
from telegram_api import send_message
import csv

threshold = 0.001


class Strategy4h1h(CtaTemplate):
    author = "Jack"

    sma = False
    # ma90
    window = 90

    # _0 is the current value, _1 is the last value
    ma4h_0 = 0.0
    ma4h_1 = 0.0
    ma4h_count = 0

    ma1h_0 = 0.0
    ma1h_1 = 0.0
    ma1h_count = 0

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
    variables = ["ma4h_0", "ma4h_1", "ma1h_0", "ma1h_1", "vwap_0", "vwap_1", "ma4h_count", "ma1h_count", "vwap_count",
                 "vwap_timeframe_count", "trend_4h", "capital", "last_trade_condition", "close", "vwap_24", "sma",
                 "vwap_volume", "vwap_high", "vwap_low", "vwap_base", "vwap_base_volume"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg1min = BarGenerator(self.on_bar, 1, self.on_1min_bar, Interval.MINUTE)
        self.am1min = ArrayManager()
        self.bg1h = BarGenerator(self.on_bar, 1, self.on_1h_bar, Interval.HOUR)
        self.am1h = ArrayManager()
        self.bgvwap = BarGenerator(self.on_bar, 1, self.on_vwap_bar, Interval.HOUR)
        self.amvwap = ArrayManager()

        self.bg4h = BarGenerator(self.on_bar, 4, self.on_4h_bar, Interval.HOUR)
        self.am4h = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(30)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg1min.update_tick(tick)

    def close_all(self, bar: BarData, num):
        """
        close all open orders
        """
        if self.pos < -threshold and not self.close:
            self.capital -= Decimal(bar.close_price)*Decimal(abs(self.pos))
            self.cover(Decimal(bar.close_price), Decimal(abs(self.pos)))
            date = bar.datetime - datetime.timedelta(hours=1)
            self.print("close"+num, str(date), Decimal(abs(self.pos)), bar.close_price)
            self.close = True
            self.last_trade_condition = 0
        elif self.pos > threshold and not self.close:
            self.capital += Decimal(bar.close_price)*Decimal(abs(self.pos))
            # print(bar.datetime)
            if str(bar.datetime) == "2021-12-28 00:59:00-05:00":
                self.sell(Decimal(bar.close_price)-Decimal(0.01), Decimal(abs(self.pos)))
            else:
                self.sell(Decimal(bar.close_price), Decimal(abs(self.pos)))
            date = bar.datetime - datetime.timedelta(hours=1)
            self.print("close"+num, str(date), Decimal(abs(self.pos)), bar.close_price)
            self.close = True
            self.last_trade_condition = 0

    def long_order(self, bar: BarData, num):
        """
        long order
        """
        self.close_all(bar, num)
        volume = Decimal(self.capital) / Decimal(bar.close_price)
        self.buy(Decimal(bar.close_price), Decimal(volume))
        self.capital = 0
        date = bar.datetime - datetime.timedelta(hours=1)
        self.print("long"+num, str(date), volume, bar.close_price)
        self.close = False

    def short_order(self, bar: BarData, num):
        """
        short order
        """
        self.close_all(bar, num)
        volume = Decimal(self.capital) / Decimal(bar.close_price)
        if str(bar.datetime) == "2021-12-28 00:59:00-05:00":
            self.short(Decimal(bar.close_price)-Decimal(0.01), Decimal(volume))
        else:
            self.short(Decimal(bar.close_price), Decimal(volume))
        self.capital *= 2
        date = bar.datetime - datetime.timedelta(hours=1)
        self.print('short'+num, str(date), volume, bar.close_price)
        self.close = False

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

    def on_1h_bar(self, bar: BarData):
        """
        update ma90_1h
        """
        self.am1h.update_bar(bar)
        if not self.am1h.inited:
            return
        if self.sma:
            ma1h = self.am1h.sma(self.window, array=True)
        else:
            ma1h = self.am1h.ema(self.window, array=True)
        self.ma1h_0 = ma1h[-1]
        self.ma1h_1 = ma1h[-2]
        self.ma1h_count = 0
        # save line information
        #
        with open('full_lines.csv', 'a+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([str(bar.datetime)[:20], str(bar.close_price), str(bar.high_price),
                             str(bar.low_price), str(bar.volume), str(self.vwap_1),
                             str(self.vwap_0), str(self.ma1h_1), str(self.ma1h_0),
                             str(self.ma4h_1), str(self.ma4h_0), str(self.vwap_timeframe_count)])

        # print("ma1h"+str(bar.datetime) + str(self.ma1h_0)+ "   " + str(self.ma1h_1))
        # print("ma4h"+str(bar.datetime) + str(self.ma4h_0) + "   " + str(self.ma4h_1))
        # print("vwap"+str(bar.datetime) + str(self.vwap_0) + "   " + str(self.vwap_1))

    def on_vwap_bar(self, bar: BarData):
        """
        update vwap
        """
        # flush the vwap data every 24 hours, i.e. every day
        if self.vwap_timeframe_count == 23:
            self.amvwap = ArrayManager()
            self.vwap_timeframe_count = 0
        else:
            self.vwap_timeframe_count += 1
        # # print(str(self.vwap_timeframe_count)+"  "+str(bar.datetime))
        self.amvwap.update_bar(bar)

        self.vwap_base_volume = self.amvwap.cumsum_volume()[0]
        # print("volume", self.vwap_base_volume)
        vwap = self.amvwap.vwap(array=True)
        # print("vwap", vwap)

        # self.vwap_24 stores the last hour vwap for last day.
        self.vwap_0 = vwap[-1]
        # self.vwap_1 = vwap[-2]
        if self.vwap_timeframe_count == 0:
            self.vwap_1 = self.vwap_24
        else:
            self.vwap_1 = vwap[-2]
        if self.vwap_timeframe_count == 23:
            self.vwap_24 = vwap[-1]
        # # print("vwap"+str(bar.datetime) + str(self.vwap_0) + "   " + str(self.vwap_1))
        self.vwap_count = 0
        self.vwap_base = self.vwap_0

    def print(self, order, date, volume, price):
        """
        print and save the order information
        """
        # print(date + ": " + str(self.capital)+", "+str(volume) + ", " + str(price))
        with open('lines.csv', 'a+', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date[:20], order, str(self.vwap_1), str(self.vwap_0),
                             str(self.ma1h_1), str(self.ma1h_0), str(self.ma4h_1),
                             str(self.ma4h_0)])

    def on_1min_bar(self, bar: BarData):
        """
        trade on minute bar
        """
        self.am1min.update_bar(bar)
        if not self.am1min.inited:
            return

        if self.ma1h_count != 0:
            self.ma1h_1 = self.ma1h_0
        else:
            self.ma1h_count += 1

        if self.ma4h_count != 0:
            self.ma4h_1 = self.ma4h_0
        else:
            self.ma4h_count += 1

        if self.vwap_count != 0:
            # print("bar", bar.volume)
            self.vwap_volume += bar.volume
            self.vwap_high = max(self.vwap_high, bar.high_price)
            self.vwap_low = min(self.vwap_low, bar.low_price)
            self.vwap_1 = self.vwap_0
            self.vwap_0 = (self.vwap_base * self.vwap_base_volume + (self.vwap_high + self.vwap_low + bar.close_price) * self.vwap_volume/3)/(self.vwap_base_volume + self.vwap_volume)
        else:
            self.vwap_count += 1
            self.vwap_volume = 0.0
            self.vwap_high = 0.0
            self.vwap_low = 10000.0

        # indicators
        bull_4h = self.vwap_0 > self.ma4h_0 and self.vwap_1 < self.ma4h_1
        bear_4h = self.vwap_0 < self.ma4h_0 and self.vwap_1 > self.ma4h_1
        bull_1h = self.vwap_0 > self.ma1h_0 and self.vwap_1 < self.ma1h_1
        bear_1h = self.vwap_0 < self.ma1h_0 and self.vwap_1 > self.ma1h_1

        # if str(bar.datetime) == "2021-10-28 00:01:00-04:00":
        #     print("0", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        # if str(bar.datetime) == "2021-10-28 00:59:00-04:00":
        #     print("1", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        # if str(bar.datetime) == "2021-10-28 01:00:00-04:00":
        #     print("2", self.vwap_0, self.vwap_1, self.ma4h_0, self.ma4h_1, self.ma1h_0, self.ma1h_1)
        if self.inited:
            if bull_4h and self.last_trade_condition != 1 and self.last_trade_condition != 3 and self.pos < threshold:
                # 4h bull
                if self.inited:
                    send_message(self.strategy_name + " long_1 "+str(bar.datetime)[:19])
                print(self.strategy_name + "long_1", str(bar.datetime)[:19])
                # self.long_order(bar, "1")
                self.trend_4h = 1
                self.last_trade_condition = 1

            elif bear_4h and self.last_trade_condition != 2 and self.last_trade_condition != 5 and self.pos > -threshold:
                # 4h bear
                if self.inited:
                    send_message(self.strategy_name + " short_2 "+str(bar.datetime)[:19])
                print(self.strategy_name + "short_2", str(bar.datetime)[:19])
                # self.short_order(bar, "2")
                self.trend_4h = -1
                self.last_trade_condition = 2

            elif self.trend_4h == 1 and bull_1h and self.last_trade_condition != 3 and self.last_trade_condition != 1 and self.pos < threshold:
                # in 4h bull zone, 1h bull
                if self.inited:
                    send_message(self.strategy_name + " long_3 "+str(bar.datetime)[:19])
                print(self.strategy_name + "long_3", str(bar.datetime)[:19])
                # self.long_order(bar, "3")
                self.last_trade_condition = 3

            elif self.trend_4h == 1 and bear_1h and self.last_trade_condition != 4:
                # in 4h bull zone, 1h bear
                if self.inited:
                    send_message(self.strategy_name + " close_long_4 "+str(bar.datetime)[:19])
                print(self.strategy_name + "close_long_4", str(bar.datetime)[:19])
                # self.close_all(bar, "4")
                self.last_trade_condition = 4

            elif self.trend_4h == -1 and bear_1h and self.last_trade_condition != 2 and self.last_trade_condition != 5 and self.pos > -threshold:
                # in 4h bear zone, 1h bear
                if self.inited:
                    send_message(self.strategy_name + " short_5 "+str(bar.datetime)[:19])
                print(self.strategy_name + "short_5", str(bar.datetime)[:19])
                # self.short_order(bar, "5")
                self.last_trade_condition = 5

            elif self.trend_4h == -1 and bull_1h and self.last_trade_condition != 6:
                # in 4h bear zone, 1h bull
                if self.inited:
                    send_message(self.strategy_name + " close_short_6 "+str(bar.datetime)[:19])
                print(self.strategy_name + "close_short_6", str(bar.datetime)[:19])
                # self.close_all(bar, "6")
                self.last_trade_condition = 6

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
        # self.bg1min.update_bar(bar)
        self.bg4h.update_bar(bar)
        self.bgvwap.update_bar(bar)
        self.bg1h.update_bar(bar)
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
