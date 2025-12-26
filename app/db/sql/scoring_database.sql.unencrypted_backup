-- =================================================================
-- PLAYER SCORING SYSTEM - DATABASE SCHEMA
-- =================================================================

-- Player Scores Table (stores calculated scores)
CREATE TABLE player_scores (
    id BIGSERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_year INTEGER NOT NULL,
    timeframe VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'season'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Overall Score
    overall_score DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    
    -- Category Scores
    scoring_score DECIMAL(5,2) NOT NULL,
    efficiency_score DECIMAL(5,2) NOT NULL,
    playmaking_score DECIMAL(5,2) NOT NULL,
    defense_score DECIMAL(5,2) NOT NULL,
    rebounding_score DECIMAL(5,2) NOT NULL,
    consistency_score DECIMAL(5,2) NOT NULL,
    
    -- Percentile Rankings
    overall_percentile DECIMAL(5,2),
    scoring_percentile DECIMAL(5,2),
    efficiency_percentile DECIMAL(5,2),
    playmaking_percentile DECIMAL(5,2),
    defense_percentile DECIMAL(5,2),
    rebounding_percentile DECIMAL(5,2),
    
    -- Trend Analysis
    trend_direction VARCHAR(10), -- 'up', 'down', 'stable'
    trend_strength DECIMAL(5,2), -- -10 to +10
    previous_score DECIMAL(5,2),
    score_change DECIMAL(5,2),
    
    -- Metadata
    games_included INTEGER NOT NULL,
    minutes_avg DECIMAL(5,2),
    calculation_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT unique_player_period UNIQUE (player_id, timeframe, period_start, period_end)
);

CREATE INDEX idx_player_scores_player ON player_scores(player_id);
CREATE INDEX idx_player_scores_season ON player_scores(season_year);
CREATE INDEX idx_player_scores_timeframe ON player_scores(timeframe);
CREATE INDEX idx_player_scores_overall ON player_scores(overall_score DESC);
CREATE INDEX idx_player_scores_created ON player_scores(created_at DESC);
CREATE INDEX idx_player_scores_composite ON player_scores(player_id, season_year, timeframe);

