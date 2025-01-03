# repository.py
from datetime import datetime
import json
import sqlite3
from typing import Optional, List, Dict, Any


class TweetRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    
    def add_monitored_account(self, account_id: str, screen_name: str):
        self.conn.execute(
            """INSERT INTO monitored_accounts (account_id, screen_name) 
               VALUES (?, ?)
               ON CONFLICT(account_id) 
               DO UPDATE SET screen_name = excluded.screen_name, is_active = TRUE""",
            (account_id, screen_name)
        )
        self.conn.commit()
    
    def stop_monitoring_account(self, account_id: str):
        self.conn.execute(
            "UPDATE monitored_accounts SET is_active = FALSE WHERE account_id = ?",
            (account_id,)
        )
        self.conn.commit()

    def update_account_last_check(self, account_id: str, timestamp: int):
        self.conn.execute(
            "UPDATE monitored_accounts SET last_check = ? WHERE account_id = ?",
            (timestamp, account_id)
        )
        self.conn.commit()
    
    def get_monitored_accounts(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT account_id, screen_name, is_active, last_check, created_at FROM monitored_accounts"
        )
        return [dict(zip(['account_id', 'screen_name', 'is_active', 'last_check', 'created_at'], row))
                for row in cursor.fetchall()]
    
    def stop_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = FALSE")
        self.conn.commit()
        
    def start_all_accounts(self):
        self.conn.execute("UPDATE monitored_accounts SET is_active = TRUE")
        self.conn.commit()
        
    def get_latest_tweet_for_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        return self.conn.execute(
            "SELECT tweet_id, created_at FROM monitored_tweets WHERE account_id = ? ORDER BY created_at DESC LIMIT 1",
            (account_id,)
        ).fetchone()
    
    def process_engagement_metrics(self, tweet_details: Dict) -> Dict[str, int]:
        """Extract engagement metrics from tweet details"""
        return {
            'quote_count': tweet_details.get('quote_count', 0),
            'reply_count': tweet_details.get('reply_count', 0),
            'retweet_count': tweet_details.get('retweet_count', 0),
            'favorite_count': tweet_details.get('favorite_count', 0),
            'views_count': tweet_details.get('views_count', 0),
            'bookmark_count': tweet_details.get('bookmark_count', 0)
        }

    def add_monitored_tweet(self, tweet_id: str, screen_name: Optional[str] = None):
        self.conn.execute(
            """INSERT INTO monitored_tweets (tweet_id, user_screen_name, is_active) 
               VALUES (?, ?, TRUE)
               ON CONFLICT(tweet_id) 
               DO UPDATE SET is_active = TRUE, user_screen_name = excluded.user_screen_name""",
            (tweet_id, screen_name)
        )
        self.conn.commit()

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
        self.conn.commit()

    def stop_monitoring_tweet(self, tweet_id: str):
        self.conn.execute(
            "UPDATE monitored_tweets SET is_active = FALSE WHERE tweet_id = ?",
            (tweet_id,)
        )
        self.conn.commit()

    def update_tweet_check(self, tweet_id: str, timestamp: Optional[int] = None):
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        self.conn.execute(
            "UPDATE monitored_tweets SET last_check = ? WHERE tweet_id = ?",
            (timestamp, tweet_id)
        )
        self.conn.commit()

    def save_tweet_details(self, tweet_id: str, details: Dict[str, Any], timestamp: Optional[int] = None):
        """Save tweet details with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        self.conn.execute(
            "INSERT INTO tweet_details (tweet_id, data_json, captured_at) VALUES (?, ?, ?)",
            (tweet_id, json.dumps(details), timestamp)
        )
        self.conn.commit()

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
        self.conn.commit()

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
        self.conn.commit()
        
    def get_feed(self) -> List[Dict[str, Any]]:
        """Get latest data for all monitored tweets"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Log start of feed retrieval
        logger.info("Starting feed retrieval")
        
        # Get all monitored tweets, both active and inactive
        monitored_tweets = self.conn.execute(
            "SELECT tweet_id, is_active FROM monitored_tweets"
        ).fetchall()
        logger.info(f"Found {len(monitored_tweets)} monitored tweets")
        
        feed_data = []
        for (tweet_id, is_active) in monitored_tweets:
            logger.info(f"Processing tweet_id: {tweet_id}")
            
            # Get latest tweet details
            latest_details = self.conn.execute(
                """SELECT data_json, captured_at 
                   FROM tweet_details 
                   WHERE tweet_id = ? 
                   ORDER BY captured_at DESC 
                   LIMIT 1""",
                (tweet_id,)
            ).fetchone()
            
            if not latest_details:
                logger.warning(f"No details found for tweet_id: {tweet_id}")
                continue
            
            tweet_data = json.loads(latest_details[0])
                
            captured_at = latest_details[1]
            
            engagement = self.process_engagement_metrics(tweet_data)
            
            
            # Get comment count
            comment_count = self.conn.execute(
                """SELECT COUNT(DISTINCT comment_id) 
                   FROM tweet_comments 
                   WHERE tweet_id = ?""",
                (tweet_id,)
            ).fetchone()[0]
            
            # Get retweeter count
            retweeter_count = self.conn.execute(
                """SELECT COUNT(DISTINCT user_id) 
                   FROM tweet_retweeters 
                   WHERE tweet_id = ?""",
                (tweet_id,)
            ).fetchone()[0]
        
            
            feed_item = {
                'tweet_id': tweet_id,
                'is_monitored': bool(is_active),
                'author': {
                    'id': tweet_data.get('author_id') or tweet_data.get('user', {}).get('id'),
                    'screen_name': tweet_data.get('user', {}).get('screen_name') or tweet_data.get('author_username'),
                    'followers_count': tweet_data.get('user', {}).get('followers_count', 0),
                    'profile_image_url_https': tweet_data.get('user', {}).get('profile_image_url_https', '').replace('_normal', '')
                },
                'engagement_metrics': engagement,
                'total_comments': comment_count,
                'total_retweeters': retweeter_count,
                'last_updated': captured_at
            }
            
            # Only add text if it exists
            text = tweet_data.get('full_text') or tweet_data.get('text')
            if text:
                feed_item['text'] = text
                
            feed_data.append(feed_item)
            
        return sorted(feed_data, key=lambda x: x['last_updated'], reverse=True)
        
    def get_monitored_tweets(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT tweet_id, user_screen_name, created_at, last_check, is_active FROM monitored_tweets"
        )
        
        return [dict(zip(['tweet_id', 'user_screen_name', 'created_at', 'last_check', 'is_active'], row))
                for row in cursor.fetchall()]

    def get_raw_tweet_history(self, tweet_id: str) -> Dict[str, Any]:
        """Get raw, unprocessed history data for a tweet"""
        details = self.conn.execute(
            """SELECT data_json, captured_at 
               FROM tweet_details 
               WHERE tweet_id = ? 
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()

        comments = self.conn.execute(
            """SELECT data_json, captured_at
               FROM tweet_comments
               WHERE tweet_id = ?
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()

        retweeters = self.conn.execute(
            """SELECT data_json, captured_at
               FROM tweet_retweeters
               WHERE tweet_id = ?
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()

        return {
            'tweet_id': tweet_id,
            'details': [
                {'data': json.loads(d[0]), 'captured_at': d[1]} 
                for d in details
            ],
            'comments': [
                {'data': json.loads(c[0]), 'captured_at': c[1]} 
                for c in comments
            ],
            'retweeters': [
                {'data': json.loads(r[0]), 'captured_at': r[1]} 
                for r in retweeters
            ]
        }

    def get_analyzed_tweet_history(self, tweet_id: str) -> Dict[str, Any]:
        """Get processed and analyzed history data for a tweet"""
        # Get all tweet details ordered by capture time
        details_rows = self.conn.execute(
            """SELECT data_json, captured_at 
               FROM tweet_details 
               WHERE tweet_id = ? 
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()
        
        if not details_rows:
            return {}
            
        # Process engagement metrics over time
        engagement_metrics = {}
        full_text = None  # Track the full text from the most recent detail
        user_info = None  # Track user info from most recent detail
        user_followers = {}  # Track user followers count over time
        for detail_json, captured_at in details_rows:
            detail = json.loads(detail_json)
            engagement_metrics[captured_at] = self.process_engagement_metrics(detail)
            # Get full_text and user info from most recent detail
            if detail.get('full_text'):
                full_text = detail['full_text']
            if detail.get('user'):
                user_info = {
                    'id': detail['user'].get('id'),
                    'screen_name': detail['user'].get('screen_name'),
                    'profile_image_url_https': detail['user'].get('profile_image_url_https', '').replace('_normal', '')
                }
                user_followers[captured_at] = detail['user'].get('followers_count', 0)
            
        # Calculate engagement changes
        engagement_changes = {}
        timestamps = sorted(engagement_metrics.keys())
        for i in range(1, len(timestamps)):
            prev_ts = timestamps[i-1]
            curr_ts = timestamps[i]
            
            engagement_changes[curr_ts] = {
                metric: (engagement_metrics[curr_ts][metric] or 0) - (engagement_metrics[prev_ts][metric] or 0)
                for metric in engagement_metrics[curr_ts].keys()
            }
            
        # Get comments with details
        comments_tracking = {}
        verified_replies = {}
        comments_rows = self.conn.execute(
            """SELECT data_json, captured_at
               FROM tweet_comments
               WHERE tweet_id = ?
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()
        
        existing_comment_ids = set()
        for comment_json, captured_at in comments_rows:
            comment = json.loads(comment_json)
            if comment['id'] not in existing_comment_ids:
                if captured_at not in comments_tracking:
                    comments_tracking[captured_at] = []
                    verified_replies[captured_at] = 0
                
                is_verified = comment.get('user', {}).get('verified', False)
                if is_verified:
                    verified_replies[captured_at] += 1
                    
                comments_tracking[captured_at].append({
                    'id': comment['id'],
                    'favorite_count': comment.get('favorite_count', 0),
                    'views_count': comment.get('views_count', 0),
                    'bookmark_count': comment.get('bookmark_count', 0),
                    'screen_name': comment.get('user', {}).get('screen_name'),
                    'followers_count': comment.get('user', {}).get('followers_count', 0),
                    'verified': is_verified
                })
                existing_comment_ids.add(comment['id'])
                
        # Get retweeters with details
        retweeters_tracking = {}
        verified_retweets = {}
        retweeter_rows = self.conn.execute(
            """SELECT data_json, captured_at
               FROM tweet_retweeters
               WHERE tweet_id = ?
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()
        
        existing_retweeter_names = set()
        for retweeter_json, captured_at in retweeter_rows:
            retweeter = json.loads(retweeter_json)
            if retweeter['screen_name'] not in existing_retweeter_names:
                if captured_at not in retweeters_tracking:
                    retweeters_tracking[captured_at] = []
                    verified_retweets[captured_at] = 0
                    
                is_verified = retweeter.get('verified', False)
                if is_verified:
                    verified_retweets[captured_at] += 1
                    
                retweeters_tracking[captured_at].append({
                    'screen_name': retweeter['screen_name'],
                    'followers_count': retweeter.get('followers_count', 0),
                    'verified': is_verified
                })
                existing_retweeter_names.add(retweeter['screen_name'])
        
        for ts in engagement_metrics:
            engagement_metrics[ts].update({
                'verified_replies': verified_replies.get(ts, 0),
                'verified_retweets': verified_retweets.get(ts, 0)
            })
        
        return {
            'tweet_id': tweet_id,
            'full_text': full_text,
            'user': user_info,
            'timestamps': timestamps,
            'engagement_metrics': engagement_metrics,
            'engagement_changes': engagement_changes,
            'comments_tracking': comments_tracking,
            'retweeters_tracking': retweeters_tracking,
            'user_followers': user_followers
        }