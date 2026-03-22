from __future__ import annotations

import argparse

from .db import DatabaseClient, command_output


COMMANDS = ["latest_bias", "latest_signal", "daily_review", "risk_status", "zone_summary"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZeroClaw Phase 1 helper CLI")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--dsn", required=True, help="PostgreSQL DSN")
    parser.add_argument("--product-code", default="BTC_JPY")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--review-date", default=None, help="ISO8601 date for daily_review")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = DatabaseClient(args.dsn)
    print(command_output(client, args.command, args.product_code, args.timeframe, args.review_date))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
