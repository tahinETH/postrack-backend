import sqlite3
from typing import Any


class BaseRepository:
    def __init__(self, conn: sqlite3.Connection):
        if not isinstance(conn, sqlite3.Connection):
            raise TypeError(f"Expected sqlite3.Connection, got {type(conn)}")
        self.conn = conn
        
    def _commit(self):
        """Helper method to commit transactions"""
        self.conn.commit()