-- Score History (for trend analysis)
CREATE TABLE score_history (
    id BIGSERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    score_date DATE NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    games_played INTEGER NOT NULL,
    
    -- Quick access to key metrics
    points_avg DECIMAL(5,2),
    rebounds_avg DECIMAL(5,2),
    assists_avg DECIMAL(5,2),
    ts_percentage DECIMAL(5,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_player_date UNIQUE (player_id, score_date)
);

CREATE INDEX idx_score_history_player ON score_history(player_id);
CREATE INDEX idx_score_history_date ON score_history(score_date DESC);

-- Performance Alerts
CREATE TABLE performance_alerts (
    id BIGSERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    alert_type VARCHAR(20) NOT NULL, -- 'positive', 'negative', 'warning', 'neutral'
    severity VARCHAR(10) NOT NULL, -- 'high', 'medium', 'low'
    category VARCHAR(50) NOT NULL, -- 'scoring', 'efficiency', 'minutes', etc.
    
    message TEXT NOT NULL,
    metric_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    
    alert_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    acknowledged_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_player ON performance_alerts(player_id);
CREATE INDEX idx_alerts_active ON performance_alerts(is_active, alert_date DESC);
CREATE INDEX idx_alerts_type ON performance_alerts(alert_type, severity);

-- Scoring Configuration (for adjustable weights)
CREATE TABLE scoring_config (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT FALSE,
    
    -- Category weights
    weight_scoring DECIMAL(4,3) NOT NULL,
    weight_efficiency DECIMAL(4,3) NOT NULL,
    weight_playmaking DECIMAL(4,3) NOT NULL,
    weight_defense DECIMAL(4,3) NOT NULL,
    weight_rebounding DECIMAL(4,3) NOT NULL,
    weight_consistency DECIMAL(4,3) NOT NULL,
    
    -- Position adjustments (JSON)
    position_adjustments JSONB,
    
    -- Configuration metadata
    description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    
    CONSTRAINT weights_sum_check CHECK (
        weight_scoring + weight_efficiency + weight_playmaking + 
        weight_defense + weight_rebounding + weight_consistency = 1.000
    )
);

-- Insert default configuration
INSERT INTO scoring_config (
    version, is_active,
    weight_scoring, weight_efficiency, weight_playmaking,
    weight_defense, weight_rebounding, weight_consistency,
    position_adjustments,
    description
) VALUES (
    'v1.0', TRUE,
    0.250, 0.200, 0.150, 0.150, 0.100, 0.150,
    '{
        "PG": {"playmaking": 1.2, "scoring": 0.9, "rebounding": 0.7},
        "SG": {"scoring": 1.1, "playmaking": 0.9, "defense": 1.0},
        "SF": {"scoring": 1.0, "defense": 1.1, "rebounding": 0.9},
        "PF": {"rebounding": 1.2, "defense": 1.1, "scoring": 0.9},
        "C": {"rebounding": 1.3, "defense": 1.2, "playmaking": 0.7}
    }'::jsonb,
    'Default balanced scoring configuration'
);

-- =================================================================
-- VIEWS FOR EASY QUERYING
-- =================================================================

-- Current Player Scores (latest weekly scores)
CREATE VIEW current_player_scores AS
SELECT 
    ps.*,
    p.name,
    p.position,
    p.team_id,
    t.abbreviation as team
FROM player_scores ps
JOIN players p ON ps.player_id = p.id
JOIN teams t ON p.team_id = t.id
WHERE ps.timeframe = 'weekly'
AND ps.period_end = (
    SELECT MAX(period_end) 
    FROM player_scores 
    WHERE player_id = ps.player_id 
    AND timeframe = 'weekly'
);

-- Top Performers (by overall score)
CREATE VIEW top_performers AS
SELECT 
    player_id,
    name,
    position,
    team,
    overall_score,
    trend_direction,
    score_change,
    overall_percentile
FROM current_player_scores
ORDER BY overall_score DESC
LIMIT 50;

-- Trending Players
CREATE VIEW trending_players AS
SELECT 
    player_id,
    name,
    position,
    team,
    overall_score,
    trend_direction,
    trend_strength,
    score_change,
    CASE 
        WHEN trend_direction = 'up' AND score_change > 5 THEN 'hot'
        WHEN trend_direction = 'down' AND score_change < -5 THEN 'cold'
        ELSE 'neutral'
    END as trend_status
FROM current_player_scores
WHERE trend_direction IN ('up', 'down')
ORDER BY ABS(score_change) DESC;

-- Category Leaders
CREATE VIEW category_leaders AS
SELECT 
    'scoring' as category,
    player_id,
    name,
    position,
    team,
    scoring_score as score
FROM current_player_scores
WHERE scoring_score IS NOT NULL
ORDER BY scoring_score DESC
LIMIT 10

UNION ALL

SELECT 
    'efficiency' as category,
    player_id,
    name,
    position,
    team,
    efficiency_score as score
FROM current_player_scores
WHERE efficiency_score IS NOT NULL
ORDER BY efficiency_score DESC
LIMIT 10

UNION ALL

SELECT 
    'playmaking' as category,
    player_id,
    name,
    position,
    team,
    playmaking_score as score
FROM current_player_scores
WHERE playmaking_score IS NOT NULL
ORDER BY playmaking_score DESC
LIMIT 10;

-- =================================================================
-- STORED PROCEDURES
-- =================================================================

-- Calculate and store player score
CREATE OR REPLACE FUNCTION calculate_player_score(
    p_player_id INTEGER,
    p_timeframe VARCHAR(20),
    p_period_start DATE,
    p_period_end DATE
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    v_score DECIMAL(5,2);
    v_config_id INTEGER;
BEGIN
    -- Get active configuration
    SELECT id INTO v_config_id 
    FROM scoring_config 
    WHERE is_active = TRUE 
    LIMIT 1;
    
    -- This would call the Python scoring engine
    -- For now, we'll use a placeholder
    v_score := 85.0;
    
    -- Insert or update score
    INSERT INTO player_scores (
        player_id, season_year, timeframe,
        period_start, period_end,
        overall_score, confidence_score,
        scoring_score, efficiency_score, playmaking_score,
        defense_score, rebounding_score, consistency_score,
        games_included, calculation_version
    ) VALUES (
        p_player_id, EXTRACT(YEAR FROM p_period_end), p_timeframe,
        p_period_start, p_period_end,
        v_score, 0.85,
        80, 85, 90, 75, 80, 88,
        10, 'v1.0'
    )
    ON CONFLICT (player_id, timeframe, period_start, period_end)
    DO UPDATE SET
        overall_score = EXCLUDED.overall_score,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Batch calculate scores for all active players
CREATE OR REPLACE FUNCTION batch_calculate_scores(
    p_timeframe VARCHAR(20),
    p_period_start DATE,
    p_period_end DATE
) RETURNS TABLE (
    player_id INTEGER,
    player_name VARCHAR(100),
    score DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        calculate_player_score(p.id, p_timeframe, p_period_start, p_period_end)
    FROM players p
    WHERE p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Generate performance alerts
CREATE OR REPLACE FUNCTION generate_performance_alerts(
    p_player_id INTEGER,
    p_current_score DECIMAL(5,2),
    p_previous_score DECIMAL(5,2)
) RETURNS VOID AS $$
DECLARE
    v_score_change DECIMAL(5,2);
BEGIN
    v_score_change := p_current_score - p_previous_score;
    
    -- Significant improvement
    IF v_score_change > 5 THEN
        INSERT INTO performance_alerts (
            player_id, alert_type, severity, category,
            message, metric_value, threshold_value, alert_date
        ) VALUES (
            p_player_id, 'positive', 'high', 'overall',
            'Significant performance improvement detected',
            p_current_score, p_previous_score, CURRENT_DATE
        );
    END IF;
    
    -- Significant decline
    IF v_score_change < -5 THEN
        INSERT INTO performance_alerts (
            player_id, alert_type, severity, category,
            message, metric_value, threshold_value, alert_date
        ) VALUES (
            p_player_id, 'warning', 'high', 'overall',
            'Significant performance decline detected',
            p_current_score, p_previous_score, CURRENT_DATE
        );
    END IF;
    
    -- Elite performance
    IF p_current_score >= 95 THEN
        INSERT INTO performance_alerts (
            player_id, alert_type, severity, category,
            message, metric_value, threshold_value, alert_date
        ) VALUES (
            p_player_id, 'positive', 'high', 'overall',
            'Elite performance - Top 5% league-wide',
            p_current_score, 95, CURRENT_DATE
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- QUERIES FOR API ENDPOINTS
-- =================================================================

-- Get player score with history
-- SELECT * FROM get_player_score_with_history(123, 'weekly', 4);
CREATE OR REPLACE FUNCTION get_player_score_with_history(
    p_player_id INTEGER,
    p_timeframe VARCHAR(20),
    p_periods INTEGER DEFAULT 4
) RETURNS TABLE (
    period_end DATE,
    overall_score DECIMAL(5,2),
    trend_direction VARCHAR(10),
    categories JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ps.period_end,
        ps.overall_score,
        ps.trend_direction,
        jsonb_build_object(
            'scoring', ps.scoring_score,
            'efficiency', ps.efficiency_score,
            'playmaking', ps.playmaking_score,
            'defense', ps.defense_score,
            'rebounding', ps.rebounding_score,
            'consistency', ps.consistency_score
        ) as categories
    FROM player_scores ps
    WHERE ps.player_id = p_player_id
    AND ps.timeframe = p_timeframe
    ORDER BY ps.period_end DESC
    LIMIT p_periods;
END;
$$ LANGUAGE plpgsql;

-- Get active alerts for player
CREATE OR REPLACE FUNCTION get_player_alerts(
    p_player_id INTEGER,
    p_days_back INTEGER DEFAULT 7
) RETURNS TABLE (
    alert_type VARCHAR(20),
    severity VARCHAR(10),
    message TEXT,
    alert_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pa.alert_type,
        pa.severity,
        pa.message,
        pa.alert_date
    FROM performance_alerts pa
    WHERE pa.player_id = p_player_id
    AND pa.is_active = TRUE
    AND pa.alert_date >= CURRENT_DATE - p_days_back
    ORDER BY pa.alert_date DESC, pa.severity DESC;
END;
$$ LANGUAGE plpgsql;