import crawl_coingecko
from pycoingecko import CoinGeckoAPI
from crawl_coingecko import CoinGecKo
from decimal import Decimal


class CoinGecKo12H(CoinGecKo):
    def __init__(self, coin_id, PROD=True):
        super().__init__(prod=PROD)
        self.coin_id = coin_id
        self.less_90_days = False
        self.ma_180 = self.h12_sma_180()

    def h12_sma_180(self):
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=90)
        price = price['prices']
        if len(price) < 2150:
            self.less_90_days = True
        price = [i[1] for i in price]
        res = 0
        for i in range(0, len(price), 12):
            res += price[i]
        return res / 180

    def alert_spot(self):
        price = self.cg.get_coin_market_chart_by_id(id=self.coin_id, vs_currency='usd', days=1)
        price = price['prices'][-1][1]
        # price = Decimal(price)
        print(f"coin_id: {self.coin_id}, price: {price}, ma_180: {self.ma_180}, {price > self.ma_180}, new_coin: {self.less_90_days}")
        return price > self.ma_180


if __name__ == '__main__':
    cg = CoinGecKo12H("bitcoin")
    cg.alert_spot()
