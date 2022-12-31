import time
import sys
import logging
import threading
from collections import defaultdict
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client
from crawl_coingecko import CoinGecKo
from telegram_api import TelegramBot
from howtrader.trader.setting import SETTINGS

tg_bot = TelegramBot(SETTINGS["PROD"], alert=False)
tg_bot.telegram_chat_id = "-859234465"
cg = CoinGecKo(SETTINGS["PROD"])
MAX_ERROR = 20

config_logging(logging, logging.INFO)

# dict for symbol->[timestamp, close1, close2]
exchange_bar_dict = defaultdict(list)
dict_lock = threading.Lock()

# # for testing
# time_counter = {}
# lock = threading.Lock()

# message queue
msg_queue_lock = threading.Lock()
msg_queue = []


def add_msg_to_queue(msg):
    msg_queue_lock.acquire()
    msg_queue.append(msg)
    msg_queue_lock.release()


def send_msg_from_queue(tg_bot):
    while SETTINGS["ten_time_bar"]:
        if msg_queue:
            msg_queue_lock.acquire()
            msg = msg_queue.pop(0)
            msg_queue_lock.release()
            tg_bot.safe_send_message(msg)
        time.sleep(1.1)


##########################################################################################
def ten_time_bar_alert(indicator):
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

        exchanges = cg.get_500_usdt_exchanges(market_cap=False)
        exchanges = [e.lower() for e in exchanges]
        logging.info(f"exchanges: {len(exchanges)}")

        exchanges = exchanges[:250] if indicator == 0 else exchanges[250:]

        klines_client = Client()
        klines_client.start()
        klines_client.kline(
            symbol=exchanges, id=id_count, interval="5m", callback=alert_ten_time_bar
        )

        time.sleep(86400.0 - ((time.time() - start_time) % 86400.0))
        logging.info("closing ws connection")
        klines_client.stop()
        SETTINGS["ten_time_bar"] = False
        msg_thread.join()
        SETTINGS["ten_time_bar"] = True

    except Exception as e:
        error_count += 1
        if error_count > MAX_ERROR:
            raise e
        time.sleep(1)


def alert_ten_time_bar(msg):
    """
    alert if second and third bar are both ten times larger than first bar
    """
    # logging.info(f"msg: {msg}")
    if "stream" not in msg or "data" not in msg or "k" not in msg["data"] or \
            msg["data"]["k"]["x"] is False or msg["data"]["k"]["i"] != "5m":
        return

    kline = msg["data"]["k"]
    symbol = kline["s"]
    current_time = int(kline["t"])
    vol = float(kline["v"])
    logging.info(f"symbol: {symbol}")
    close = float(kline["c"])
    amount = vol * close
    # # for testing
    # lock.acquire()
    # if current_time not in time_counter:
    #     time_counter[current_time] = 1
    # else:
    #     time_counter[current_time] += 1
    #
    # for k, v in time_counter.items():
    #     logging.info(f"vs: {v}")
    # lock.release()

    dict_lock.acquire()
    if len(exchange_bar_dict[symbol]) == 2:
        if vol != 0.0 and vol >= 10 * exchange_bar_dict[symbol][1] and ((symbol[-4:] == "USDT" or symbol[-4:] == "BUSD") and amount > 10000.0 or symbol[-3:] == "BTC" and amount > 0.1):
            exchange_bar_dict[symbol].append(vol)
            exchange_bar_dict[symbol][0] = current_time
        else:
            exchange_bar_dict[symbol] = [current_time, vol]
    elif len(exchange_bar_dict[symbol]) == 3:
        if vol != 0.0 and vol >= 10 * exchange_bar_dict[symbol][1] and ((symbol[-4:] == "USDT" or symbol[-4:] == "BUSD") and amount > 10000.0 or symbol[-3:] == "BTC" and amount > 0.1):
            add_msg_to_queue(f"{symbol} 5min bar ten times alert: volume [{exchange_bar_dict[symbol][1]} -> {exchange_bar_dict[symbol][2]} -> {vol}]")
        exchange_bar_dict[symbol] = [current_time, vol]
    else:
        exchange_bar_dict[symbol] = [current_time, vol]
    logging.info(exchange_bar_dict)
    dict_lock.release()


if __name__ == "__main__":
    ten_time_bar_alert(sys.argv[1])
