from typing import Optional, Dict
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.migrations import get_async_session
from db.schemas import APICall

logger = logging.getLogger(__name__)

class APICallLogRepository():
    async def upsert_api_calls(self, monitor_timestamp: int, tweet_details_calls: int = 0,
                        retweet_api_calls: int = 0, quote_api_calls: int = 0,
                        comment_api_calls: int = 0, total_api_calls: int = 0) -> None:
        """Log API calls for a monitoring timestamp"""
        try:
            async with await get_async_session() as session:
                result = await session.execute(
                    select(APICall).filter(APICall.monitor_timestamp == monitor_timestamp)
                )
                api_call = result.scalars().first()

                if api_call:
                    api_call.tweet_details_calls = tweet_details_calls
                    api_call.retweet_api_calls = retweet_api_calls
                    api_call.quote_api_calls = quote_api_calls
                    api_call.comment_api_calls = comment_api_calls
                    api_call.total_api_calls = total_api_calls
                else:
                    new_api_call = APICall(
                        monitor_timestamp=monitor_timestamp,
                        tweet_details_calls=tweet_details_calls,
                        retweet_api_calls=retweet_api_calls,
                        quote_api_calls=quote_api_calls,
                        comment_api_calls=comment_api_calls,
                        total_api_calls=total_api_calls
                    )
                    session.add(new_api_call)
                await session.commit()
                logger.info(f"Logged API calls for timestamp {monitor_timestamp}")
        except Exception as e:
            logger.error(f"Error logging API calls for timestamp {monitor_timestamp}: {str(e)}")
            raise

    async def get_api_calls(self, monitor_timestamp: int) -> Optional[Dict[str, int]]:
        """Get API call logs for a specific timestamp"""
        try:
            async with await get_async_session() as session:
                result = await session.execute(
                    select(APICall).filter(APICall.monitor_timestamp == monitor_timestamp)
                )
                api_call = result.scalars().first()
                
                if api_call:
                    return {
                        'tweet_details_calls': api_call.tweet_details_calls,
                        'retweet_api_calls': api_call.retweet_api_calls,
                        'quote_api_calls': api_call.quote_api_calls,
                        'comment_api_calls': api_call.comment_api_calls,
                        'total_api_calls': api_call.total_api_calls
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting API calls for timestamp {monitor_timestamp}: {str(e)}")
            raise
