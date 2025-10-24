import time
from decimal import Decimal
from typing import Any, Dict, Optional

from src.common.validation import get_symbol_info, validate_side, validate_qty, validate_price


def execute_twap(
    client,
    symbol: str,
    side: str,
    total_quantity: float,
    slices: int,
    interval_sec: float,
    order_type: str = "MARKET",
    limit_price: Optional[float] = None,
) -> Dict[str, Any]:
    """Execute a simple TWAP by splitting into evenly sized slices over time.

    - MARKET: places market orders per slice
    - LIMIT: places limit orders per slice at `limit_price`
    """
    if slices <= 0:
        raise ValueError("slices must be > 0")
    if interval_sec < 0:
        raise ValueError("interval_sec must be >= 0")

    exi = client.exchange_info()
    si = get_symbol_info(exi, symbol)
    if not si:
        raise ValueError(f"symbol {symbol} not found in exchangeInfo")

    validate_side(side)
    total_qty = validate_qty(si, total_quantity)

    per_slice_qty = (total_qty / Decimal(slices)).quantize(total_qty)  # keep precision

    results = {"slices": []}
    for i in range(slices):
        if order_type == "MARKET":
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": str(per_slice_qty),
            }
        elif order_type == "LIMIT":
            if limit_price is None:
                raise ValueError("limit_price required for LIMIT TWAP")
            lp = validate_price(si, limit_price)
            params = {
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "timeInForce": "GTC",
                "quantity": str(per_slice_qty),
                "price": str(lp),
            }
        else:
            raise ValueError("order_type must be MARKET or LIMIT")

        res = client.place_order(params)
        results["slices"].append({"index": i + 1, "response": res})
        if i < slices - 1 and interval_sec > 0:
            time.sleep(interval_sec)

    return results