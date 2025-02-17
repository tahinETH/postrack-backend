import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import asyncio
from db.migrations import connect_and_migrate
from db.tw.tweet_db import TweetDataRepository
from db.tw.structured import TweetStructuredRepository
from db.tw.account_db import AccountRepository
from api_client import TwitterAPIClient
import json
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringRun:
    def __init__(self, tweet_id: str, run_timestamp: float):
        self.tweet_id = tweet_id
        self.timestamp = run_timestamp
        self.details_saved = False
        self.comments_saved = False
        self.retweeters_saved = False
        self.errors: List[str] = []

    def add_error(self, key, message, critical=True):
        self.errors.append({"key": key, "message": message, "critical": critical})

    def is_successful(self):
        return not any(error["critical"] for error in self.errors)
    
    @property
    def error_messages(self):
        return [f"{err['key']}: {err['message']}" for err in self.errors]


class TweetMonitor:
    def __init__(self, db_path: str, api_key: str, interval_minutes: int = 5):
        self.conn = connect_and_migrate(Path(db_path))
        self.tweet_data = TweetDataRepository(self.conn)
        self.tweet_analysis = TweetStructuredRepository(self.conn)
        self.accounts = AccountRepository(self.conn)
        self.api_client = TwitterAPIClient(api_key)
        self.interval_minutes = interval_minutes
        self.logger = logging.getLogger(__name__)

    async def monitor_account(self, screen_name: str, max_followers: int):
        """Start monitoring an account"""
        try:
            user_details = await self.api_client.api_get_user(screen_name)
            if user_details:
                account_id = user_details['id_str']
                if user_details['followers_count'] > max_followers:
                    self.accounts.upsert_account(account_id, screen_name, user_details, monitor=False, update_existing=True, is_active=False)
                    self.logger.info(f"Account {screen_name} has too many followers ({user_details['followers_count']}), not monitoring")
                    return None
                self.accounts.upsert_account(account_id, screen_name, user_details, monitor=True, update_existing=True, is_active=True)
                self.logger.info(f"Started monitoring account {screen_name}")
                return account_id
            return None
        except Exception as e:
            self.logger.error(f"Error monitoring account {screen_name}: {str(e)}")
            return None

    async def check_and_update_accounts(self):
        "monitors accounts for new tweets"
        try:
            accounts = self.accounts.get_monitored_accounts()
            for account in accounts:
                if account['is_active']:
                    since_time = account['last_check']
                    if not since_time:
                        since_time = account['created_at']
                    
                    new_tweets = await self.get_latest_user_tweets(
                        account['screen_name'],
                        since_time=since_time
                    )
                    
                    for tweet in new_tweets:
                        tweet_id = tweet['id_str']
                        screen_name = tweet['user']['screen_name']
                        self.tweet_data.add_monitored_tweet(tweet_id, screen_name)
                        await self.monitor_tweet(tweet_id=tweet_id, tweet=tweet)

                    if new_tweets:
                        self.logger.info(
                            f"Found {len(new_tweets)} new tweets from {account['screen_name']}"
                        )
                        
                    current_timestamp = int(datetime.now().timestamp())
                    self.accounts.update_account_last_check(account['account_id'], current_timestamp)

            await asyncio.sleep(180)

        except Exception as e:
            self.logger.error(f"Error checking accounts for new tweets: {str(e)}")

    async def get_latest_user_tweets(self, username: str, since_time: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            tweets = await self.api_client.api_get_latest_user_tweets(username, since_time)
            if tweets:
                self.logger.info(f"Retrieved {len(tweets)} tweets for user {username}")
                return tweets
            else:
                self.logger.warning(f"No tweets found for user {username}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting tweets for user {username}: {str(e)}")
            return []

    def _needs_update(self, last_check: Optional[str], interval_minutes: Optional[int] = None) -> bool:
        if not last_check:
            return True
            
        interval = interval_minutes or self.interval_minutes
        last_check_dt = datetime.fromtimestamp(int(last_check))
        time_since_check = datetime.now() - last_check_dt
        
        return time_since_check > timedelta(minutes=interval)

    async def check_and_update_tweets(self):
        "monitors existing tweets and updates if needed"
        try:
            tweets = self.tweet_data.get_monitored_tweets()
            update_tasks = []
        
            for tweet in tweets:
                if tweet['is_active'] and self._needs_update(tweet['last_check']):
                    self.logger.info(
                        f"Tweet {tweet['tweet_id']} needs update "
                        f"(last check: {tweet['last_check'] or 'never'})"
                    )
                    update_tasks.append(self.monitor_tweet(tweet_id=tweet['tweet_id']))
                
            if update_tasks:
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Error in update task: {str(result)}")
                    if isinstance(result, MonitoringRun) and not result.is_successful():
                        self.logger.warning(
                            f"Monitoring run for tweet {result.tweet_id} had critical issues: "
                            f"{'; '.join(result.error_messages)}"
                        )
            else:
                self.logger.info("No tweets need updating at this time")
                
        except Exception as e:
            self.logger.error(f"Error checking tweets: {str(e)}")

    async def _fetch_tweet_details(self, tweet_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            details = await self.api_client.api_get_tweet(tweet_id)
            if not details:
                return None, None
                
            if isinstance(details, dict) and 'status' in details and details['status'] == 'error':
                self.logger.error(f"Error response for tweet {tweet_id}: {details['message']}")
                if details['message'] == 'Tweet not found':
                    self.tweet_data.stop_monitoring_tweet(tweet_id)
                return None, None
            
            screen_name = details.get('user', {}).get('screen_name')
            return details, screen_name
        except Exception as e:
            self.logger.error(f"Error fetching tweet details for {tweet_id}: {str(e)}")
            return None, None

    async def _fetch_tweet_comments(self, tweet_id: str, screen_name: Optional[str], since_timestamp: Optional[str] = None) -> List[Dict]:
        try:
            comments = await self.api_client.api_get_tweet_comments(tweet_id, screen_name, since_timestamp)
            return comments['data'] if comments else []
        except Exception as e:
            self.logger.error(f"Error fetching comments for {tweet_id}: {str(e)}")
            return []

    async def _fetch_tweet_retweeters(self, tweet_id: str) -> List[Dict]:
        try:
            retweeters = await self.api_client.api_get_tweet_retweeters(tweet_id)
            return retweeters['data'] if retweeters else []
        except Exception as e:
            self.logger.error(f"Error fetching retweeters for {tweet_id}: {str(e)}")
            return []
        
    async def _fetch_tweet_quotes(self, tweet_id: str) -> List[Dict]:
        try:
            quotes = await self.api_client.api_get_tweet_quotes(tweet_id)
            return quotes['data'] if quotes else []
        except Exception as e:
            self.logger.error(f"Error fetching quotes for {tweet_id}: {str(e)}")
            return []

    async def monitor_tweet(self, tweet_id: str, tweet: Optional[Dict] = None) -> MonitoringRun:
        self.logger.info(f"Starting monitoring run for tweet {tweet_id}")
        run_timestamp = int(datetime.now().timestamp())
        monitoring_run = MonitoringRun(tweet_id, run_timestamp)
        
        self.logger.debug(f"Fetching existing tweet details for {tweet_id}")
        latest_tweet_details = self.tweet_data.get_latest_tweet_details(tweet_id)
        tweet_details = self.tweet_data.get_tweet_by_id(tweet_id)
        
        
        if tweet_details:
            self.logger.debug(f"Checking update frequency for tweet {tweet_id}")
            current_time = datetime.now().timestamp()
            tweet_age = current_time - tweet_details[3]  # created_at is index 3
            last_check = tweet_details[4]
            hours_old = tweet_age / 3600
            
            if last_check and (hours_old > 3):
                if last_check + 3600 < current_time:
                    self.logger.debug(f"Tweet {tweet_id} is over 3 hours old and was checked within last hour, skipping")
                    return monitoring_run
            elif last_check and (hours_old > 1):
                if last_check + 900 < current_time:
                    self.logger.debug(f"Tweet {tweet_id} is over 1 hour old and was checked within last 15 minutes, skipping") 
                    return monitoring_run
            elif last_check and (hours_old > 0.5):
                if last_check + 300 < current_time:
                    self.logger.debug(f"Tweet {tweet_id} is less than 1 hour old and was checked within last 5 minutes, skipping")
                    return monitoring_run

        self.logger.debug(f"Getting tweet details for {tweet_id}")
        if tweet:
            details = tweet
            screen_name = tweet['user']['screen_name']
            self.logger.debug(f"Using provided tweet details for {tweet_id}")
        else:
            self.logger.debug(f"Fetching tweet details from API for {tweet_id}")
            details, screen_name = await self._fetch_tweet_details(tweet_id)

        if details:
            try:
                self.logger.debug(f"Processing user data for tweet {tweet_id}")
                user_data = details.get('user', {})
                account_id = user_data.get('id_str')
                screen_name = user_data.get('screen_name')

                if user_data:
                    self.logger.debug(f"Upserting account {screen_name} for tweet {tweet_id}")
                    self.accounts.upsert_account(account_id, screen_name, user_data, monitor=None, update_existing=True)

                if account_id and screen_name:
                    self.logger.debug(f"Adding account info to monitored tweet {tweet_id}")
                    self.tweet_data.add_account_info_to_monitored_tweet(account_id, tweet_id, screen_name)

                self.logger.debug(f"Saving tweet details for {tweet_id}")
                self.tweet_data.save_tweet_details(
                    tweet_id=tweet_id,
                    details=details,
                    timestamp=str(run_timestamp)
                )
                
                monitoring_run.details_saved = True
                self.logger.info(f"Successfully saved details for tweet {tweet_id}")
            except Exception as e:
                monitoring_run.add_error("details", str(e), critical=True)
                self.logger.error(f"Error saving details for {tweet_id}: {str(e)}")
        else:
            monitoring_run.add_error("details", "Failed to fetch tweet details", critical=True)
            self.logger.error(f"Failed to fetch details for tweet {tweet_id}")
            return monitoring_run

        self.logger.debug(f"Getting latest monitoring run for {tweet_id}")
        latest_run = self.tweet_data.get_latest_monitoring_run(tweet_id)
        
        since_timestamp = str(latest_run[0]) if latest_run else None
        self.logger.debug(f"Using since_timestamp {since_timestamp} for tweet {tweet_id}")

        # Check if tweet details exist and compare engagement metrics
        comments_needs_update = True
        retweets_needs_update = True
        quotes_needs_update = True
        
        if latest_tweet_details:
            self.logger.debug(f"Comparing engagement metrics for tweet {tweet_id}")
            try:
                quotes_needs_update = latest_tweet_details.get('quote_count') != details.get('quote_count')
                comments_needs_update = latest_tweet_details.get('reply_count') != details.get('reply_count')
                retweets_needs_update = latest_tweet_details.get('retweet_count') != details.get('retweet_count')
                self.logger.debug(f"Tweet {tweet_id} needs updates - comments: {comments_needs_update}, retweets: {retweets_needs_update}")
            except Exception as e:
                self.logger.error(f"Error comparing tweet engagement for {tweet_id}: {str(e)}")

        if comments_needs_update:
            self.logger.debug(f"Fetching comments for tweet {tweet_id}")
            comments = await self._fetch_tweet_comments(tweet_id, screen_name, since_timestamp)
            
            if comments:
                try:
                    self.logger.debug(f"Getting tweet history for comments comparison for {tweet_id}")
                    tweet_history = await self.tweet_analysis.get_raw_tweet_history(tweet_id)
                    existing_comments = {
                        comment['data']['id_str'] 
                        for comment in tweet_history.get('comments', [])
                    }
                    
                    new_comments = [
                        comment for comment in comments 
                        if comment['id_str'] not in existing_comments
                    ]
                    
                    if new_comments:
                        self.logger.debug(f"Saving {len(new_comments)} new comments for tweet {tweet_id}")
                        self.tweet_data.save_tweet_comments(
                            tweet_id=tweet_id,
                            comments=new_comments,
                            timestamp=str(run_timestamp)
                        )
                        monitoring_run.comments_saved = True
                        self.logger.info(f"Successfully saved {len(new_comments)} new comments for tweet {tweet_id}")
                    else:
                        monitoring_run.comments_saved = True
                        self.logger.info(f"No new comments found for tweet {tweet_id}")
                        
                except Exception as e:
                    monitoring_run.add_error("comments", str(e), critical=False)
                    self.logger.error(f"Error saving comments for {tweet_id}: {str(e)}")

        if retweets_needs_update:
            self.logger.debug(f"Fetching retweeters for tweet {tweet_id}")
            retweeters = await self._fetch_tweet_retweeters(tweet_id)
            if retweeters:
                try:
                    self.logger.debug(f"Getting tweet history for retweeters comparison for {tweet_id}")
                    tweet_history = await self.tweet_analysis.get_raw_tweet_history(tweet_id)
                    existing_retweeters = {
                        retweeter['data']['id_str'] 
                        for retweeter in tweet_history.get('retweeters', [])
                    }
                    
                    new_retweeters = [
                        retweeter for retweeter in retweeters 
                        if retweeter['id_str'] not in existing_retweeters
                    ]
                    
                    if new_retweeters:
                        self.logger.debug(f"Saving {len(new_retweeters)} new retweeters for tweet {tweet_id}")
                        self.tweet_data.save_tweet_retweeters(
                            tweet_id=tweet_id,
                            retweeters=new_retweeters,
                            timestamp=str(run_timestamp)
                        )
                        monitoring_run.retweeters_saved = True
                        self.logger.info(f"Successfully saved {len(new_retweeters)} new retweeters for tweet {tweet_id}")
                    else:
                        monitoring_run.retweeters_saved = True
                        self.logger.info(f"No new retweeters found for tweet {tweet_id}")
                        
                except Exception as e:
                    monitoring_run.add_error("retweeters", str(e), critical=False)
                    self.logger.error(f"Error saving retweeters for {tweet_id}: {str(e)}")

        if quotes_needs_update:
            self.logger.debug(f"Fetching quotes for tweet {tweet_id}")
            quotes = await self._fetch_tweet_quotes(tweet_id)
            if quotes:
                try:
                    self.logger.debug(f"Getting tweet history for quotes comparison for {tweet_id}")
                    tweet_history = await self.tweet_analysis.get_raw_tweet_history(tweet_id)
                    existing_quotes = {
                        quote['data']['id_str']
                        for quote in tweet_history.get('quotes', [])
                    }
                    new_quotes = [
                        quote for quote in quotes
                        if quote['id_str'] not in existing_quotes
                    ]
                    if new_quotes:
                        self.logger.debug(f"Saving {len(new_quotes)} new quotes for tweet {tweet_id}")
                        self.tweet_data.save_tweet_quotes(
                            tweet_id=tweet_id,
                            quotes=new_quotes,
                            timestamp=str(run_timestamp)
                        )
                        monitoring_run.quotes_saved = True
                        self.logger.info(f"Successfully saved {len(new_quotes)} new quotes for tweet {tweet_id}")
                    else:
                        monitoring_run.quotes_saved = True
                        self.logger.info(f"No new quotes found for tweet {tweet_id}")
                        
                except Exception as e:
                    monitoring_run.add_error("quotes", str(e), critical=False)
                    self.logger.error(f"Error saving quotes for {tweet_id}: {str(e)}")
            
        

        return monitoring_run
