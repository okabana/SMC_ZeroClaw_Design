from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from .models import MarketStructureSnapshot, ReviewSummary, RiskStatus, TradeSignal, ZoneSummary


class DatabaseClient:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "psycopg is required for database access. Install with `pip install .[postgres]`."
            ) from exc
        return psycopg.connect(self.dsn)

    def latest_bias(self, product_code: str, timeframe: str) -> MarketStructureSnapshot:
        query = """
            SELECT product_code, timeframe, captured_at, bias, last_bos, last_choch,
                   swing_high, swing_low, premium_discount_state, COALESCE(note_json, '{}'::jsonb)
            FROM market_structure_snapshots
            WHERE product_code = %s AND timeframe = %s
            ORDER BY captured_at DESC
            LIMIT 1
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (product_code, timeframe))
            row = cur.fetchone()
        if row is None:
            raise LookupError(f"market_structure_snapshots not found for {product_code} {timeframe}")
        return MarketStructureSnapshot(*row)

    def latest_signal(self, product_code: str, timeframe: str) -> TradeSignal:
        query = """
            SELECT product_code, timeframe, signal_type, direction, score, detected_at, status,
                   COALESCE(reason_json, '{}'::jsonb)
            FROM trade_signals
            WHERE product_code = %s AND timeframe = %s
            ORDER BY detected_at DESC
            LIMIT 1
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (product_code, timeframe))
            row = cur.fetchone()
        if row is None:
            raise LookupError(f"trade_signals not found for {product_code} {timeframe}")
        return TradeSignal(*row)

    def daily_review(self, product_code: str, review_date: datetime) -> ReviewSummary:
        start = datetime(review_date.year, review_date.month, review_date.day)
        end = start + timedelta(days=1)
        query = """
            SELECT
                product_code,
                %s AS period_start,
                %s AS period_end,
                COUNT(*) AS total_trades,
                COUNT(*) FILTER (WHERE side = 'BUY') AS win_trades,
                COUNT(*) FILTER (WHERE side = 'SELL') AS lose_trades,
                COALESCE(SUM(price * size * CASE WHEN side = 'BUY' THEN 1 ELSE -1 END), 0) AS gross_pnl,
                COALESCE(AVG(price * size * CASE WHEN side = 'BUY' THEN 1 ELSE -1 END), 0) AS average_pnl,
                MAX(price * size) AS max_win,
                MIN(price * size * -1) AS max_loss
            FROM multi_asset_executions
            WHERE product_code = %s
              AND exec_date >= %s
              AND exec_date < %s
            GROUP BY product_code
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (start, end, product_code, start, end))
            row = cur.fetchone()
        if row is None:
            return ReviewSummary(product_code, start, end, 0, 0, 0, 0.0, 0.0, None, None)
        return ReviewSummary(*row)

    def risk_status(self, product_code: str) -> RiskStatus:
        now = datetime.now(UTC).replace(tzinfo=None)
        start_day = datetime(now.year, now.month, now.day)
        start_week = start_day - timedelta(days=start_day.weekday())
        query = """
            WITH trade_stats AS (
                SELECT
                    product_code,
                    COALESCE(SUM(price * size * CASE WHEN exec_date >= %s THEN CASE WHEN side = 'BUY' THEN 1 ELSE -1 END ELSE 0 END), 0) AS daily_pnl,
                    COALESCE(SUM(price * size * CASE WHEN exec_date >= %s THEN CASE WHEN side = 'BUY' THEN 1 ELSE -1 END ELSE 0 END), 0) AS weekly_pnl,
                    COUNT(*) FILTER (WHERE side = 'SELL' AND exec_date >= %s) AS consecutive_losses
                FROM multi_asset_executions
                WHERE product_code = %s
                GROUP BY product_code
            ),
            error_stats AS (
                SELECT COALESCE(COUNT(*), 0) AS abnormal_error_count
                FROM notifications
                WHERE category = 'system_error'
                  AND severity IN ('warning', 'critical')
                  AND sent_at >= %s
            )
            SELECT
                t.product_code,
                t.daily_pnl,
                t.weekly_pnl,
                t.consecutive_losses,
                e.abnormal_error_count
            FROM trade_stats t
            CROSS JOIN error_stats e
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (start_day, start_week, start_day, product_code, start_day))
            row = cur.fetchone()
        if row is None:
            return RiskStatus(product_code, 0.0, 0.0, 0, 0, ["対象データがありません"])
        risk = RiskStatus(*row)
        if risk.daily_pnl < 0:
            risk.warning_messages.append("日次損益がマイナスです")
        if risk.consecutive_losses >= 3:
            risk.warning_messages.append("連敗回数が閾値に近づいています")
        if risk.abnormal_error_count > 0:
            risk.warning_messages.append("system_error 通知が発生しています")
        return risk

    def zone_summary(self, product_code: str, timeframe: str) -> ZoneSummary:
        query = """
            SELECT zone_type, price_from, price_to, strength_score
            FROM smc_zones
            WHERE product_code = %s AND timeframe = %s AND is_active = TRUE
            ORDER BY strength_score DESC, created_at DESC
            LIMIT 10
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (product_code, timeframe))
            rows = cur.fetchall()
        return ZoneSummary(
            product_code=product_code,
            timeframe=timeframe,
            active_zones=[
                {
                    "zone_type": zone_type,
                    "price_from": price_from,
                    "price_to": price_to,
                    "strength_score": strength_score,
                }
                for zone_type, price_from, price_to, strength_score in rows
            ],
        )


def parse_review_date(raw: str | None) -> datetime:
    if raw is None:
        now = datetime.now(UTC).replace(tzinfo=None)
        return datetime(now.year, now.month, now.day)
    return datetime.fromisoformat(raw)


def command_output(client: DatabaseClient, command: str, product_code: str, timeframe: str, review_date: str | None = None) -> str:
    from .formatters import (
        format_market_summary,
        format_review_summary,
        format_risk_status,
        format_signal_summary,
        format_zone_summary,
    )

    if command == "latest_bias":
        return format_market_summary(client.latest_bias(product_code, timeframe))
    if command == "latest_signal":
        return format_signal_summary(client.latest_signal(product_code, timeframe))
    if command == "daily_review":
        return format_review_summary(client.daily_review(product_code, parse_review_date(review_date)))
    if command == "risk_status":
        return format_risk_status(client.risk_status(product_code))
    if command == "zone_summary":
        return format_zone_summary(client.zone_summary(product_code, timeframe))
    raise ValueError(f"Unsupported command: {command}")
