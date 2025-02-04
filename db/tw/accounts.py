from typing import List, Dict, Any
from db.base import BaseRepository


class AccountRepository(BaseRepository):
    def add_monitored_account(self, account_id: str, screen_name: str):
        self.conn.execute(
            """INSERT INTO monitored_accounts (account_id, screen_name) 
               VALUES (?, ?)
               ON CONFLICT(account_id) 
               DO UPDATE SET screen_name = excluded.screen_name, 
                           is_active = TRUE,
                           last_check = strftime('%s', 'now')""",
            (account_id, screen_name)
        )
        self._commit()
    
    def stop_monitoring_account(self, account_id: str):
        self.conn.execute(
            "UPDATE monitored_accounts SET is_active = FALSE WHERE account_id = ?",
            (account_id,)
        )
        self._commit()

    def update_account_last_check(self, account_id: str, timestamp: int):
        self.conn.execute(
            "UPDATE monitored_accounts SET last_check = ? WHERE account_id = ?",
            (timestamp, account_id)
        )
        self._commit()
    
    def get_monitored_accounts(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT account_id, screen_name, is_active, last_check, created_at FROM monitored_accounts"
        )
        return [dict(zip(['account_id', 'screen_name', 'is_active', 'last_check', 'created_at'], row))
                for row in cursor.fetchall()]
    
    def stop_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = FALSE")
        self._commit()
        
    def start_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = TRUE")
        self._commit()