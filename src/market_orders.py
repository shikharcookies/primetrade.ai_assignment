from typing import Any, Dict

from src.common.validation import get_symbol_info, validate_side, validate_qty, validate_notional


def place_market_order(client, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """Place a MARKET order on USDT-M Futures."""
    exi = client.exchange_info()
    si = get_symbol_info(exi, symbol)
    if not si:
        raise ValueError(f"symbol {symbol} not found in exchangeInfo")

    validate_side(side)
    qty = validate_qty(si, quantity)

    # For MARKET orders, notional check is best-effort (requires current price). Skipped here.
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": str(qty),
    }
    return client.place_order(params)