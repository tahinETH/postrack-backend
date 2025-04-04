import time
import asyncio
from typing import Dict, Optional, List, Tuple
import logging
from db.migrations import get_async_session
from db.users.user_db import UserDataRepository
from db.tw.tweet_db import TweetDataRepository
from db.tw.structured import TweetStructuredRepository
from db.tw.account_db import AccountRepository
from analysis.ai import AIAnalyzer
from analysis.account import AccountAnalyzer
from analysis.workshop import Workshop
from api_client import TwitterAPIClient
from monitor import TweetMonitor
from datetime import datetime
from config import config


from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DB_PATH = config.DB_PATH
SOCIAL_DATA_API_KEY = config.SOCIAL_DATA_API_KEY





class SubscriptionTier:
    def __init__(self, tier_id: str, max_accounts: int, max_tweets: int, max_analysis: int, max_followers: int):
        self.tier_id = tier_id
        self.max_accounts = max_accounts
        self.max_tweets = max_tweets
        self.max_analysis = max_analysis
        self.max_followers = max_followers

class SubscriptionTiers:
    FREE = SubscriptionTier('tier0', 0, 1, 5, 5000)
    PREMIUM = SubscriptionTier('tier1', 0, 1, 5, 50000) 
    ADMIN = SubscriptionTier('admin', 1000, 1000, 20, 1000000000)

    @classmethod 
    def get_tier(cls, tier_id: str) -> Optional[SubscriptionTier]:
        return getattr(cls, tier_id.upper(), cls.FREE)

