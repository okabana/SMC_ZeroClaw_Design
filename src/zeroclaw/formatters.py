from __future__ import annotations

from .models import MarketStructureSnapshot, ReviewSummary, RiskStatus, TradeSignal, ZoneSummary


def _fmt_price(value: float | None) -> str:
    return f"{value:,.0f}" if value is not None else "データ不足"


def format_market_summary(snapshot: MarketStructureSnapshot) -> str:
    notes = snapshot.note_json or {}
    watch_points = notes.get("watch_points", [])
    missing = notes.get("missing_conditions", [])
    reasons = [
        f"- 上位足バイアス: {snapshot.bias or 'データ不足'}",
        f"- 直近 BOS: {snapshot.last_bos or 'データ不足'}",
        f"- 直近 CHoCH: {snapshot.last_choch or '未確認'}",
        f"- swing high / low: {_fmt_price(snapshot.swing_high)} / {_fmt_price(snapshot.swing_low)}",
        f"- premium / discount: {snapshot.premium_discount_state or 'データ不足'}",
    ]
    watch_block = "\n".join(f"- {point}" for point in watch_points) if watch_points else "- 監視ポイントは未登録"
    missing_block = "\n".join(f"- {item}" for item in missing) if missing else "- 未充足条件は未登録"
    conclusion = f"{snapshot.timeframe} は {snapshot.bias or 'データ不足'}。直近 BOS は {snapshot.last_bos or '不明'}。"
    return (
        f"結論:\n{conclusion}\n\n"
        f"根拠:\n" + "\n".join(reasons) + "\n\n"
        f"未充足条件:\n{missing_block}\n\n"
        f"監視ポイント:\n{watch_block}"
    )


def format_signal_summary(signal: TradeSignal) -> str:
    reasons = signal.reason_json or {}
    met = reasons.get("met_conditions", [])
    missing = reasons.get("missing_conditions", [])
    rationale = "\n".join(f"- {item}" for item in met) if met else "- 根拠データ不足"
    missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- 未充足条件なし"
    return (
        f"候補:\n{signal.direction or '方向不明'} {signal.signal_type} を監視\n\n"
        f"理由:\n{rationale}\n\n"
        f"不足:\n{missing_text}\n\n"
        f"注意:\n- status: {signal.status or '不明'}\n- score: {signal.score if signal.score is not None else 'データ不足'}"
    )


def format_review_summary(review: ReviewSummary) -> str:
    win_rate = (review.win_trades / review.total_trades * 100) if review.total_trades else 0.0
    return (
        "総評:\n"
        f"{review.product_code} の対象期間は {review.total_trades} トレード、損益は {review.gross_pnl:,.0f}。\n\n"
        "良かった点:\n"
        f"- 勝率 {win_rate:.1f}%\n"
        f"- 最大利益 {review.max_win if review.max_win is not None else 'データ不足'}\n\n"
        "問題点:\n"
        f"- 負けトレード数 {review.lose_trades}\n"
        f"- 最大損失 {review.max_loss if review.max_loss is not None else 'データ不足'}\n\n"
        "改善:\n"
        f"- 平均損益 {review.average_pnl:,.0f} を基準に RR を再点検"
    )


def format_risk_status(risk: RiskStatus) -> str:
    warnings = "\n".join(f"- {item}" for item in risk.warning_messages) if risk.warning_messages else "- 重大な警告はありません"
    return (
        f"結論:\n{risk.product_code} のリスク状態を確認しました。\n\n"
        f"根拠:\n- 日次損益: {risk.daily_pnl:,.0f}\n- 週次損益: {risk.weekly_pnl:,.0f}\n"
        f"- 連敗回数: {risk.consecutive_losses}\n- 異常件数: {risk.abnormal_error_count}\n\n"
        f"監視ポイント:\n{warnings}"
    )


def format_zone_summary(zones: ZoneSummary) -> str:
    if not zones.active_zones:
        zone_lines = "- アクティブ zone はありません"
    else:
        zone_lines = "\n".join(
            f"- {zone['zone_type']}: {zone['price_from']:,.0f} - {zone['price_to']:,.0f} (strength {zone['strength_score']})"
            for zone in zones.active_zones
        )
    return (
        f"結論:\n{zones.product_code} {zones.timeframe} の主要 zone 一覧です。\n\n"
        f"根拠:\n{zone_lines}"
    )
