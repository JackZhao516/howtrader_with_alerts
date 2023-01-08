import time
import math
import logging
import threading
from collections import defaultdict
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client
from crawl_coingecko import CoinGecKo
from telegram_api import TelegramBot
from howtrader.trader.setting import SETTINGS

# services
TG_VOLUME_ALERT = "-859234465"
TG_PRICE_ALERT = "-824512265"
tg_bot = TelegramBot(SETTINGS["PROD"], alert=False)
tg_bot.telegram_chat_id = TG_VOLUME_ALERT
tg_bot_price = TelegramBot(SETTINGS["PROD"], alert=False)
tg_bot_price.telegram_chat_id = TG_PRICE_ALERT
cg = CoinGecKo(SETTINGS["PROD"])
MAX_ERROR = 20

config_logging(logging, logging.INFO)

# symbol->[timestamp, close1, close2]
# symbol->[timestamp, close]
exchange_bar_dict = defaultdict(list)
exchange_bar_dict_0 = defaultdict(list)
dict_lock = threading.Lock()

# dict for 15min price alert: symbol->[price_change_rate, last_price]
price_dict = defaultdict(list)
price_lock = threading.Lock()

# coin exchanges
exchanges = cg.get_500_usdt_exchanges(market_cap=False)
exchanges = [e.lower() for e in exchanges]
exchanges.sort()

# message queue
msg_queue_lock = threading.Lock()
msg_queue = []

# exchange count
exchange_count = 0

# BTC_price
BTC_price = 17000

def add_msg_to_queue(msg):
    msg_queue_lock.acquire()
    msg_queue.append(msg)
    msg_queue_lock.release()


def send_msg_from_queue(tg_bot):
    while SETTINGS["ten_time_bar"]:
        if msg_queue:
            msg_queue_lock.acquire()
            msg = msg_queue.pop(0)
            tg_bot.safe_send_message(msg)
            msg_queue_lock.release()
        time.sleep(0.11)


def monitor_price_change():
    global exchange_count
    rate_threshold = 5.0
    while SETTINGS["ten_time_bar"]:
        if exchange_count == 342:
            dict_lock.acquire()
            exchange_count = 0
            price_lists = [[k, v[0]] for k, v in price_dict.items()]
            largest, smallest = [], []

            # get the largest five
            price_lists.sort(key=lambda x: x[1], reverse=True)
            logging.info(f"price_lists: {price_lists}")
            for k, v in price_lists:
                if v >= rate_threshold and len(largest) < 5:
                    v = round(v, 2)
                    largest.append([k, v])
                if len(largest) == 5:
                    break

            # get the smallest five
            price_lists.sort(key=lambda x: x[1], reverse=False)
            logging.info(f"price_lists: {price_lists}")
            for k, v in price_lists:
                if v <= -1 * rate_threshold and len(smallest) < 5:
                    v = round(v, 2)
                    smallest.append([k, v])
                if len(smallest) == 5:
                    break

            logging.info(f"largest price change: {largest}")
            logging.info(f"smallest price change: {smallest}")
            logging.info(f"exchange bar dict: {exchange_bar_dict}")
            logging.info(f"exchange bar dict 0: {exchange_bar_dict_0}")
            if len(largest) > 0:
                tg_bot_price.safe_send_message(f"15 min top 5 positive price change in %: {largest}")
            if len(smallest) > 0:
                tg_bot_price.safe_send_message(f"15 min top 5 negative price change in %: {smallest}")
            logging.info(f"exchange_count: {exchange_count}")
            time.sleep(1)
            dict_lock.release()


##########################################################################################
def klines_alert():
    """
    alert if second and third bar are both ten times larger than first bar
    for top 500 market cap USDT exchanges on binance
    """
    id_count = 1
    start_time = time.time()
    error_count = 0
    logging.info("start ten_time_bar_alert")
    # add_msg_to_queue("start volume alert")

    try:
        SETTINGS["ten_time_bar"] = True
        # setting up the msg queue
        msg_thread = threading.Thread(target=send_msg_from_queue, args=(tg_bot,))
        msg_thread.start()

        monitor_thread = threading.Thread(target=monitor_price_change)
        monitor_thread.start()

        global exchanges
        # exchanges = exchanges[:250] if indicator == "0" else exchanges[250:]
        # exchanges = exchanges[:180]
        logging.info(f"exchanges: {len(exchanges)}")

        klines_client = Client()
        klines_client.start()
        klines_client.kline(
            symbol=exchanges, id=id_count, interval="15m", callback=alert_ten_time_bar
        )
        id_count += 1
        # klines_client.kline(
        #     symbol=exchanges, id=id_count, interval="15m", callback=alert_price
        # )

        time.sleep(88200.0 - ((time.time() - start_time) % 86400.0))
        logging.info("closing ws connection")
        klines_client.stop()
        SETTINGS["ten_time_bar"] = False
        msg_thread.join()
        monitor_thread.join()
        SETTINGS["ten_time_bar"] = True

    except Exception as e:
        error_count += 1
        if error_count > MAX_ERROR:
            raise e
        time.sleep(1)


