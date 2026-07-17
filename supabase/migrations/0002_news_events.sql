CREATE TABLE news_events (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    external_id VARCHAR(50) NOT NULL,
    headline TEXT,
    description TEXT,
    source VARCHAR(50),
    url TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    reaction VARCHAR(20) DEFAULT 'pending',  -- pending | confirmed | no_reaction
    price_at_detection DECIMAL(10,4),
    price_change_pct DECIMAL(6,2),
    card_id INTEGER REFERENCES trade_cards(id),
    UNIQUE(symbol, external_id)
);
CREATE INDEX idx_news_events_symbol ON news_events(symbol, detected_at DESC);

ALTER TABLE trade_cards ADD COLUMN trigger_source VARCHAR(10) DEFAULT 'scan';
-- 'scan' | 'news' | 'manual'
CREATE INDEX idx_cards_trigger_source ON trade_cards(trigger_source);
