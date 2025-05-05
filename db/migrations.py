from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .schemas import Base
from config import config
from typing import AsyncGenerator

# Create and store engine once at import time
if not config.DB_PATH.startswith("postgresql+asyncpg://"):
    db_url = config.DB_PATH.replace("postgresql://", "postgresql+asyncpg://")
else:
    db_url = config.DB_PATH

engine = create_async_engine(
    db_url,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create a single global sessionmaker
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Use the global sessionmaker to get a session, and close it properly."""
    async with AsyncSessionLocal() as session:
        yield session

def migrations():
    metadata = Base.metadata

    return [
        # Create tables
        lambda conn: metadata.create_all(conn),

        # Drop old tables
        """DROP TABLE IF EXISTS reply_and_quote""",
        """DROP TABLE IF EXISTS refinements""", 
        """DROP TABLE IF EXISTS inspirations""",
        """DROP TABLE IF EXISTS visualizations""",

        # Create indexes
        """CREATE INDEX IF NOT EXISTS idx_tweet_details ON tweet_details (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_tweet_comments ON tweet_comments (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_tweet_retweeters ON tweet_retweeters (tweet_id, captured_at)""",
        """CREATE INDEX IF NOT EXISTS idx_monitored_accounts ON monitored_accounts (account_id, screen_name)""",
        """CREATE INDEX IF NOT EXISTS idx_ai_analysis ON ai_analysis (tweet_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_users ON users (id, email)""",
        """CREATE INDEX IF NOT EXISTS idx_user_tracked_items ON user_tracked_items (user_id, tracked_type, tracked_id)""",
        """CREATE INDEX IF NOT EXISTS idx_account_analysis ON account_analysis (account_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_workshop_refinements ON workshop_refinements (user_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_workshop_generation ON workshop_generation (user_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_workshop_reply ON workshop_reply (user_id, created_at)""",
        """CREATE INDEX IF NOT EXISTS idx_workshop_visualization ON workshop_visualization (user_id, created_at)""",
        
        # Add style_analysis column to account_analysis table if it doesn't exist
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='account_analysis' AND column_name='style_analysis'
            ) THEN
                ALTER TABLE account_analysis ADD COLUMN style_analysis JSONB;
            END IF;
        END $$;""",

        # Add status column if it doesn't exist
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='account_analysis' AND column_name='status'
            ) THEN
                ALTER TABLE account_analysis ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completed';
            END IF;
        END $$;""",

        # Add error column if it doesn't exist
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='account_analysis' AND column_name='error'
            ) THEN
                ALTER TABLE account_analysis ADD COLUMN error TEXT;
            END IF;
        END $$;""",

        # Update existing rows to have a status if they don't
        """UPDATE account_analysis SET status = 'completed' WHERE status IS NULL;""",

        # Add status column to community_analysis if it doesn't exist
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='community_analysis' AND column_name='status'
            ) THEN
                ALTER TABLE community_analysis ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completed';
            END IF;
        END $$;""",

        # Add error column to community_analysis if it doesn't exist
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='community_analysis' AND column_name='error'
            ) THEN
                ALTER TABLE community_analysis ADD COLUMN error TEXT;
            END IF;
        END $$;""",

        # Update existing rows to have a status if they don't
        """UPDATE community_analysis SET status = 'completed' WHERE status IS NULL;"""
    ]

async def connect_and_migrate(db_url: str):
    # Ensure we have an async URL
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url)
    
    # Use async context manager; note: run synchronous functions via run_sync
    async with engine.begin() as conn:
        for cmd in migrations():
            if callable(cmd):
                # Use run_sync to run synchronous migration functions
                await conn.run_sync(cmd)
            else:
                await conn.execute(text(cmd))
    return engine