import json
import logging
from typing import Dict, List, Any
from .base import BaseRepository
from .tw_data import TweetDataRepository


class TweetAnalysisRepository(BaseRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tweet_data = TweetDataRepository(self.conn)

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

    def get_feed(self) -> List[Dict[str, Any]]:
        """Get latest data for all monitored tweets"""
        logger = logging.getLogger(__name__)
        
        logger.info("Starting feed retrieval")
        monitored_tweets = self.conn.execute(
            "SELECT tweet_id, is_active FROM monitored_tweets"
        ).fetchall()
        logger.info(f"Found {len(monitored_tweets)} monitored tweets")
        
        feed_data = []
        for (tweet_id, is_active) in monitored_tweets:
            logger.info(f"Processing tweet_id: {tweet_id}")
            
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
            
            comment_count = self.conn.execute(
                """SELECT COUNT(DISTINCT comment_id) 
                   FROM tweet_comments 
                   WHERE tweet_id = ?""",
                (tweet_id,)
            ).fetchone()[0]
            
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
            
            text = tweet_data.get('full_text') or tweet_data.get('text')
            if text:
                feed_item['text'] = text
                
            feed_data.append(feed_item)
            
        return sorted(feed_data, key=lambda x: x['last_updated'], reverse=True)

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
        details_rows = self.conn.execute(
            """SELECT data_json, captured_at 
               FROM tweet_details 
               WHERE tweet_id = ? 
               ORDER BY captured_at""",
            (tweet_id,)
        ).fetchall()
        
        if not details_rows:
            return {}
            
        engagement_metrics = {}
        full_text = None
        user_info = None
        user_followers = {}
        
        for detail_json, captured_at in details_rows:
            detail = json.loads(detail_json)
            engagement_metrics[captured_at] = self.process_engagement_metrics(detail)
            
            if detail.get('full_text'):
                full_text = detail['full_text']
            if detail.get('user'):
                user_info = {
                    'id': detail['user'].get('id'),
                    'screen_name': detail['user'].get('screen_name'),
                    'profile_image_url_https': detail['user'].get('profile_image_url_https', '').replace('_normal', '')
                }
                user_followers[captured_at] = detail['user'].get('followers_count', 0)
            
        engagement_changes = {}
        timestamps = sorted(engagement_metrics.keys())
        for i in range(1, len(timestamps)):
            prev_ts = timestamps[i-1]
            curr_ts = timestamps[i]
            
            engagement_changes[curr_ts] = {
                metric: (engagement_metrics[curr_ts][metric] or 0) - (engagement_metrics[prev_ts][metric] or 0)
                for metric in engagement_metrics[curr_ts].keys()
            }
            
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