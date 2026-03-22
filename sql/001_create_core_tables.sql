BEGIN;

CREATE TABLE IF NOT EXISTS multi_asset_executions (
    id BIGSERIAL PRIMARY KEY,
    product_code TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    price NUMERIC(18, 8) NOT NULL CHECK (price > 0),
    size NUMERIC(18, 8) NOT NULL CHECK (size > 0),
    exec_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_multi_asset_executions_product_exec_date
    ON multi_asset_executions (product_code, exec_date DESC);

CREATE TABLE IF NOT EXISTS market_structure_snapshots (
    id BIGSERIAL PRIMARY KEY,
    product_code TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    bias TEXT CHECK (bias IN ('bullish', 'bearish', 'neutral')),
    last_bos TEXT CHECK (last_bos IN ('up', 'down')),
    last_choch TEXT CHECK (last_choch IN ('up', 'down')),
    swing_high NUMERIC(18, 8),
    swing_low NUMERIC(18, 8),
    premium_discount_state TEXT CHECK (premium_discount_state IN ('premium', 'discount', 'equilibrium')),
    note_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_market_structure_swings
        CHECK (swing_high IS NULL OR swing_low IS NULL OR swing_high >= swing_low)
);

CREATE INDEX IF NOT EXISTS idx_market_structure_snapshots_lookup
    ON market_structure_snapshots (product_code, timeframe, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_structure_snapshots_note_json_gin
    ON market_structure_snapshots USING GIN (note_json);

CREATE TABLE IF NOT EXISTS smc_zones (
    id BIGSERIAL PRIMARY KEY,
    product_code TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    price_from NUMERIC(18, 8) NOT NULL,
    price_to NUMERIC(18, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    strength_score NUMERIC(6, 4) NOT NULL DEFAULT 0 CHECK (strength_score >= 0 AND strength_score <= 1),
    meta_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT chk_smc_zones_price_range CHECK (price_to >= price_from)
);

CREATE INDEX IF NOT EXISTS idx_smc_zones_lookup
    ON smc_zones (product_code, timeframe, is_active, strength_score DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_smc_zones_meta_json_gin
    ON smc_zones USING GIN (meta_json);

CREATE TABLE IF NOT EXISTS trade_signals (
    id BIGSERIAL PRIMARY KEY,
    product_code TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    direction TEXT CHECK (direction IN ('long', 'short', 'neutral')),
    score NUMERIC(6, 4) CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
    detected_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    reason_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_signals_lookup
    ON trade_signals (product_code, timeframe, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_trade_signals_reason_json_gin
    ON trade_signals USING GIN (reason_json);

CREATE TABLE IF NOT EXISTS trade_reviews (
    id BIGSERIAL PRIMARY KEY,
    review_date DATE NOT NULL,
    product_code TEXT NOT NULL,
    period_type TEXT NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    summary TEXT NOT NULL,
    good_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    bad_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    violations JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_trade_reviews UNIQUE (review_date, product_code, period_type)
);

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    category TEXT NOT NULL CHECK (
        category IN (
            'structure_update',
            'entry_candidate',
            'entry_blocked',
            'risk_warning',
            'drawdown_alert',
            'execution_result',
            'daily_review',
            'weekly_review',
            'system_error'
        )
    ),
    message TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    related_signal_id BIGINT REFERENCES trade_signals (id) ON DELETE SET NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_notifications_category_sent_at
    ON notifications (category, sent_at DESC);

COMMIT;
