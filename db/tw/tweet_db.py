from datetime import datetime
import json
from typing import Optional, List, Dict, Any, Tuple
import logging
from sqlalchemy import select
from db.migrations import get_async_session
from db.schemas import MonitoredTweet, TweetDetail, TweetComment, TweetQuote, TweetRetweeter, AIAnalysis, UserTrackedItem

logger = logging.getLogger(__name__)

class TweetDataRepository():
    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            tweet = result.scalars().first()
            return tweet.__dict__ if tweet else None
    
    async def get_latest_tweet_for_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet)
                .where(MonitoredTweet.account_id == account_id)
                .order_by(MonitoredTweet.created_at.desc())
                .limit(1)
            )
            tweet = result.scalars().first()
            return tweet.__dict__ if tweet else None
    
    async def get_tweets_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet)
                .where(MonitoredTweet.account_id == account_id)
                .order_by(MonitoredTweet.created_at.desc())
            )
            tweets = result.scalars().all()
            return [tweet.__dict__ for tweet in tweets]
    
    async def get_tweets_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get tweets for a user based on their tracked items"""
        async with get_async_session() as session:
            tracked_items = await session.execute(
                select(UserTrackedItem).where(UserTrackedItem.user_id == user_id)
            )
            
            tweets = []
            for item in tracked_items.scalars():
                if item.tracked_type == 'account':
                    # Get tweets for tracked account
                    account_tweets = await session.execute(
                        select(MonitoredTweet)
                        .where(MonitoredTweet.account_id == item.tracked_id)
                        .order_by(MonitoredTweet.created_at.desc())
                    )
                    for tweet in account_tweets.scalars():
                        tweets.append({
                            'tweet_id': tweet.tweet_id,
                            'created_at': tweet.created_at,
                            'is_active': tweet.is_active,
                            'tracking_type': 'account',
                            'tracked_id': item.tracked_id
                        })
                elif item.tracked_type == 'tweet':
                    # Get individual tracked tweet
                    tweet_result = await session.execute(
                        select(MonitoredTweet)
                        .where(MonitoredTweet.tweet_id == item.tracked_id)
                    )
                    tweet = tweet_result.scalars().first()
                    if tweet:
                        tweets.append({
                            'tweet_id': tweet.tweet_id,
                            'created_at': tweet.created_at,
                            'is_active': tweet.is_active,
                            'tracking_type': 'individual',
                            'tracked_id': item.tracked_id
                        })

            return tweets

    async def add_account_info_to_monitored_tweet(self, account_id: str, tweet_id: str, screen_name: Optional[str] = None):
        async with get_async_session() as session:
            tweet = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            existing_tweet = tweet.scalars().first()
            
            if existing_tweet:
                existing_tweet.account_id = account_id
                existing_tweet.user_screen_name = screen_name
                existing_tweet.is_active = True
            else:
                new_tweet = MonitoredTweet(
                    tweet_id=tweet_id,
                    account_id=account_id,
                    user_screen_name=screen_name,
                    is_active=True,
                    created_at=int(datetime.now().timestamp())
                )
                session.add(new_tweet)
            await session.commit()
    
    async def add_monitored_tweet(self, tweet_id: str, screen_name: Optional[str] = None):
        async with get_async_session() as session:
            tweet = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            existing_tweet = tweet.scalars().first()
            
            if existing_tweet:
                existing_tweet.user_screen_name = screen_name
                existing_tweet.is_active = True
            else:
                new_tweet = MonitoredTweet(
                    tweet_id=tweet_id,
                    user_screen_name=screen_name,
                    is_active=True,
                    created_at=int(datetime.now().timestamp())
                )
                session.add(new_tweet)
            await session.commit()

    async def stop_monitoring_tweet(self, tweet_id: str):
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            tweet = result.scalars().first()
            if tweet:
                tweet.is_active = False
                await session.commit()

    async def start_monitoring_tweet(self, tweet_id: str):
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            tweet = result.scalars().first()
            if tweet:
                tweet.is_active = True
                await session.commit()

    async def update_tweet_last_check(self, tweet_id: str, timestamp: Optional[int] = None):
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            tweet = result.scalars().first()
            if tweet:
                tweet.last_check = timestamp
                await session.commit()
    
    async def get_all_tweet_details(self, tweet_id: str) -> List[Tuple[str, int]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(TweetDetail.data_json, TweetDetail.captured_at)
                .where(TweetDetail.tweet_id == tweet_id)
                .order_by(TweetDetail.captured_at)
            )
            return result.all()

    async def get_latest_tweet_details(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(TweetDetail)
                .where(TweetDetail.tweet_id == tweet_id)
                .order_by(TweetDetail.captured_at.desc())
                .limit(1)
            )
            detail = result.scalars().first()
            return json.loads(detail.data_json) if detail else None
    
    async def save_tweet_details(self, tweet_id: str, details: Dict[str, Any], timestamp: Optional[int] = None):
        """Save tweet details with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_detail = TweetDetail(
                tweet_id=tweet_id,
                data_json=json.dumps(details),
                captured_at=timestamp
            )
            session.add(new_detail)
            await session.commit()
    
    async def remove_all_tweet_data(self, tweet_id: str):
        """Remove all data related to a tweet from all tables"""
        try:
            async with get_async_session() as session:
                await session.execute(
                    select(TweetDetail).where(TweetDetail.tweet_id == tweet_id).delete()
                )
                await session.execute(
                    select(TweetComment).where(TweetComment.tweet_id == tweet_id).delete()
                )
                await session.execute(
                    select(TweetRetweeter).where(TweetRetweeter.tweet_id == tweet_id).delete()
                )
                await session.execute(
                    select(AIAnalysis).where(AIAnalysis.tweet_id == tweet_id).delete()
                )
                await session.execute(
                    select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id).delete()
                )
                await session.commit()
                logger.info(f"Successfully removed all data for tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error removing data for tweet {tweet_id}: {str(e)}")
            raise
    
    async def get_tweet_comments(self, tweet_id: str) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(TweetComment).where(TweetComment.tweet_id == tweet_id)
            )
            return result.scalars().all()

    async def save_tweet_comments(self, tweet_id: str, comments: List[Dict[str, Any]], timestamp: Optional[int] = None):
        """Save tweet comments with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            for comment in comments:
                new_comment = TweetComment(
                    comment_id=comment['id'],
                    tweet_id=tweet_id,
                    data_json=json.dumps(comment),
                    captured_at=timestamp
                )
                session.add(new_comment)
            await session.commit()

    async def get_tweet_quotes(self, tweet_id: str) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(TweetQuote).where(TweetQuote.tweet_id == tweet_id)
            )
            return result.scalars().all()

    async def save_tweet_quotes(self, tweet_id: str, quotes: List[Dict[str, Any]], timestamp: Optional[int] = None):
        """Save tweet quotes with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            for quote in quotes:
                new_quote = TweetQuote(
                    quote_id=quote['id'],
                    tweet_id=tweet_id,
                    data_json=json.dumps(quote),
                    captured_at=timestamp
                )
                session.add(new_quote)
            await session.commit()
    async def get_tweet_retweeters(self, tweet_id: str) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(TweetRetweeter).where(TweetRetweeter.tweet_id == tweet_id)
            )
            return result.scalars().all()

    async def save_tweet_retweeters(self, tweet_id: str, retweeters: List[Dict[str, Any]], timestamp: Optional[int] = None):
        """Save tweet retweeters with timestamp"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            for retweeter in retweeters:
                new_retweeter = TweetRetweeter(
                    user_id=retweeter['id'],
                    tweet_id=tweet_id,
                    data_json=json.dumps(retweeter),
                    captured_at=timestamp
                )
                session.add(new_retweeter)
            await session.commit()

    async def get_monitored_tweets(self) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(select(MonitoredTweet))
            tweets = result.scalars().all()
            return [{
                'tweet_id': tweet.tweet_id,
                'user_screen_name': tweet.user_screen_name,
                'created_at': tweet.created_at,
                'last_check': tweet.last_check,
                'is_active': tweet.is_active
            } for tweet in tweets]
    
    async def save_ai_analysis(self, tweet_id: str, analysis: str, input_data: Dict[str, Any]):
        timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_analysis = AIAnalysis(
                tweet_id=tweet_id,
                analysis=analysis,
                input_data=json.dumps(input_data),
                created_at=timestamp
            )
            session.add(new_analysis)
            await session.commit()

    async def get_ai_analysis(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(AIAnalysis)
                .where(AIAnalysis.tweet_id == tweet_id)
                .order_by(AIAnalysis.created_at.desc())
                .limit(1)
            )
            analysis = result.scalars().first()
            return (analysis.analysis, analysis.input_data) if analysis else None

    async def get_latest_monitoring_run(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredTweet).where(MonitoredTweet.tweet_id == tweet_id)
            )
            tweet = result.scalars().first()
            return (tweet.last_check,) if tweet else None
