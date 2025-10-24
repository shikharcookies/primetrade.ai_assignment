import os
import json
from flask import Flask, request, redirect, url_for, render_template_string

from src.binance_client import BinanceFuturesClient
from src.market_orders import place_market_order
from src.limit_orders import place_limit_order
from src.advanced.oco import place_oco_order


def load_env_from_file():
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip('"').strip("'")
                            os.environ[key] = val
            except Exception:
                pass
            break


def get_client():
    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("BINANCE_API_KEY and BINANCE_API_SECRET are required")
    base_url = "https://testnet.binancefuture.com"
    return BinanceFuturesClient(api_key, api_secret, base_url=base_url, log_file_path="bot.log")


app = Flask(__name__)
app.secret_key = "dev-key"

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>PrimeTrade Web UI</title>
  <style>
    body { font-family: system-ui, -apple-system, Arial; margin: 24px; }
    h1 { margin-bottom: 8px; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    form { border: 1px solid #ddd; border-radius: 8px; padding: 12px; }
    label { display: block; margin: 6px 0 2px; font-size: 13px; }
    input, select { width: 100%; padding: 6px; font-size: 14px; }
    button { margin-top: 8px; padding: 8px 10px; font-size: 14px; }
    pre { background: #f8f8f8; padding: 12px; border-radius: 8px; overflow: auto; }
    .section { margin-top: 20px; }
  </style>
</head>
<body>
  <h1>PrimeTrade Web UI</h1>
  <p>Submit orders below. Results persist to <code>last_response.json</code>.</p>

  <div class="grid">
    <!-- Market Order -->
    <form method="post" action="{{ url_for('market') }}">
      <h3>Market Order</h3>
      <label>Symbol</label>
      <input name="symbol" value="BTCUSDT" />
      <label>Side</label>
      <select name="side">
        <option>BUY</option>
        <option>SELL</option>
      </select>
      <label>Quantity</label>
      <input name="quantity" value="0.001" />
      <button type="submit">Place Market</button>
    </form>

    <!-- Limit Order -->
    <form method="post" action="{{ url_for('limit') }}">
      <h3>Limit Order</h3>
      <label>Symbol</label>
      <input name="symbol" value="BTCUSDT" />
      <label>Side</label>
      <select name="side">
        <option>BUY</option>
        <option selected>SELL</option>
      </select>
      <label>Quantity</label>
      <input name="quantity" value="0.001" />
      <label>Price</label>
      <input name="price" value="110000" />
      <label>Time In Force</label>
      <select name="tif">
        <option selected>GTC</option>
        <option>IOC</option>
        <option>FOK</option>
      </select>
      <button type="submit">Place Limit</button>
    </form>

    <!-- OCO Order -->
    <form method="post" action="{{ url_for('oco') }}">
      <h3>OCO (Limit + Stop)</h3>
      <label>Symbol</label>
      <input name="symbol" value="BTCUSDT" />
      <label>Side</label>
      <select name="side">
        <option selected>SELL</option>
        <option>BUY</option>
      </select>
      <label>Quantity</label>
      <input name="quantity" value="0.001" />
      <label>Limit Price</label>
      <input name="price" value="110000" />
      <label>Stop Price</label>
      <input name="stop_price" value="100000" />
      <label>Stop-Limit Price</label>
      <input name="stop_limit_price" value="100000" />
      <button type="submit">Place OCO</button>
    </form>
  </div>

  <div class="section">
    <h3>Last Response</h3>
    <pre>{{ last_response }}</pre>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    # Load last response for display
    try:
        with open("last_response.json", "r") as f:
            lr = json.load(f)
        last_response = json.dumps(lr, indent=2)
    except Exception:
        last_response = "{}"
    return render_template_string(INDEX_HTML, last_response=last_response)


def persist_response(title: str, response: dict):
    try:
        with open("last_response.json", "w") as f:
            json.dump({"title": title, "response": response}, f, indent=2)
    except Exception:
        pass


@app.route("/market", methods=["POST"])
def market():
    load_env_from_file()
    client = get_client()
    symbol = request.form.get("symbol", "BTCUSDT")
    side = request.form.get("side", "BUY")
    quantity = float(request.form.get("quantity", "0.001"))
    res = place_market_order(client, symbol, side, quantity)
    persist_response("Market Order Response", res)
    return redirect(url_for("index"))


@app.route("/limit", methods=["POST"])
def limit():
    load_env_from_file()
    client = get_client()
    symbol = request.form.get("symbol", "BTCUSDT")
    side = request.form.get("side", "SELL")
    quantity = float(request.form.get("quantity", "0.001"))
    price = float(request.form.get("price", "110000"))
    tif = request.form.get("tif", "GTC")
    res = place_limit_order(client, symbol, side, quantity, price, time_in_force=tif)
    persist_response("Limit Order Response", res)
    return redirect(url_for("index"))


@app.route("/oco", methods=["POST"])
def oco():
    load_env_from_file()
    client = get_client()
    symbol = request.form.get("symbol", "BTCUSDT")
    side = request.form.get("side", "SELL")
    quantity = float(request.form.get("quantity", "0.001"))
    price = float(request.form.get("price", "110000"))
    stop_price = float(request.form.get("stop_price", "100000"))
    stop_limit_price = float(request.form.get("stop_limit_price", stop_price))
    res = place_oco_order(client, symbol, side, quantity, price, stop_price, stop_limit_price)
    persist_response("OCO Order Response", res)
    return redirect(url_for("index"))


if __name__ == "__main__":
    load_env_from_file()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))