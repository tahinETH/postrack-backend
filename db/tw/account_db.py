from typing import List, Dict, Any, Optional
from db.base import BaseRepository
import json


class AccountRepository(BaseRepository):
    def upsert_account(self, account_id: str, screen_name: str, account_details: Dict[str, Any], 
                       monitor: Optional[bool] = None, update_existing: bool = True) -> None:
        """
        Args:
            account_id: The unique identifier of the account
            screen_name: The screen name of the account
            account_details: Dictionary containing account details
            monitor: If True, account will be set as active for monitoring. If None, monitoring status won't change
            update_existing: If True, will update existing records on conflict
        """
        # Serialize account_details to JSON string
        account_details_json = json.dumps(account_details)
        
        if update_existing:
            self.conn.execute(
                """INSERT INTO monitored_accounts (account_id, screen_name, is_active, account_details) 
                   VALUES (?, ?, COALESCE(?, TRUE), ?)
                   ON CONFLICT(account_id) 
                   DO UPDATE SET screen_name = excluded.screen_name,
                               is_active = CASE WHEN ? IS NULL THEN is_active ELSE ? END,
                               account_details = excluded.account_details,
                               last_check = CASE WHEN ? IS NOT NULL AND ? THEN strftime('%s', 'now') ELSE last_check END""",
                (account_id, screen_name, monitor, account_details_json, monitor, monitor, monitor, monitor)
            )
        else:
            self.conn.execute(
                """INSERT INTO monitored_accounts (account_id, screen_name, is_active, account_details, last_check) 
                   VALUES (?, ?, COALESCE(?, TRUE), ?, strftime('%s', 'now'))
                   ON CONFLICT(account_id) DO NOTHING""",
                (account_id, screen_name, monitor, account_details_json)
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
            "SELECT account_id, screen_name, is_active, last_check, created_at, account_details FROM monitored_accounts"
        )
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(['account_id', 'screen_name', 'is_active', 'last_check', 'created_at', 'account_details'], row))
            if row_dict['account_details']:
                row_dict['account_details'] = json.loads(row_dict['account_details'])
            results.append(row_dict)
        return results
    
    def stop_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = FALSE")
        self._commit()
        
    def start_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = TRUE")
        self._commit()

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT account_id, screen_name, is_active, last_check, created_at, account_details FROM monitored_accounts WHERE account_id = ?",
            (account_id,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(zip(['account_id', 'screen_name', 'is_active', 'last_check', 'created_at', 'account_details'], row))
            if result['account_details']:
                result['account_details'] = json.loads(result['account_details'])
            return result
        return None

    