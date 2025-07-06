import hmac
import hashlib
import json
import time
import requests

# API credentials
key = "c59533f65955dd8ae2cf3a054af838dfd18ccbce81917c17"
secret = "ae637e28beb87b0dd0238fe47f4c924fcb7fc441263827fdb319ad4ff165a443"

secret_bytes = bytes(secret, encoding='utf-8')
timeStamp = int(time.time())

# --- Step 1: Fetch Position Data ---
body = {
    "timestamp": timeStamp,
    "status": "open, filled, partially_filled, partially_cancelled, cancelled, rejected, untriggered",
    "side": "buy",
    "page": "1",
    "size": "10",
    "margin_currency_short_name": ["INR"]
}
json_body = json.dumps(body, separators=(',', ':'))
signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

positions_url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions"
headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': key,
    'X-AUTH-SIGNATURE': signature
}
positions_response = requests.post(positions_url, data=json_body, headers=headers)
positions = positions_response.json()

# --- Step 2: Fetch Wallet Data ---
wallet_body = {"timestamp": int(round(time.time() * 1000))}
wallet_json = json.dumps(wallet_body, separators=(',', ':'))
wallet_signature = hmac.new(secret_bytes, wallet_json.encode(), hashlib.sha256).hexdigest()

wallet_url = "https://api.coindcx.com/exchange/v1/derivatives/futures/wallets"
wallet_headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': key,
    'X-AUTH-SIGNATURE': wallet_signature
}
wallet_response = requests.get(wallet_url, data=wallet_json, headers=wallet_headers)
wallet_data = wallet_response.json()

wallet_inr = next((w for w in wallet_data if w["currency_short_name"] == "INR"), {})
available_inr = float(wallet_inr.get("balance", 0))
locked_inr = float(wallet_inr.get("locked_balance", 0))
total_inr = available_inr + locked_inr

# --- Step 3: Fetch Last Traded Price ---
def get_last_trade_price(pair):
    url = f"https://api.coindcx.com/exchange/v1/derivatives/futures/data/trades?pair={pair}"
    try:
        resp = requests.get(url)
        data = resp.json()
        return float(data[0]['price'])
    except:
        return None

# --- Step 4: Print Summary ---
print("📊 Futures P&L + Wallet Strategy:\n")
print(f"💰 Total Wallet: ₹{total_inr:.2f} | Free: ₹{available_inr:.2f} | Locked: ₹{locked_inr:.2f}\n")

for pos in positions:
    qty = float(pos["active_pos"])
    if qty == 0.0:
        continue

    pair = pos["pair"]
    avg_price = float(pos["avg_price"])
    leverage = float(pos.get("leverage", 1))
    inr_rate = float(pos.get("settlement_currency_avg_price", 83.0))
    live_price = get_last_trade_price(pair)
    if not live_price:
        continue

    pnl_inr = (live_price - avg_price) * qty * inr_rate
    pnl_percent = ((live_price - avg_price) / avg_price) * leverage * 100
    invested_inr = float(pos.get("locked_user_margin", (avg_price * qty) / leverage)) * inr_rate
    invest_pct = (invested_inr / total_inr) * 100

    print(f"🔹 {pair}")
    print(f"   Invested: ₹{invested_inr:.2f}")
    print(f"   P&L: ₹{pnl_inr:.2f}")
    print(f"   P&L %: {pnl_percent:.2f}%")
    print(f"   📊 Investment % of Wallet: {invest_pct:.2f}%")

    # 🧠 Updated Investment-based Take Profit Strategy
    tp_percent = None
    if invest_pct <= 25:
        tp_percent = 0.41
    elif invest_pct <= 40:
        tp_percent = 0.32
    elif invest_pct <= 60:
        tp_percent = 0.23
    elif invest_pct <= 80:
        tp_percent = 0.17
    elif invest_pct <= 100:
        tp_percent = 0.105

    if tp_percent is not None:
        target_pnl = invested_inr * tp_percent
        print(f"   📌 Strategy Target: ₹{target_pnl:.2f} ({tp_percent * 100:.2f}% of investment)")
        if pnl_inr >= target_pnl:
            print(f"   ✅ Book Profit: Target reached. Suggest booking ₹{target_pnl:.2f}\n")
        else:
            print(f"   🕒 Hold: Target is ₹{target_pnl:.2f}, current is ₹{pnl_inr:.2f}\n")
    else:
        print(f"   ⚠️ Investment is {invest_pct:.1f}% of wallet — consider custom strategy.\n")
