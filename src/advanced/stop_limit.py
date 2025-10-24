from typing import Any, Dict

from src.common.validation import get_symbol_info, validate_side, validate_qty, validate_price, validate_notional


def place_stop_limit_order(
    client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """Place a STOP (stop-limit) order on USDT-M Futures.

    Binance Futures uses type=STOP with price + stopPrice for stop-limit.
    """
    exi = client.exchange_info()
    si = get_symbol_info(exi, symbol)
    if not si:
        raise ValueError(f"symbol {symbol} not found in exchangeInfo")

    validate_side(side)
    qty = validate_qty(si, quantity)
    limit_price = validate_price(si, price)
    trigger_price = validate_price(si, stop_price)
    validate_notional(si, limit_price, qty)

    params = {
        "symbol": symbol,
        "side": side,
        "type": "STOP",
        "timeInForce": time_in_force,
        "quantity": str(qty),
        "price": str(limit_price),
        "stopPrice": str(trigger_price),
    }
    return client.place_order(params)