class Service:
    def __init__(self):
        self.user_repository = UserDataRepository()
        self.monitor = TweetMonitor(DB_PATH, SOCIAL_DATA_API_KEY)
        self.data = TweetDataRepository()
        self.analysis = TweetStructuredRepository()
        self.accounts = AccountRepository()
        self.ai_analyzer = AIAnalyzer(self.analysis)
        self.account_analyzer = AccountAnalyzer(self.analysis, SOCIAL_DATA_API_KEY)
        self.api_client = TwitterAPIClient(SOCIAL_DATA_API_KEY)
        self.content_workshop = Workshop()

    async def _get_user_limits(self, user_id: str) -> Tuple[int, int]:
        """Get user's max allowed accounts and tweets based on their tier"""
        user = await self.user_repository.get_user(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
            
        tier = SubscriptionTiers.get_tier(user['current_tier'])
        
        return tier.max_accounts, tier.max_tweets, tier.max_analysis, tier.max_followers

    async def get_user(self, user_id: str) -> Dict:
        """Get user details"""
        user = await self.user_repository.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    async def _can_track_account(self, user_id: str) -> bool:
        """Check if user can track another account based on their tier limits"""
        try:
            max_accounts, _, _, max_followers = await self._get_user_limits(user_id)
            tracked_items = await self.user_repository.get_tracked_items(user_id)
            current_accounts = len(tracked_items['accounts'])

            return current_accounts < max_accounts, max_followers
            
        except Exception as e:
            logger.error(f"Error checking account tracking limit for user {user_id}: {str(e)}")
            raise

    async def _can_track_analysis(self, user_id: str) -> bool:
        """Check if user can track another analysis based on their tier limits"""
        try:
            _, _, max_analysis, _ = await self._get_user_limits(user_id)
            tracked_items = await self.user_repository.get_tracked_items(user_id)
            current_analysis = len(tracked_items['analysis'])
            return current_analysis < max_analysis
        except Exception as e:
            logger.error(f"Error checking analysis tracking limit for user {user_id}: {str(e)}")
            raise
            
    async def _can_track_tweet(self, user_id: str) -> bool:
        """Check if user can track another tweet based on their tier limits"""
        try:
            _, max_tweets, _, max_followers = await self._get_user_limits(user_id)
            tracked_items = await self.user_repository.get_tracked_items(user_id)
            current_tweets = len(tracked_items['tweets'])
            
            return current_tweets < max_tweets
            
        except Exception as e:
            logger.error(f"Error checking tweet tracking limit for user {user_id}: {str(e)}")
            raise

    async def handle_account_monitoring(self, user_id: str, account_identifier: str, action: str) -> bool:
        """Handle starting or stopping monitoring of an account"""
        try:
            if action == "start":
                can_track_account, max_followers = await self._can_track_account(user_id)
                if not can_track_account:
                    raise ValueError("Account tracking limit reached for user's tier")
                account_id = await self.monitor.monitor_account(screen_name=account_identifier, max_followers= max_followers, user_id=user_id)
                
                if account_id:  
                    await self.user_repository.add_tracked_item(user_id, "account", account_id, account_identifier)
                    logger.info(f"Started monitoring account {account_identifier} for user {user_id}")
                    return True
                return False

            elif action == "stop":
                success = await self.user_repository.remove_tracked_item(user_id, "account", account_identifier)
                if success:
                    logger.info(f"Stopped monitoring account {account_identifier} for user {user_id}")
                return success

            else:
                raise ValueError("Invalid action. Must be 'start' or 'stop'")

        except Exception as e:
            logger.error(f"Error handling account monitoring for user {user_id}: {str(e)}")
            raise
            

    async def handle_tweet_monitoring(self, user_id: str, tweet_id: str, action: str) -> bool:
        """Handle starting or stopping monitoring of a tweet"""
        try:
            
            if action == "start":
                if not await self._can_track_tweet(user_id):
                    raise ValueError("Tweet tracking limit reached for user's tier")

                # Check if tweet exists first
                
                existing_tweet = await self.monitor.tweet_data.get_tweet_by_id(tweet_id)
                
                
                if existing_tweet:
                    #db
                    await self.monitor.tweet_data.start_monitoring_tweet(tweet_id)
                else:
                    #db
                   await self.monitor.tweet_data.add_monitored_tweet(tweet_id)
                    
                
                
                monitoring_run = await self.monitor.monitor_tweet(tweet_id=tweet_id)
                
            

                if monitoring_run.details_saved:
                    details, screen_name = await self.monitor._fetch_tweet_details(tweet_id)
                    
                    # Add to user's tracked items
                    await self.user_repository.add_tracked_item(user_id, "tweet", tweet_id, screen_name)
                    logger.info(f"Started monitoring tweet {tweet_id} for user {user_id}")
                    return True
                return False

            elif action == "stop":
                success = await self.user_repository.remove_tracked_item(user_id, "tweet", tweet_id)
                if success:
                    is_tweet_tracked = await self.user_repository.is_tweet_tracked(tweet_id)
                    if not is_tweet_tracked:
                        self.monitor.tweet_data.stop_monitoring_tweet(tweet_id)
                    logger.info(f"Stopped monitoring tweet {tweet_id} for user {user_id}")
                return success

            else:
                raise ValueError("Invalid action. Must be 'start' or 'stop'")

        except Exception as e:
            logger.error(f"Error handling tweet monitoring for user {user_id}: {str(e)}")
            raise

    async def get_monitored_tweets(self) -> List[Dict]:
        """Get all monitored tweets"""
        try:
            tweets = await self.monitor.tweet_data.get_monitored_tweets()
            logger.info(f"Retrieved {len(tweets)} monitored tweets")
            return tweets
        except Exception as e:
            logger.error(f"Error getting monitored tweets: {str(e)}")
            raise

    async def get_account_analysis(self, account_id: str, user_id: str) -> Dict:
        """Get account analysis"""
        try:
            result = await self.account_analyzer.get_account_analysis(account_id, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting account analysis: {str(e)}")
            raise
    async def delete_account_analysis(self,user_id:str, account_id:str) -> Dict:
        """Delete account analysis"""
        try:
            result = await self.accounts.delete_account_analysis(user_id, account_id)
            # Remove tracked item for the user
            await self.user_repository.remove_tracked_item(user_id, "analysis", account_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting account analysis: {str(e)}")
            raise

    async def analyze_account(self, screen_name: str, new_fetch: bool = False, user_id: str = None) -> Dict:
        if not await self._can_track_analysis(user_id):
            raise ValueError("Analysis tracking limit reached for user's tier")
        try:
            account = await self.api_client.api_get_account_by_screen_name(screen_name)
        except:
            raise ValueError(f"Account {screen_name} not found")
        account_id = account['id_str']

        try:
            await self.user_repository.add_tracked_item(user_id, "analysis", account_id, screen_name)
        except:
            raise ValueError(f"Account {screen_name} already tracked")
        
        try:
            result = await self.account_analyzer.analyze_account(account_id, new_fetch, account_data=account, user_id=user_id)
            logger.info(f"Generated AI analysis for account {account_id}")
            return result
        except Exception as e:
            logger.error(f"Error analyzing account {account_id}: {str(e)}")
            raise
       
       
        
    async def analyze_tweet(self, tweet_id: str, with_ai: bool = False) -> Dict:
        """Get AI analysis for a tweet"""
        try:
            result = await self.ai_analyzer.generate_ai_analysis_tweet(tweet_id, with_ai)
            logger.info(f"Generated AI analysis for tweet {tweet_id}")
            return result
        except Exception as e:
            logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
            raise

    async def get_user_feed(self, user_id: str, skip: int = 0, limit: int = 20, type: str = "time", sort: str = "desc") -> Dict:
        """Get paginated feed for a user"""
        try:
            feed = await self.analysis.get_user_feed(user_id, skip, limit, type, sort)
            logger.info(f"Retrieved paginated feed for user {user_id}")
            return feed
        except Exception as e:
            logger.error(f"Error getting feed for user {user_id}: {str(e)}")
            raise

    async def get_tweet_history(self, tweet_id: str, format: str) -> Dict:
        """Get tweet history in raw or analyzed format"""
        try:
            if format == "raw":
                history = await self.analysis.get_raw_tweet_history(tweet_id)
            else:  # format == "analyzed"
                history = await self.analysis.get_analyzed_tweet_history(tweet_id)
                
            
            if not history:
                logger.warning(f"Tweet history not found for {tweet_id}")
                return None
                
            logger.info(f"Retrieved {format} history for tweet {tweet_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error getting {format} tweet history for {tweet_id}: {str(e)}")
            raise




        ### ADMIN FUNCTIONs ###
    async def handle_all_accounts(self, action: str) -> bool:
        """Handle starting or stopping monitoring of all accounts"""
        try:
            if action == "start":
                self.monitor.accounts.start_all_accounts()
                logger.info("Started monitoring all accounts")
                return True
            elif action == "stop":
                self.monitor.accounts.stop_all_accounts() 
                logger.info("Stopped monitoring all accounts")
                return True
            else:
                raise ValueError("Invalid action. Must be 'start' or 'stop'")
        except Exception as e:
            logger.error(f"Error handling all accounts monitoring: {str(e)}")
            raise
        
    async def handle_all_tweets(self, action: str) -> bool:
        """Handle starting or stopping monitoring of all tweets"""
        try:
            tweets = await self.monitor.tweet_data.get_monitored_tweets()
            count = 0

            if action == "start":
                for tweet in tweets:
                    if not tweet['is_active']:
                        await self.monitor.tweet_data.add_monitored_tweet(tweet['tweet_id'])
                        await self.monitor.monitor_tweet(tweet_id = tweet['tweet_id'])
                        count += 1
                logger.info(f"Started monitoring {count} inactive tweets")
                return True

            elif action == "stop":
                for tweet in tweets:
                    if tweet['is_active']:
                        self.monitor.tweet_data.stop_monitoring_tweet(tweet['tweet_id'])
                        count += 1
                logger.info(f"Stopped monitoring {count} active tweets")
                return True

            else:
                raise ValueError("Invalid action. Must be 'start-all' or 'stop-all'")

        except Exception as e:
            action_type = "starting" if action == "start-all" else "stopping"
            logger.error(f"Error {action_type} all tweet monitoring: {str(e)}")
            raise





    async def get_content_inspiration(self, tweet_id: str, account_id: str, is_thread: bool, user_id: str, additional_commands: str) -> str:
        """Get content inspiration ideas for a tweet"""
        try:
            inspiration = await self.content_workshop.workshop_inspiration(tweet_id, account_id, is_thread, user_id, additional_commands)
            return inspiration
        except Exception as e:
            logger.error(f"Error getting content inspiration for tweet {tweet_id}: {str(e)}")
            raise

    async def get_tweet_refinements(self, user_id: str, tweet_text: str, account_id: str, additional_commands: str) -> str:
        """Get refinement suggestions for a tweet"""
        try:
            refinements = await self.content_workshop.workshop_refine(user_id, tweet_text, account_id, additional_commands)
            return refinements
        except Exception as e:
            logger.error(f"Error getting tweet refinements service: {str(e)}")
            raise

    async def get_visualization_ideas(self, tweet_text: str) -> str:
        """Get visualization ideas for a tweet"""
        try:
            ideas = await self.content_workshop.workshop_visualization(tweet_text)
            return ideas
        except Exception as e:
            logger.error(f"Error getting visualization ideas: {str(e)}")
            raise



    ## PERIODIC CHECKS ##
    async def check_single_tweet(self, timestamp: int):
        """Single run of tweet check and update"""
        try:
            logger.info(f"Running periodic tweet check at {timestamp}")
            await self.monitor.check_and_update_tweets()
        except Exception as e:
            logger.error(f"Error in tweet check at {timestamp}: {str(e)}")

    async def check_account(self, timestamp: int):
        """Single run of account check and update"""
        try:
            logger.info(f"Running periodic account check at {timestamp}")
            await self.monitor.check_and_update_accounts()
        except Exception as e:
            logger.error(f"Error in account check at {timestamp}: {str(e)}")


    async def handle_periodic_checks(self):
        """Periodic task to check and update tweets and accounts"""
        while True:
            timestamp = int(time.time())
            
            try:
                await self.check_single_tweet(timestamp)
            except Exception as e:
                logger.error(f"Error checking tweets at {int(time.time())}: {str(e)}")

            try:
                await self.check_account(timestamp)
            except Exception as e:
                logger.error(f"Error checking accounts at {int(time.time())}: {str(e)}")
            await asyncio.sleep(60)
   
