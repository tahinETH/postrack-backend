import json
import logging
import asyncio
from typing import Dict, Any, List, Tuple
from db.tw.structured import TweetStructuredRepository
from db.tw.community_db import CommunityRepository
from api_client import TwitterAPIClient
from analysis.ai import AIAnalyzer

logger = logging.getLogger(__name__)

class CommunityAnalyzer:
    def __init__(self, analysis_repo: TweetStructuredRepository, community_repo: CommunityRepository, api_key: str):
        self.analysis_repo = analysis_repo
        self.community_repo = community_repo
        self.ai = AIAnalyzer(analysis_repo)
        self.api_client = TwitterAPIClient(api_key)

    async def _fetch_community_data(self, community_id: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch community details and top tweets"""
        # First get community details
        community_details = await self.api_client.api_get_community(community_id)
        if not community_details:
            raise ValueError("Could not fetch community details")
            
        # Then get top tweets
        tweets = await self.api_client.api_get_community_top_tweets(community_id, limit=200)
        if not tweets:
            raise ValueError("Could not fetch community tweets")
            
        return community_details, tweets

    async def get_community_analysis(self, community_id: str, user_id: str) -> Dict[str, Any]:
        """Get community analysis"""
        existing_analysis = await self.analysis_repo.get_community_analysis(community_id, user_id)
        return existing_analysis

    async def clean_community_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_tweets = []
        for tweet in tweets:
            cleaned_tweet = {
                'tweet_created_at': tweet.get('tweet_created_at'),
                'id': tweet.get('id'),
                'id_str': tweet.get('id_str'),
                'full_text': tweet.get('full_text', ''),
                'favorite_count': tweet.get('favorite_count', 0),
                'retweet_count': tweet.get('retweet_count', 0),
                'reply_count': tweet.get('reply_count', 0),
                'quote_count': tweet.get('quote_count', 0),
                'views_count': 0 if tweet.get('views_count') is None else tweet.get('views_count'),
                'bookmark_count': tweet.get('bookmark_count', 0),
                'is_quote_status': tweet.get('is_quote_status', False),
                'quoted_status_id_str': tweet.get('quoted_status_id_str'),
                'retweeted_status': tweet.get('retweeted_status'),
                'entities': tweet.get('entities'),
                'source': tweet.get('source'),
                'user': tweet.get('user'),
            }
            cleaned_tweets.append(cleaned_tweet)
        return cleaned_tweets

    async def analyze_community(self, community_id: str, new_fetch: bool = False, user_id: str = None) -> Dict[str, Any]:
        """Analyze a community"""
        try:
            existing_analysis = await self.analysis_repo.get_community_analysis(community_id, user_id)

            if new_fetch or not existing_analysis:
                try:
                    community_details, tweets = await self._fetch_community_data(community_id)
                except Exception as e:
                    logger.error(f"Error fetching community data: {str(e)}")
                    raise

                try:
                    cleaned_tweets = await self.clean_community_tweets(tweets)
                except Exception as e:
                    logger.error(f"Error cleaning community tweets: {str(e)}")
                    raise

                try:
                    analysis = await self.ai.generate_ai_analysis_community(cleaned_tweets)
                except Exception as e:
                    logger.error(f"Error generating community analysis: {str(e)}")
                    raise

                try:
                    await self.analysis_repo.save_community_analysis(
                        user_id,
                        community_id,
                        cleaned_tweets,
                        analysis,
                        details=community_details
                    )
                except Exception as e:
                    logger.error(f"Error saving community analysis: {str(e)}")
                    raise

                return {
                    "tweets": cleaned_tweets,
                    "analysis": analysis,
                    "details": community_details
                }

            return existing_analysis

        except Exception as e:
            logger.error(f"Error analyzing community: {str(e)}")
            raise
