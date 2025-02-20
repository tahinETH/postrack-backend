
from typing import Optional, Dict
from ..base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class APICallLogRepository(BaseRepository):
    def upsert_api_calls(self, monitor_timestamp: int, tweet_details_calls: int = 0,
                        retweet_api_calls: int = 0, quote_api_calls: int = 0,
                        comment_api_calls: int = 0, total_api_calls: int = 0) -> None:
        """Log API calls for a monitoring timestamp"""
        try:
            self.conn.execute(
                """INSERT INTO api_calls 
                   (monitor_timestamp, tweet_details_calls, retweet_api_calls,
                    quote_api_calls, comment_api_calls, total_api_calls)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(monitor_timestamp) 
                   DO UPDATE SET 
                       tweet_details_calls = excluded.tweet_details_calls,
                       retweet_api_calls = excluded.retweet_api_calls,
                       quote_api_calls = excluded.quote_api_calls,
                       comment_api_calls = excluded.comment_api_calls,
                       total_api_calls = excluded.total_api_calls""",
                (monitor_timestamp, tweet_details_calls, retweet_api_calls,
                 quote_api_calls, comment_api_calls, total_api_calls)
            )
            self._commit()
            logger.info(f"Logged API calls for timestamp {monitor_timestamp}")
        except Exception as e:
            logger.error(f"Error logging API calls for timestamp {monitor_timestamp}: {str(e)}")
            raise

    def get_api_calls(self, monitor_timestamp: int) -> Optional[Dict[str, int]]:
        """Get API call logs for a specific timestamp"""
        try:
            cursor = self.conn.execute(
                """SELECT tweet_details_calls, retweet_api_calls,
                          quote_api_calls, comment_api_calls, total_api_calls
                   FROM api_calls 
                   WHERE monitor_timestamp = ?""",
                (monitor_timestamp,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'tweet_details_calls': row[0],
                    'retweet_api_calls': row[1],
                    'quote_api_calls': row[2],
                    'comment_api_calls': row[3],
                    'total_api_calls': row[4]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting API calls for timestamp {monitor_timestamp}: {str(e)}")
            raise
