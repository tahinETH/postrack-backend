from datetime import datetime
import json
from typing import Optional, Dict, Any, List
from ..base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class UserDataRepository(BaseRepository):
    def create_user(self, user_id: str, email: str, name: Optional[str] = None,
                   current_tier: Optional[str] = None, fe_metadata: Optional[Dict] = None) -> None:
        """Create a new user"""
        try:
            now = int(datetime.now().timestamp())
            self.conn.execute(
                """INSERT INTO users 
                   (id, email, name, current_tier, current_period_start, fe_metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, email, name, current_tier or 'free', now, 
                 json.dumps(fe_metadata) if fe_metadata else None)
            )
            self._commit()
            logger.info(f"Created user {user_id}")
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {str(e)}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        cursor = self.conn.execute(
            """SELECT id, email, name, current_tier, 
                      current_period_start, current_period_end, fe_metadata
               FROM users WHERE id = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            # Get tracked items
            tracked_items = self.get_tracked_items(row[0])
            
            return {
                'id': row[0],
                'email': row[1], 
                'name': row[2],
                'current_tier': row[3],
                'current_period_start': row[4],
                'current_period_end': row[5],
                'fe_metadata': json.loads(row[6]) if row[6] else None,
                'tracked_items': tracked_items
            }
        return None

    def update_user(self, user_id: str, **updates: Any) -> bool:
        """Update user fields"""
        try:
            valid_fields = {'email', 'name', 'current_tier', 
                          'current_period_start', 'current_period_end', 'fe_metadata'}
            
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in valid_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(value) if field == 'fe_metadata' else value)
            
            if not update_fields:
                return False
                
            values.append(user_id)
            query = f"""UPDATE users 
                       SET {', '.join(update_fields)}
                       WHERE id = ?"""
                       
            self.conn.execute(query, values)
            self._commit()
            logger.info(f"Updated user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise

    """ def delete_user(self, user_id: str) -> bool:
        
        try:
            self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self._commit()
            logger.info(f"Deleted user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise """

    def add_tracked_item(self, user_id: str, tracked_type: str, tracked_id: str, tracked_account_name: Optional[str] = None) -> bool:
        """Add a tracked item (tweet or account) for a user"""
        try:
            self.conn.execute(
                """INSERT INTO user_tracked_items 
                   (user_id, tracked_type, tracked_id, tracked_account_name)
                   VALUES (?, ?, ?, ?)""",
                (user_id, tracked_type, tracked_id, tracked_account_name)
            )
            self._commit()
            logger.info(f"Added tracked {tracked_type} {tracked_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding tracked item for user {user_id}: {str(e)}")
            raise

    def remove_tracked_item(self, user_id: str, tracked_type: str, tracked_id: str) -> bool:
        """Remove a tracked item for a user"""
        try:
            self.conn.execute(
                """DELETE FROM user_tracked_items 
                   WHERE user_id = ? AND tracked_type = ? AND tracked_id = ?""",
                (user_id, tracked_type, tracked_id)
            )
            self._commit()
            logger.info(f"Removed tracked {tracked_type} {tracked_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing tracked item for user {user_id}: {str(e)}")
            raise

    def get_tracked_items(self, user_id: str) -> Dict[str, List[str]]:
        """Get all tracked items for a user"""
        cursor = self.conn.execute(
            """SELECT tracked_type, tracked_id 
               FROM user_tracked_items 
               WHERE user_id = ?""",
            (user_id,)
        )
        items = {'tweets': [], 'accounts': []}
        for row in cursor.fetchall():
            if row[0] == 'tweet':
                items['tweets'].append(row[1])
            elif row[0] == 'account':
                items['accounts'].append(row[1])
        return items
    def is_tweet_tracked(self, tweet_id: str) -> bool:
        """Check if a tweet is being tracked by any user"""
        try:
            cursor = self.conn.execute(
                """SELECT COUNT(*) FROM user_tracked_items 
                   WHERE tracked_type = 'tweet' AND tracked_id = ?""",
                (tweet_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if tweet {tweet_id} is tracked: {str(e)}")
            raise

    
