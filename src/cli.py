import os
import argparse
from typing import Optional

from src.binance_client import BinanceFuturesClient
from src.market_orders import place_market_order
from src.limit_orders import place_limit_order
from src.advanced.stop_limit import place_stop_limit_order
from src.advanced.twap import execute_twap
from src.advanced.oco import place_oco_order


def load_env_from_file():
    # Load environment variables from a local .env file if present
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
                # Silently ignore .env parsing errors to avoid blocking CLI
                pass
            break


def get_client(api_key: Optional[str], api_secret: Optional[str], testnet: bool, log_file_path: str) -> BinanceFuturesClient:
    api_key = api_key or os.environ.get("BINANCE_API_KEY")
    api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise SystemExit("BINANCE_API_KEY and BINANCE_API_SECRET are required (env or CLI).")
    base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
    return BinanceFuturesClient(api_key, api_secret, base_url=base_url, log_file_path=log_file_path)


def main():
    load_env_from_file()
    parser = argparse.ArgumentParser(description="CLI-based Binance USDT-M Futures Bot (Testnet by default)")
    parser.add_argument("--api-key", dest="api_key", help="Binance API key", default=None)
    parser.add_argument("--api-secret", dest="api_secret", help="Binance API secret", default=None)
    parser.add_argument("--realnet", action="store_true", help="Use realnet instead of testnet (default is testnet)")
    parser.add_argument("--log-file", dest="log_file", default="bot.log", help="Path to structured log file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Market
    sp_market = subparsers.add_parser("market", help="Place a MARKET order")
    sp_market.add_argument("--symbol", required=True, help="Trading symbol, e.g., BTCUSDT")
    sp_market.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    sp_market.add_argument("--quantity", required=True, type=float, help="Order quantity")

    # Limit
    sp_limit = subparsers.add_parser("limit", help="Place a LIMIT order")
    sp_limit.add_argument("--symbol", required=True)
    sp_limit.add_argument("--side", required=True, choices=["BUY", "SELL"])
    sp_limit.add_argument("--quantity", required=True, type=float)
    sp_limit.add_argument("--price", required=True, type=float)
    sp_limit.add_argument("--tif", default="GTC", choices=["GTC", "IOC", "FOK"], help="timeInForce")

    # Stop-Limit
    sp_sl = subparsers.add_parser("stop-limit", help="Place a STOP (stop-limit) order")
    sp_sl.add_argument("--symbol", required=True)
    sp_sl.add_argument("--side", required=True, choices=["BUY", "SELL"])
    sp_sl.add_argument("--quantity", required=True, type=float)
    sp_sl.add_argument("--price", required=True, type=float, help="Limit price")
    sp_sl.add_argument("--stop-price", required=True, type=float, help="Trigger stop price")
    sp_sl.add_argument("--tif", default="GTC", choices=["GTC", "IOC", "FOK"], help="timeInForce")

    # TWAP
    sp_twap = subparsers.add_parser("twap", help="Execute a simple TWAP strategy")
    sp_twap.add_argument("--symbol", required=True)
    sp_twap.add_argument("--side", required=True, choices=["BUY", "SELL"])
    sp_twap.add_argument("--total-quantity", required=True, type=float)
    sp_twap.add_argument("--slices", required=True, type=int)
    sp_twap.add_argument("--interval", required=True, type=float, help="Seconds between slices")
    sp_twap.add_argument("--type", default="MARKET", choices=["MARKET", "LIMIT"], help="Order type per slice")
    sp_twap.add_argument("--limit-price", type=float, default=None, help="Limit price if type=LIMIT")
    
    # OCO
    sp_oco = subparsers.add_parser("oco", help="Place an OCO (One-Cancels-the-Other) order")
    sp_oco.add_argument("--symbol", required=True, help="Trading symbol, e.g., BTCUSDT")
    sp_oco.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    sp_oco.add_argument("--quantity", required=True, type=float, help="Order quantity")
    sp_oco.add_argument("--price", required=True, type=float, help="Limit order price")
    sp_oco.add_argument("--stop-price", required=True, type=float, help="Stop trigger price")
    sp_oco.add_argument("--stop-limit-price", type=float, help="Stop-limit price (defaults to stop price if not provided)")

    args = parser.parse_args()
    client = get_client(args.api_key, args.api_secret, not args.realnet, args.log_file)

    def print_response(response, title="Order Response"):
        print("\n" + "="*50)
        print(f"{title}:")
        print("="*50)
        if isinstance(response, dict):
            for key, value in response.items():
                print(f"{key}: {value}")
        else:
            print(response)
        print("="*50 + "\n")
        # Also persist the last response to a file for easy inspection
        try:
            import json
            with open("last_response.json", "w") as f:
                json.dump({"title": title, "response": response}, f, indent=2)
        except Exception:
            pass

    if args.command == "market":
        res = place_market_order(client, args.symbol, args.side, args.quantity)
        print_response(res, "Market Order Response")
    elif args.command == "limit":
        res = place_limit_order(client, args.symbol, args.side, args.quantity, args.price, time_in_force=args.tif)
        print_response(res, "Limit Order Response")
    elif args.command == "stop-limit":
        res = place_stop_limit_order(
            client,
            args.symbol,
            args.side,
            args.quantity,
            args.price,
            args.stop_price,
            time_in_force=args.tif,
        )
        print_response(res, "Stop-Limit Order Response")
    elif args.command == "twap":
        res = execute_twap(
            client,
            args.symbol,
            args.side,
            args.total_quantity,
            args.slices,
            args.interval,
            order_type=args.type,
            limit_price=args.limit_price,
        )
        print_response(res, "TWAP Strategy Response")
    elif args.command == "oco":
        res = place_oco_order(
            client,
            args.symbol,
            args.side,
            args.quantity,
            args.price,
            args.stop_price,
            args.stop_limit_price,
        )
        print_response(res, "OCO Order Response")
    else:
        raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()