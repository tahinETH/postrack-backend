import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA trusted_schema = OFF")
    conn.execute("PRAGMA sqlite_check_constraints = ON")
    conn.execute("PRAGMA trusted_schema = ON")
    return conn

def migrations():
    return [
        """CREATE TABLE IF NOT EXISTS monitored_accounts (
            account_id TEXT PRIMARY KEY,
            screen_name TEXT,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            last_check INTEGER,
            is_active BOOLEAN DEFAULT TRUE
        )""",

        """CREATE TABLE IF NOT EXISTS monitored_tweets (
            tweet_id TEXT PRIMARY KEY,
            user_screen_name TEXT,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            last_check INTEGER,
            is_active BOOLEAN DEFAULT TRUE
        )""",
        
        """CREATE TABLE IF NOT EXISTS tweet_details (
            tweet_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            captured_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (tweet_id) REFERENCES monitored_tweets(tweet_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS tweet_comments (
            comment_id TEXT PRIMARY KEY,
            tweet_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            captured_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (tweet_id) REFERENCES monitored_tweets(tweet_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS tweet_retweeters (
            user_id TEXT NOT NULL,
            tweet_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            captured_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            PRIMARY KEY (user_id, tweet_id),
            FOREIGN KEY (tweet_id) REFERENCES monitored_tweets(tweet_id)
        )""",
        
        "CREATE INDEX IF NOT EXISTS idx_tweet_details ON tweet_details (tweet_id, captured_at)",
        "CREATE INDEX IF NOT EXISTS idx_tweet_comments ON tweet_comments (tweet_id, captured_at)",
        "CREATE INDEX IF NOT EXISTS idx_tweet_retweeters ON tweet_retweeters (tweet_id, captured_at)",
        "CREATE INDEX IF NOT EXISTS idx_monitored_accounts ON monitored_accounts (account_id, screen_name)"
    ]

def connect_and_migrate(path: Path):
    conn = connect(path)
    for cmd in migrations():
        conn.execute(cmd)
    conn.commit()
    return conn