from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.engine import Engine
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extensions import connection as PGConnection
from .schemas import (
    Base
)
from config import config

async def create_async_db_engine(db_url: str):
    # Convert the URL to async format if needed
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(
        db_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    
    return engine

async def get_async_session():
    """Create a session factory for async operations"""
    load_dotenv()
    
    engine = await create_async_db_engine(config.DB_PATH)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    # Return the session instance instead of the sessionmaker
    return async_session()

def connect(db_url: str, use_async: bool = False) -> Engine:
    if use_async:
        return create_async_db_engine(db_url)
    return create_engine(db_url)

def migrations():
    metadata = Base.metadata

    return [
        # Create tables
        lambda conn: metadata.create_all(conn),

        # Create indexes
        """CREATE INDEX IF NOT EXISTS idx_tweet_details ON tweet_details (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_tweet_comments ON tweet_comments (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_tweet_retweeters ON tweet_retweeters (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_monitored_accounts ON monitored_accounts (account_id, screen_name)""",
        """CREATE INDEX IF NOT EXISTS idx_ai_analysis ON ai_analysis (tweet_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_users ON users (id, email)""",
        """CREATE INDEX IF NOT EXISTS idx_user_tracked_items ON user_tracked_items (user_id, tracked_type, tracked_id)"""
    ]

def connect_and_migrate(db_url: str):
    engine = connect(db_url)
    with engine.begin() as conn:
        for cmd in migrations():
            if callable(cmd):
                cmd(conn)
            else:
                conn.execute(text(cmd))
    return engine