from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, Optional


def _d(x: Any) -> Decimal:
    return Decimal(str(x))


def get_symbol_info(exchange_info: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
    for s in exchange_info.get("symbols", []):
        if s.get("symbol") == symbol:
            return s
    return None


def _get_filter(symbol_info: Dict[str, Any], ftype: str) -> Optional[Dict[str, Any]]:
    for f in symbol_info.get("filters", []):
        if f.get("filterType") == ftype:
            return f
    return None


def round_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step == 0:
        return value
    # Quantize down to step size
    places = max(0, -step.as_tuple().exponent)
    quantized = (value // step) * step
    return quantized.quantize(Decimal(10) ** -places)


def validate_side(side: str) -> None:
    if side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")


def validate_qty(symbol_info: Dict[str, Any], quantity: float) -> Decimal:
    qty = _d(quantity)
    if qty <= 0:
        raise ValueError("quantity must be positive")
    lot = _get_filter(symbol_info, "LOT_SIZE")
    if lot:
        step = _d(lot.get("stepSize", "0"))
        min_qty = _d(lot.get("minQty", "0"))
        max_qty = _d(lot.get("maxQty", "0"))
        qty = round_to_step(qty, step)
        if qty < min_qty:
            raise ValueError(f"quantity {qty} below minQty {min_qty}")
        if max_qty > 0 and qty > max_qty:
            raise ValueError(f"quantity {qty} above maxQty {max_qty}")
    return qty


def validate_price(symbol_info: Dict[str, Any], price: float) -> Decimal:
    p = _d(price)
    if p <= 0:
        raise ValueError("price must be positive")
    pf = _get_filter(symbol_info, "PRICE_FILTER")
    if pf:
        tick = _d(pf.get("tickSize", "0"))
        min_price = _d(pf.get("minPrice", "0"))
        max_price = _d(pf.get("maxPrice", "0"))
        p = round_to_step(p, tick)
        if min_price > 0 and p < min_price:
            raise ValueError(f"price {p} below minPrice {min_price}")
        if max_price > 0 and p > max_price:
            raise ValueError(f"price {p} above maxPrice {max_price}")
    return p


def validate_notional(symbol_info: Dict[str, Any], price: Decimal, qty: Decimal) -> None:
    # Futures may expose NOTIONAL or MIN_NOTIONAL
    notional_filters = [f for f in symbol_info.get("filters", []) if f.get("filterType") in {"NOTIONAL", "MIN_NOTIONAL"}]
    if notional_filters:
        min_notional = _d(notional_filters[0].get("minNotional", "0"))
        if min_notional > 0 and (price * qty) < min_notional:
            raise ValueError(f"notional {price*qty} below minNotional {min_notional}")