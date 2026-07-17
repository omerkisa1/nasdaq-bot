CREATE TABLE trade_cards (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    direction VARCHAR(5) DEFAULT 'long',
    status VARCHAR(15) NOT NULL DEFAULT 'ACTIVE',
    -- ACTIVE | TARGET_HIT | STOP_HIT | EXPIRED | NO_FILL | CANCELLED
    entry_zone_low DECIMAL(10,4) NOT NULL,
    entry_zone_high DECIMAL(10,4) NOT NULL,
    stop DECIMAL(10,4) NOT NULL,
    target_1 DECIMAL(10,4) NOT NULL,
    target_2 DECIMAL(10,4) NOT NULL,
    t1_hit BOOLEAN DEFAULT FALSE,
    horizon VARCHAR(5) NOT NULL,          -- 30m | 2h | 1d | 2d | 3d
    expires_at TIMESTAMPTZ NOT NULL,      -- created_at + horizon (piyasa saatleri hesaba katılır)
    confidence DECIMAL(3,2),
    position_size INTEGER,
    risk_amount DECIMAL(10,2),
    reasoning TEXT,
    invalidation TEXT,
    catalyst TEXT,
    news_context JSONB,
    snapshot JSONB,                        -- Üretim anındaki fiyat/hacim/seviye verileri
    price_at_creation DECIMAL(10,4),
    resolved_price DECIMAL(10,4),
    realized_r DECIMAL(6,2),               -- Sonuç R cinsinden: +1.5R, -1.0R vb.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX idx_cards_status ON trade_cards(status, created_at DESC);
CREATE INDEX idx_cards_symbol ON trade_cards(symbol, created_at DESC);

CREATE TABLE scan_runs (
    id SERIAL PRIMARY KEY,
    universe_size INTEGER,
    prefiltered_count INTEGER,
    gemini_calls INTEGER,
    cards_created INTEGER,
    cards_rejected INTEGER,
    duration_ms INTEGER,
    ran_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE system_settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO system_settings (key, value) VALUES
    ('account_size', '1000'),
    ('risk_percent', '1.0'),
    ('max_active_cards', '5'),
    ('paper_mode', 'true'),
    ('min_confidence', '0.5'),
    ('scan_enabled', 'true');
