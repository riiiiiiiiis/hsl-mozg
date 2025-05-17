CREATE TABLE IF NOT EXISTS bookings (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    confirmed   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
