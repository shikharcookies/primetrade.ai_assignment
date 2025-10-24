PrimeTrade: CLI Binance USDT-M Futures Bot (Testnet)

Overview
- CLI bot for Binance USDⓈ-M Futures Testnet (`https://testnet.binancefuture.com`).
- Supports MARKET and LIMIT (mandatory), plus STOP (stop-limit) and TWAP (bonus).
- Validates symbol, quantity, price using `exchangeInfo` filters and logs every action to `bot.log` in structured JSON.

Features
- MARKET orders: buy/sell with validated quantity.
- LIMIT orders: buy/sell with validated price, quantity, and notional.
- STOP (stop-limit): limit order triggered at `stopPrice`.
- TWAP: splits a large order into timed slices (MARKET or LIMIT).
- Robust logging: requests, responses, and errors captured to `bot.log`.

Requirements
- Python 3.9+ recommended.
- Dependencies: `requests`.

Setup
- Create and activate a venv and install deps:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Export credentials (or pass via CLI):
  - `export BINANCE_API_KEY=YOUR_KEY`
  - `export BINANCE_API_SECRET=YOUR_SECRET`
- Testnet account and API keys required; activate USDT-M Futures account in testnet.

Usage
- From project root, run the CLI:
  - MARKET: `python -m src.cli market --symbol BTCUSDT --side BUY --quantity 0.001`
  - LIMIT: `python -m src.cli limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 70000 --tif GTC`
  - STOP-LIMIT: `python -m src.cli stop-limit --symbol BTCUSDT --side BUY --quantity 0.001 --price 69000 --stop-price 68000 --tif GTC`
  - TWAP MARKET: `python -m src.cli twap --symbol BTCUSDT --side BUY --total-quantity 0.01 --slices 5 --interval 3 --type MARKET`
  - TWAP LIMIT: `python -m src.cli twap --symbol BTCUSDT --side SELL --total-quantity 0.01 --slices 4 --interval 5 --type LIMIT --limit-price 71000`
- Realnet (not recommended for testing): add `--realnet` to use `https://fapi.binance.com`.

Validation & Logging
- Validation:
  - Quantity respects `LOT_SIZE.stepSize`, `minQty`, `maxQty`.
  - Price respects `PRICE_FILTER.tickSize`, `minPrice`, `maxPrice`.
  - Notional checked when available (`NOTIONAL` or `MIN_NOTIONAL`).
- Logging:
  - All API requests/responses/errors are logged in JSON to `bot.log` and stdout.

Design Notes
- REST-only implementation to ensure precise testnet base URL handling.
- `src/binance_client.py` signs requests with HMAC SHA256 and attaches `X-MBX-APIKEY`.
- `exchangeInfo` is fetched before each order to validate parameters.

Binance Docs
- Official Futures API docs: https://binance-docs.github.io/apidocs/futures/en/
- Note: As of 2025-10-23, `priceMatch` enum values `OPPONENT_10` and `OPPONENT_20` are temporarily removed from place/amend flows; this bot does not use `priceMatch`. Source: https://binance-docs.github.io/apidocs/futures/en/ (Change Log).

Files
- `src/common/logger.py`: JSON logger.
- `src/common/validation.py`: input validations using `exchangeInfo`.
- `src/binance_client.py`: REST client for Futures (`/fapi`).
- `src/market_orders.py`: MARKET order logic.
- `src/limit_orders.py`: LIMIT order logic.
- `src/advanced/stop_limit.py`: STOP (stop-limit) logic.
- `src/advanced/twap.py`: TWAP strategy.
- `bot.log`: log file (created on first run).
- `report.pdf`: analysis/notes placeholder.

Caveats
- TWAP sleeps in-process; do not interrupt for consistent execution.
- MARKET order notional validation is approximate unless current price is fetched; kept simple here.
- Hedge-mode, reduceOnly, and positionSide are not exposed in CLI in this version.

Submission
- Create the zip from project root:
  - `zip -r shikharsingh_binance_bot.zip .`
- Ensure `bot.log` and `report.pdf` are included before zipping.