def alert_ten_time_bar(msg):
    """
    alert if second and third bar are both 10X first bar
    alert if second bar is 50X first bar
    """
    # logging.info(f"msg: {msg}")
    alert_threshold = 500000.0
    if "stream" not in msg or "data" not in msg or "k" not in msg["data"] or \
            msg["data"]["k"]["x"] is False or msg["data"]["k"]["i"] != "15m":
        return

    if msg["data"]["k"]["s"].lower() not in exchanges:
        return

    kline = msg["data"]["k"]
    symbol = kline["s"]
    current_time = int(kline["t"])
    vol = float(kline["v"])
    # logging.info(f"symbol: {symbol}")
    close = float(kline["c"])
    amount = vol * close

    dict_lock.acquire()
    # update BTC_price
    global BTC_price
    if symbol == "BTCUSDT":
        BTC_price = close
        logging.info(f"BTC_price: {BTC_price}")

    # two bars alert
    if len(exchange_bar_dict_0[symbol]) == 2 and vol >= 50 * exchange_bar_dict[symbol][1] and \
            (((symbol[-4:] == "USDT" or symbol[-4:] == "BUSD") and amount >= alert_threshold) or
             (symbol[-3:] == "BTC" and amount >= (alert_threshold / BTC_price))):
        add_msg_to_queue(f"{symbol} 15 min volume alert 2 bars: volume [{exchange_bar_dict[symbol][1]} "
                         f"-> {vol}]\namount: ${math.ceil(amount)}")
        exchange_bar_dict_0[symbol] = [current_time, vol]
    else:
        exchange_bar_dict_0[symbol] = [current_time, vol]
    # logging.info(f"exchange_bar_dict_0: {exchange_bar_dict_0}")

    # three bars alert
    if len(exchange_bar_dict[symbol]) == 2:
        if vol != 0.0 and vol >= 10 * exchange_bar_dict[symbol][1] and\
                (((symbol[-4:] == "USDT" or symbol[-4:] == "BUSD") and amount >= alert_threshold) or
                 (symbol[-3:] == "BTC" and amount >= (alert_threshold / BTC_price))):
            exchange_bar_dict[symbol].append(vol)
            exchange_bar_dict[symbol][0] = current_time
        else:
            exchange_bar_dict[symbol] = [current_time, vol]
    elif len(exchange_bar_dict[symbol]) == 3:
        if vol != 0.0 and vol >= 10 * exchange_bar_dict[symbol][1] and \
                (((symbol[-4:] == "USDT" or symbol[-4:] == "BUSD") and amount >= alert_threshold) or
                 (symbol[-3:] == "BTC" and amount >= (alert_threshold / BTC_price))):
            add_msg_to_queue(f"{symbol} 15 min volume alert 3 bars: volume [{exchange_bar_dict[symbol][1]} "
                             f"-> {exchange_bar_dict[symbol][2]} -> {vol}]\namount: ${math.ceil(amount)}")
        exchange_bar_dict[symbol] = [current_time, vol]
    else:
        exchange_bar_dict[symbol] = [current_time, vol]
    # logging.info(exchange_bar_dict)

    # price alert
    global exchange_count
    exchange_count += 1
    # logging.info(f"exchange_count: {exchange_count}")

    if symbol not in price_dict:
        price_dict[symbol] = [0.0, close]
    else:
        price_dict[symbol][0] = (close / price_dict[symbol][1] - 1) * 100
        price_dict[symbol][1] = close
    dict_lock.release()


# def alert_price(msg):
#     """
#         mark close price change rate for 15min bar
#     """
#     # logging.info(f"msg: {msg}")
#     # TODO for testing set to 1min
#     global exchange_count
#     if "stream" not in msg or "data" not in msg or "k" not in msg["data"] or \
#             msg["data"]["k"]["x"] is False or msg["data"]["k"]["i"] != "15m":
#         return
#     # logging.info(f"msg: {msg}")
#     if msg["data"]["k"]["s"].lower() not in exchanges:
#         return
#
#     close = float(msg["data"]["k"]["c"])
#     symbol = msg["data"]["k"]["s"]
#     logging.info(f"symbol: {symbol}")
#     price_lock.acquire()
#     exchange_count += 1
#     logging.info(f"exchange_count: {exchange_count}")
#
#     if symbol not in price_dict:
#         price_dict[symbol] = [0.0, close]
#     else:
#         price_dict[symbol][0] = (close / price_dict[symbol][1] - 1) * 100
#         price_dict[symbol][1] = close
#     # logging.info(f"price_dict: {price_dict}")
#     price_lock.release()


if __name__ == "__main__":
    klines_alert()
