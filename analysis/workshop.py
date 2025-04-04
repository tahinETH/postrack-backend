import json
import logging
import os
from typing import Dict, Any, Optional, List
from db.tw.structured import TweetStructuredRepository
from config import config
from analysis.prompts import (
    prepare_content_inspiration_prompt,
    prepare_tweet_refinement_prompt,
    prepare_visualization_prompt
)
from api_client import TwitterAPIClient
from analysis.account import AccountAnalyzer
from db.workshop.workshop_db import WorkshopRepository
from litellm import completion

logger = logging.getLogger(__name__)

class Workshop:
    def __init__(self):
        
        self.api_client = TwitterAPIClient(api_key=config.SOCIAL_DATA_API_KEY)
        self.analysis_repo = TweetStructuredRepository()
        self.accounts = AccountAnalyzer(self.analysis_repo, config.SOCIAL_DATA_API_KEY)
        self.workshop_repo = WorkshopRepository()

    async def _get_tweet_text(self, tweet_id: str, is_thread: bool = False) -> Optional[str]:
        if is_thread:
            thread_tweets = await self.api_client.api_get_thread_tweets(tweet_id)
            if thread_tweets:
                thread_text = "This is a thread:\n\n"
                for i, tweet in enumerate(thread_tweets, 1):
                    thread_text += f"Post {i}:\n{tweet.get('full_text')}\n\n"
                return thread_text
        else:
            tweet_data = await self.api_client.api_get_tweet(tweet_id)
            if tweet_data:
                if tweet_data.get('is_quote_status') and tweet_data.get('quoted_status'):
                    quoted_text = tweet_data['quoted_status'].get('full_text', '')
                    tweet_text = tweet_data.get('full_text', '')
                    return f"{tweet_text}\n\nQuoted tweet:\n{quoted_text}"
                return tweet_data.get('full_text')
        return None

    async def clean_tweets(self, tweets: List[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cleaned_tweets = []
        tweets_to_process = tweets[:limit] if limit else tweets
        
        for tweet in tweets_to_process:
            cleaned_tweet = {
                'tweet_created_at': tweet.get('created_at'),
                'id': tweet.get('id'),
                'id_str': tweet.get('id_str'), 
                'full_text': tweet.get('full_text', ''),
                'favorite_count': tweet.get('favorite_count', 0),
                'retweet_count': tweet.get('retweet_count', 0),
                'reply_count': tweet.get('reply_count', 0),
                'quote_count': tweet.get('quote_count', 0),
                'views_count': tweet.get('views_count', 0),
                'bookmark_count': tweet.get('bookmark_count', 0),
                'is_quote_status': tweet.get('is_quote_status', False),
                'quoted_status_id_str': tweet.get('quoted_status_id_str'),
                'retweeted_status': tweet.get('retweeted_status'),
                'entities': tweet.get('entities'),
            }
            cleaned_tweets.append(cleaned_tweet)
        
        if limit == None:
            return cleaned_tweets
        else:
            return [tweet.get('full_text', '') for tweet in cleaned_tweets]

    async def workshop_inspiration(self, tweet_id: str, account_id: str, is_thread: bool, user_id: str, additional_commands: str) -> str:
        
        try:
            tweet_text = await self._get_tweet_text(tweet_id, is_thread)
            if not tweet_text:
                return "Error: Could not retrieve tweet"
            try:
                analysis = await self.accounts.get_account_analysis(account_id, user_id)
                raw_tweets = analysis.get('top_tweets', [])
                example_posts = await self.clean_tweets(raw_tweets, limit=20)
            except Exception as e:
                logger.error(f"Error getting example posts: {str(e)}")
                example_posts = {}
            
            prompt = prepare_content_inspiration_prompt(example_posts, [tweet_text], additional_commands)
            response = completion(
                model="chatgpt-4o-latest",
                max_tokens=2000,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            result = response.choices[0].message.content
            
            # Save the inspiration
            await self.workshop_repo.save_inspiration(
                user_id=user_id,
                tweet_id=tweet_id,
                prompt=prompt,
                result=result,
                account_id=account_id,
                is_thread=is_thread
            )
            
            return result
        except Exception as e:
            logger.error(f"Error getting content inspiration: {str(e)}")
            return "Error generating content inspiration"

    async def workshop_refine(self, user_id: str, tweet_text: str, account_id: str, additional_commands: str) -> str:
        try:
            if not tweet_text:
                return "Error: Could not retrieve tweet"

            analysis = await self.accounts.get_account_analysis(account_id, user_id)
            
            raw_tweets = analysis.get('top_tweets', [])
            example_posts = await self.clean_tweets(raw_tweets, limit=20)
            prompt = prepare_tweet_refinement_prompt(tweet_text, example_posts, additional_commands)
            response = completion(
                model="chatgpt-4o-latest", 
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            result = response.choices[0].message.content
            
            # Save the refinement
            await self.workshop_repo.save_refinement(
                user_id=user_id,
                tweet_draft=tweet_text,
                result=result,
                prompt=prompt,
                account_id=account_id,
                additional_commands=additional_commands
            )
            
            return result
        except Exception as e:
            logger.error(f"Error getting tweet refinements workshop: {str(e)}")
            return "Error refining tweet"

    async def workshop_visualization(self, tweet_text: str) -> str:
        try:
            prompt = prepare_visualization_prompt(tweet_text)
            response = completion(
                model="chatgpt-4o-latest",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            result = response.choices[0].message.content
            return result
        except Exception as e:
            logger.error(f"Error generating visualization ideas: {str(e)}")
            return "Error generating visualization ideas"
