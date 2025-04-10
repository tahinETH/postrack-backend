import json
import logging
import os
from typing import Dict, Any, Optional, List
from db.tw.structured import TweetStructuredRepository
from config import config
from analysis.prompts.prompts_analysis import prepare_tweet_ai_analysis_prompt, prepare_account_ai_analysis_quantitative_prompt, prepare_account_ai_analysis_qualitative_prompt
logger = logging.getLogger(__name__)

from litellm import completion


class AIAnalyzer:
    def __init__(self, analysis_repo: TweetStructuredRepository):
        self.analysis_repo = analysis_repo

    async def generate_ai_analysis_tweet(self, tweet_id: str, with_ai: bool = False) -> Dict[str, Any]:
        """Get insights and AI analysis for a tweet"""
        try:
            # Get insight data
            insights = await self.analysis_repo.prepare_insight_data(tweet_id)
            if not insights:
                logger.warning(f"No insights found for tweet {tweet_id}")
                return {}

            # Prepare prompt for llm
            prompt = prepare_tweet_ai_analysis_prompt(insights, metrics=None, account_data=None)
            
            # Get llm's analysis
            llm_response = "_empty_"
            if with_ai:
                llm_response = await self._get_llm_analysis(prompt)
                if llm_response is None:
                    llm_response = "_empty_"
            
            # Save the analysis and input data
            await self.analysis_repo.tweet_data.save_ai_analysis(tweet_id, llm_response, insights)

            return {
                "insights": insights,
                "ai_analysis": llm_response
            }

        except Exception as e:
            logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
            raise

    async def generate_ai_analysis_metrics(self, metrics: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an account based on its tweets"""
        prompt = prepare_account_ai_analysis_quantitative_prompt(metrics=metrics, account_data=account_data)
        llm_response = await self._get_llm_analysis(prompt)
        return llm_response
    
    async def generate_ai_analysis_qualitative(self, insights: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an account based on its tweets"""
        cleaned_tweets = self._prepare_tweets_for_prompt(insights)
        prompt = prepare_account_ai_analysis_qualitative_prompt(insights=cleaned_tweets, account_data=account_data)
        llm_response = await self._get_llm_analysis(prompt)
        return llm_response
       
       
    def _prepare_tweets_for_prompt(self, insights: Dict[str, Any]) -> str:
        cleaned_tweets = []
        for tweet in insights:
            cleaned_tweet = {
                'full_text': tweet.get('full_text', ''),
                'views_count': tweet.get('views_count', 0),
                'bookmark_count': tweet.get('bookmark_count', 0),
                'favorite_count': tweet.get('favorite_count', 0),
                'retweet_count': tweet.get('retweet_count', 0),
                'reply_count': tweet.get('reply_count', 0),
                'quote_count': tweet.get('quote_count', 0),
                'is_quote_status': tweet.get('is_quote_status', False)
            }
            cleaned_tweets.append(cleaned_tweet)
        return cleaned_tweets
    


    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from llm"""
        try:
            response = completion(
                model="chatgpt-4o-latest",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting llm analysis: {str(e)}")
            return "Error getting AI analysis"
