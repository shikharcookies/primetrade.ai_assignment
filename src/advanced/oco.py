import time
from typing import Any, Dict

from src.common.validation import (
    get_symbol_info,
    validate_side,
    validate_qty,
    validate_price,
)


def place_oco_order(
    client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
    stop_limit_price: float | None = None,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Simulate an OCO (One-Cancels-the-Other) on USDT-M Futures by placing
    a LIMIT order and a STOP (stop-limit) order together.

    Binance Futures does not provide a native OCO endpoint like Spot.
    This function submits both orders and returns both API responses.
    Managing cancellation of the remaining order after one fills would
    normally require websocket/order updates, which are out of scope for
    this CLI-only bot.

    Args:
        client: BinanceFuturesClient instance
        symbol: Trading symbol, e.g. "BTCUSDT"
        side: "BUY" or "SELL"
        quantity: base asset quantity
        price: limit order price
        stop_price: trigger price for the stop-limit order
        stop_limit_price: price for the stop-limit order (defaults to stop_price)
        time_in_force: e.g., "GTC"

    Returns:
        Dict with both order responses: {"limit_order": ..., "stop_order": ...}
    """
    exi = client.exchange_info()
    si = get_symbol_info(exi, symbol)
    if not si:
        raise ValueError(f"symbol {symbol} not found in exchangeInfo")

    validate_side(side)
    qty = validate_qty(si, quantity)
    limit_px = validate_price(si, price)
    trigger_px = validate_price(si, stop_price)

    if stop_limit_price is None:
        stop_limit_price = stop_price
    stop_limit_px = validate_price(si, stop_limit_price)

    base_client_id = f"oco-{symbol}-{int(time.time()*1000)}"

    limit_params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": time_in_force,
        "quantity": str(qty),
        "price": str(limit_px),
        "newClientOrderId": f"{base_client_id}-limit",
    }

    stop_params = {
        "symbol": symbol,
        "side": side,
        "type": "STOP",
        "timeInForce": time_in_force,
        "quantity": str(qty),
        "price": str(stop_limit_px),
        "stopPrice": str(trigger_px),
        "newClientOrderId": f"{base_client_id}-stop",
    }

    limit_resp = client.place_order(limit_params)
    stop_resp = client.place_order(stop_params)

    return {"limit_order": limit_resp, "stop_order": stop_resp}