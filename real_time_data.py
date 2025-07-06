import requests  # Install requests module first.
import json

coin_names = ['B-LINK_USDT','B-XRP_USDT','B-BTC_USDT','B-1000PEPE_USDT','B-VINE_USDT','B-TRB_USDT']

def get_last_trade_price(coin):
    url = f"https://api.coindcx.com/exchange/v1/derivatives/futures/data/trades?pair={coin}"
    response = requests.get(url)
    data = response.json()
    return data[0]['price']

for coin in coin_names:
    print(f"-------------------------------- Coin Name : {coin} -----------------------------------------")
    print(get_last_trade_price(coin))