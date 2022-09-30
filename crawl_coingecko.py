import requests
from pycoingecko import CoinGeckoAPI


def get_coins(num):
    cg = CoinGeckoAPI()
    market_list = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=num, page=1, sparkline=False)
    market_list = [market['symbol'].upper() for market in market_list]
    # print(market_list)
    return market_list


def get_all_exchanges():
    api_url = f'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(api_url, timeout=10).json()
    exchanges = {exchange['symbol'] for exchange in response['symbols']}
    return exchanges
