from datetime import datetime

from zeroclaw.db import command_output, parse_review_date
from zeroclaw.formatters import (
    format_market_summary,
    format_no_data,
    format_review_summary,
    format_risk_status,
    format_signal_summary,
    format_zone_summary,
)
from zeroclaw.models import MarketStructureSnapshot, ReviewSummary, RiskStatus, TradeSignal, ZoneSummary


def test_format_market_summary_includes_sections():
    snapshot = MarketStructureSnapshot(
        product_code="BTC_JPY",
        timeframe="15m",
        captured_at=datetime(2026, 3, 22, 0, 0),
        bias="bullish",
        last_bos="up",
        last_choch=None,
        swing_high=11280000,
        swing_low=11190000,
        premium_discount_state="discount",
        note_json={"watch_points": ["11218000 再接触"], "missing_conditions": ["1分足 CHoCH 未確認"]},
    )
    text = format_market_summary(snapshot)
    assert "結論:" in text
    assert "未充足条件:" in text
    assert "11218000 再接触" in text


def test_format_signal_summary_includes_met_and_missing_conditions():
    signal = TradeSignal(
        product_code="BTC_JPY",
        timeframe="15m",
        signal_type="entry_candidate",
        direction="long",
        score=0.83,
        detected_at=datetime(2026, 3, 22, 0, 0),
        status="watching",
        reason_json={
            "met_conditions": ["上位足 bullish", "sell-side sweep 済み"],
            "missing_conditions": ["1分足 CHoCH 未確認"],
        },
    )
    text = format_signal_summary(signal)
    assert "候補:" in text
    assert "上位足 bullish" in text
    assert "1分足 CHoCH 未確認" in text


def test_format_review_summary_contains_metrics():
    review = ReviewSummary("BTC_JPY", datetime(2026, 3, 22), datetime(2026, 3, 23), 4, 2, 2, 1200, 300, 800, -400)
    text = format_review_summary(review)
    assert "総評:" in text
    assert "勝率 50.0%" in text


def test_format_risk_status_shows_warnings():
    risk = RiskStatus("BTC_JPY", -1200, -3500, 3, 1, ["日次損益がマイナスです"])
    text = format_risk_status(risk)
    assert "監視ポイント:" in text
    assert "日次損益がマイナスです" in text


def test_format_zone_summary_lists_active_zones():
    summary = ZoneSummary(
        product_code="BTC_JPY",
        timeframe="15m",
        active_zones=[{"zone_type": "bullish_ob", "price_from": 11212000, "price_to": 11218000, "strength_score": 0.83}],
    )
    text = format_zone_summary(summary)
    assert "bullish_ob" in text
    assert "11,212,000" in text


def test_parse_review_date_defaults_to_midnight_today():
    parsed = parse_review_date(None)
    assert parsed.hour == 0
    assert parsed.minute == 0


def test_format_no_data_returns_user_friendly_message():
    text = format_no_data("latest_bias", "BTC_JPY", "15m")
    assert "データ不足です" in text
    assert "BTC_JPY 15m" in text


def test_command_output_returns_no_data_message_on_missing_snapshot():
    class DummyClient:
        def latest_bias(self, product_code, timeframe):
            raise LookupError(f"market_structure_snapshots not found for {product_code} {timeframe}")

    text = command_output(DummyClient(), "latest_bias", "BTC_JPY", "15m")
    assert "データ不足です" in text
    assert "latest_bias" in text
