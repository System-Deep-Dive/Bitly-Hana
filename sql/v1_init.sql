CREATE TABLE IF NOT EXISTS url_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code   TEXT NOT NULL,
    original_url TEXT NOT NULL,
    created_at   TEXT DEFAULT (datetime('now'))
);
