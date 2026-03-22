from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MarketStructureSnapshot:
    product_code: str
    timeframe: str
    captured_at: datetime
    bias: str | None
    last_bos: str | None
    last_choch: str | None
    swing_high: float | None
    swing_low: float | None
    premium_discount_state: str | None
    note_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TradeSignal:
    product_code: str
    timeframe: str
    signal_type: str
    direction: str | None
    score: float | None
    detected_at: datetime
    status: str | None
    reason_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReviewSummary:
    product_code: str
    period_start: datetime
    period_end: datetime
    total_trades: int
    win_trades: int
    lose_trades: int
    gross_pnl: float
    average_pnl: float
    max_win: float | None
    max_loss: float | None


@dataclass(slots=True)
class RiskStatus:
    product_code: str
    daily_pnl: float
    weekly_pnl: float
    consecutive_losses: int
    abnormal_error_count: int
    warning_messages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ZoneSummary:
    product_code: str
    timeframe: str
    active_zones: list[dict[str, Any]] = field(default_factory=list)
