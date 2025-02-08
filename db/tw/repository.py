from datetime import datetime
import json
from typing import Optional, List, Dict, Any
from db.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class TweetDataRepository(BaseRepository):
    def get_latest_tweet_for_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        return self.conn.execute(
            "SELECT tweet_id, created_at FROM monitored_tweets WHERE account_id = ? ORDER BY created_at DESC LIMIT 1",
            (account_id,)
        ).fetchone()
    
    def get_tweets_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        return self.conn.execute(
            "SELECT tweet_id, created_at FROM monitored_tweets WHERE account_id = ? ORDER BY created_at DESC",
            (account_id,)
        ).fetchall()
    
    def get_tweets_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get tweets for a user based on their tracked items"""
        tracked_items = self.conn.execute(
            """SELECT tracked_type, tracked_id 
               FROM user_tracked_items 
               WHERE user_id = ?""",
            (user_id,)
        ).fetchall()
        
        tweets = []
        for item in tracked_items:
            tracked_type = item[0]  # Access tuple elements by index
            tracked_id = item[1]
            
            if tracked_type == 'account':
                # Get tweets for tracked account
                account_tweets = self.conn.execute(
                    """SELECT tweet_id, created_at, is_active 
                       FROM monitored_tweets 
                       WHERE account_id = ? 
                       ORDER BY created_at DESC""",
                    (tracked_id,)
                ).fetchall()
                for tweet in account_tweets:
                    tweets.append({
                        'tweet_id': tweet[0],
                        'created_at': tweet[1], 
                        'is_active': tweet[2],
                        'tracking_type': 'account',
                        'tracked_id': tracked_id
                    })
            elif tracked_type == 'tweet':
                # Get individual tracked tweet
                tweet = self.conn.execute(
                    """SELECT tweet_id, created_at, is_active 
                       FROM monitored_tweets 
                       WHERE tweet_id = ?""",
                    (tracked_id,)
                ).fetchone()
                if tweet:
                    tweets.append({
                        'tweet_id': tweet[0],
                        'created_at': tweet[1],
                        'is_active': tweet[2],
                        'tracking_type': 'individual',
                        'tracked_id': tracked_id
                    })

        return tweets
    
    def add_monitored_tweet(self, tweet_id: str, screen_name: Optional[str] = None):
        self.conn.execute(
            """INSERT INTO monitored_tweets (tweet_id, user_screen_name, is_active) 
               VALUES (?, ?, TRUE)
               ON CONFLICT(tweet_id) 
               DO UPDATE SET is_active = TRUE, user_screen_name = excluded.user_screen_name""",
            (tweet_id, screen_name)
        )
        self._commit()

    def delete_monitored_tweet(self, tweet_id: str):
        # Delete related records first to satisfy foreign key constraints
        self.conn.execute(
            "DELETE FROM tweet_details WHERE tweet_id = ?",
            (tweet_id,)
        )
        self.conn.execute(
            "DELETE FROM tweet_comments WHERE tweet_id = ?", 
            (tweet_id,)
        )
        self.conn.execute(
            "DELETE FROM tweet_retweeters WHERE tweet_id = ?",
            (tweet_id,)
        )
        # Then delete the main tweet record
        self.conn.execute(
            "DELETE FROM monitored_tweets WHERE tweet_id = ?",
            (tweet_id,)
        )
        self._commit()

    def stop_monitoring_tweet(self, tweet_id: str):
        self.conn.execute(
            "UPDATE monitored_tweets SET is_active = FALSE WHERE tweet_id = ?",
            (tweet_id,)
        )
        self._commit()

    def update_tweet_check(self, tweet_id: str, timestamp: Optional[int] = None):
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        self.conn.execute(
            "UPDATE monitored_tweets SET last_check = ? WHERE tweet_id = ?",
            (timestamp, tweet_id)
        )
        self._commit()

    def save_tweet_details(self, tweet_id: str, details: Dict[str, Any], timestamp: Optional[int] = None):
        """Save tweet details with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        self.conn.execute(
            "INSERT INTO tweet_details (tweet_id, data_json, captured_at) VALUES (?, ?, ?)",
            (tweet_id, json.dumps(details), timestamp)
        )
        self._commit()
    
    def remove_all_tweet_data(self, tweet_id: str):
        """Remove all data related to a tweet from all tables"""
        try:
            # Delete from all related tables
            self.conn.execute(
                "DELETE FROM tweet_details WHERE tweet_id = ?",
                (tweet_id,)
            )
            self.conn.execute(
                "DELETE FROM tweet_comments WHERE tweet_id = ?",
                (tweet_id,)
            )
            self.conn.execute(
                "DELETE FROM tweet_retweeters WHERE tweet_id = ?",
                (tweet_id,)
            )
            self.conn.execute(
                "DELETE FROM ai_analysis WHERE tweet_id = ?",
                (tweet_id,)
            )
            self.conn.execute(
                "DELETE FROM monitored_tweets WHERE tweet_id = ?",
                (tweet_id,)
            )
            self._commit()
            logger.info(f"Successfully removed all data for tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error removing data for tweet {tweet_id}: {str(e)}")
            raise

    def save_tweet_comments(self, tweet_id: str, comments: List[Dict[str, Any]], timestamp: Optional[int] = None):
        """Save tweet comments with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        for comment in comments:
            self.conn.execute(
                """INSERT OR REPLACE INTO tweet_comments 
                   (comment_id, tweet_id, data_json, captured_at) 
                   VALUES (?, ?, ?, ?)""",
                (comment['id'], tweet_id, json.dumps(comment), timestamp)
            )
        self._commit()

    def save_tweet_retweeters(self, tweet_id: str, retweeters: List[Dict[str, Any]], timestamp: Optional[int] = None):
        """Save tweet retweeters with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        for retweeter in retweeters:
            self.conn.execute(
                """INSERT OR REPLACE INTO tweet_retweeters 
                   (user_id, tweet_id, data_json, captured_at) 
                   VALUES (?, ?, ?, ?)""",
                (retweeter['id'], tweet_id, json.dumps(retweeter), timestamp)
            )
        self._commit()

    def get_monitored_tweets(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT tweet_id, user_screen_name, created_at, last_check, is_active FROM monitored_tweets"
        )
        return [dict(zip(['tweet_id', 'user_screen_name', 'created_at', 'last_check', 'is_active'], row))
                for row in cursor.fetchall()]
    
    def save_ai_analysis(self, tweet_id: str, analysis: str, input_data: Dict[str, Any]):
        timestamp = int(datetime.now().timestamp())
        self.conn.execute(
            "INSERT INTO ai_analysis (tweet_id, analysis, input_data, created_at) VALUES (?, ?, ?, ?)",
            (tweet_id, analysis, json.dumps(input_data), timestamp)
        )
        self._commit()

    def get_ai_analysis(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute(
            """SELECT analysis, input_data 
               FROM ai_analysis 
               WHERE tweet_id = ?
               ORDER BY created_at DESC
               LIMIT 1""",
            (tweet_id,)
        )
        return cursor.fetchone()