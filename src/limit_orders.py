from typing import Any, Dict

from src.common.validation import get_symbol_info, validate_side, validate_qty, validate_price, validate_notional


def place_limit_order(client, symbol: str, side: str, quantity: float, price: float, time_in_force: str = "GTC") -> Dict[str, Any]:
    """Place a LIMIT order on USDT-M Futures."""
    exi = client.exchange_info()
    si = get_symbol_info(exi, symbol)
    if not si:
        raise ValueError(f"symbol {symbol} not found in exchangeInfo")

    validate_side(side)
    qty = validate_qty(si, quantity)
    p = validate_price(si, price)
    validate_notional(si, p, qty)

    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": time_in_force,
        "quantity": str(qty),
        "price": str(p),
    }
    return client.place_order(params)