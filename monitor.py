import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import asyncio
from db import connect_and_migrate
from repositories.tw_data import TweetDataRepository
from repositories.tw_analysis import TweetAnalysisRepository
from repositories.accounts import AccountRepository
from api_client import TwitterAPIClient

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

    def add_error(self, stage: str, error: str):
        self.errors.append(f"{stage}: {error}")

    def is_successful(self) -> bool:
        return (self.details_saved and 
                self.comments_saved and 
                self.retweeters_saved and 
                not self.errors)


class TweetMonitor:
    def __init__(self, db_path: str, api_key: str, interval_minutes: int = 5):
        self.conn = connect_and_migrate(Path(db_path))
        self.tweet_data = TweetDataRepository(self.conn)
        self.tweet_analysis = TweetAnalysisRepository(self.conn)
        self.accounts = AccountRepository(self.conn)
        self.api_client = TwitterAPIClient(api_key)
        self.interval_minutes = interval_minutes
        self.logger = logging.getLogger(__name__)

    async def monitor_account(self, screen_name: str):
        """Start monitoring an account"""
        try:
            user_details = await self.api_client.get_user_details_by_screen_name(screen_name)
            
            if user_details:
                account_id = user_details['id_str']
                self.accounts.add_monitored_account(account_id, screen_name)
                self.logger.info(f"Started monitoring account {screen_name}")
                return True
        except Exception as e:
            self.logger.error(f"Error monitoring account {screen_name}: {str(e)}")
            return False

    async def check_and_update_accounts(self):
        """Check monitored accounts for new tweets every 3 minutes"""
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
                        self.tweet_data.add_monitored_tweet(tweet_id)
                        await self.monitor_tweet(tweet_id)

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
            tweets = await self.api_client.get_user_tweets(username, since_time)
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
        try:
            tweets = self.tweet_data.get_monitored_tweets()
            update_tasks = []
            
            for tweet in tweets:
                if tweet['is_active'] and self._needs_update(tweet['last_check']):
                    self.logger.info(
                        f"Tweet {tweet['tweet_id']} needs update "
                        f"(last check: {tweet['last_check'] or 'never'})"
                    )
                    update_tasks.append(self.monitor_tweet(tweet['tweet_id']))
                
            if update_tasks:
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Error in update task: {str(result)}")
                    elif isinstance(result, MonitoringRun) and not result.is_successful():
                        self.logger.warning(
                            f"Monitoring run for tweet {result.tweet_id} had issues: "
                            f"{'; '.join(result.errors)}"
                        )
            else:
                self.logger.info("No tweets need updating at this time")
                
        except Exception as e:
            self.logger.error(f"Error checking tweets: {str(e)}")

    async def _fetch_tweet_details(self, tweet_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            details = await self.api_client.get_tweet_details(tweet_id)
            if not details:
                return None, None
            screen_name = details.get('user', {}).get('screen_name')
            return details, screen_name
        except Exception as e:
            self.logger.error(f"Error fetching tweet details for {tweet_id}: {str(e)}")
            return None, None

    async def _fetch_tweet_comments(self, tweet_id: str, screen_name: Optional[str]) -> List[Dict]:
        try:
            comments = await self.api_client.get_tweet_comments(tweet_id, screen_name)
            return comments['data'] if comments else []
        except Exception as e:
            self.logger.error(f"Error fetching comments for {tweet_id}: {str(e)}")
            return []

    async def _fetch_tweet_retweeters(self, tweet_id: str) -> List[Dict]:
        try:
            retweeters = await self.api_client.get_tweet_retweeters(tweet_id)
            return retweeters['data'] if retweeters else []
        except Exception as e:
            self.logger.error(f"Error fetching retweeters for {tweet_id}: {str(e)}")
            return []

    async def monitor_tweet(self, tweet_id: str) -> MonitoringRun:
        run_timestamp = int(datetime.now().timestamp())
        monitoring_run = MonitoringRun(tweet_id, run_timestamp)
        
        # Step 1: Fetch and save tweet details
        details, screen_name = await self._fetch_tweet_details(tweet_id)
        if details:
            try:
                self.tweet_data.save_tweet_details(
                    tweet_id=tweet_id,
                    details=details,
                    timestamp=str(run_timestamp)
                )
                monitoring_run.details_saved = True
                self.logger.info(f"Saved details for tweet {tweet_id}")
            except Exception as e:
                monitoring_run.add_error("details", str(e))
                self.logger.error(f"Error saving details for {tweet_id}: {str(e)}")
        else:
            monitoring_run.add_error("details", "Failed to fetch tweet details")
            self.logger.error(f"Failed to fetch details for tweet {tweet_id}")
            return monitoring_run

        # Step 2: Fetch and save new comments
        comments = await self._fetch_tweet_comments(tweet_id, screen_name)
        if comments:
            try:
                # Get existing comments to compare using the analysis repository
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
                    self.tweet_data.save_tweet_comments(
                        tweet_id=tweet_id,
                        comments=new_comments,
                        timestamp=str(run_timestamp)
                    )
                    monitoring_run.comments_saved = True
                    self.logger.info(f"Saved {len(new_comments)} new comments for tweet {tweet_id}")
                else:
                    monitoring_run.comments_saved = True
                    self.logger.info(f"No new comments for tweet {tweet_id}")
                    
            except Exception as e:
                monitoring_run.add_error("comments", str(e))
                self.logger.error(f"Error saving comments for {tweet_id}: {str(e)}")

        # Step 3: Fetch and save new retweeters
        retweeters = await self._fetch_tweet_retweeters(tweet_id)
        if retweeters:
            try:
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
                    self.tweet_data.save_tweet_retweeters(
                        tweet_id=tweet_id,
                        retweeters=new_retweeters,
                        timestamp=str(run_timestamp)
                    )
                    monitoring_run.retweeters_saved = True
                    self.logger.info(f"Saved {len(new_retweeters)} new retweeters for tweet {tweet_id}")
                else:
                    monitoring_run.retweeters_saved = True
                    self.logger.info(f"No new retweeters for tweet {tweet_id}")
                    
            except Exception as e:
                monitoring_run.add_error("retweeters", str(e))
                self.logger.error(f"Error saving retweeters for {tweet_id}: {str(e)}")

        try:
            self.tweet_data.update_tweet_check(tweet_id, str(run_timestamp))
        except Exception as e:
            monitoring_run.add_error("update_check", str(e))
            self.logger.error(f"Error updating last check time for {tweet_id}: {str(e)}")

        return monitoring_run

    async def monitor_all_tweets(self, interval_minutes: int = 5):
        while True:
            try:
                tweets = self.tweet_data.get_monitored_tweets()
                current_time = datetime.now().timestamp()
                
                for tweet in tweets:
                    if not tweet['is_active']:
                        continue
                        
                    tweet_age = current_time - int(tweet['created_at'])
                    hours_old = tweet_age / 3600
                    
                    if hours_old > 6 and int(tweet['last_check']) + 3600 > current_time:
                        continue
                    elif hours_old > 1 and int(tweet['last_check']) + 1200 > current_time:
                        continue
                    elif int(tweet['last_check']) + 300 > current_time:
                        continue
                        
                    run_result = await self.monitor_tweet(tweet['tweet_id'])
                    if not run_result.is_successful():
                        self.logger.warning(
                            f"Monitoring run for tweet {tweet['tweet_id']} had issues: "
                            f"{'; '.join(run_result.errors)}"
                        )
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
            finally:
                await asyncio.sleep(interval_minutes * 60)