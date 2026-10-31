CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(40) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_start DATETIME(6) NOT NULL,
    session_end DATETIME(6) NOT NULL,
    event_count INT NOT NULL,
    duration_seconds BIGINT NOT NULL,
    first_event_id VARCHAR(255) NOT NULL,
    last_event_id VARCHAR(255) NOT NULL,
    INDEX idx_sessions_user_start (user_id, session_start)
);

CREATE TABLE IF NOT EXISTS session_events (
    event_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_timestamp DATETIME(6) NOT NULL,
    session_id VARCHAR(40) NOT NULL,
    source_file VARCHAR(255),
    source_row_number INT,
    CONSTRAINT fk_session_events_session
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    INDEX idx_session_events_user_time (user_id, event_timestamp)
);
