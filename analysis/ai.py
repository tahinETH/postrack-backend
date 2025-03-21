import json
import logging
import os
import anthropic
from typing import Dict, Any, Optional, List
from db.tw.structured import TweetStructuredRepository
from config import config

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self, analysis_repo: TweetStructuredRepository):
        self.analysis_repo = analysis_repo
        self.claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def generate_ai_analysis_tweet(self, tweet_id: str, with_ai: bool = False) -> Dict[str, Any]:
        """Get insights and AI analysis for a tweet"""
        try:
            # Get insight data
            insights = await self.analysis_repo.prepare_insight_data(tweet_id)
            if not insights:
                logger.warning(f"No insights found for tweet {tweet_id}")
                return {}

            # Prepare prompt for Claude
            prompt = self._prepare_claude_prompt(insights, type="tweet", metrics=None, account_data=None)
            
            # Get Claude's analysis
            claude_response = "_empty_"
            if with_ai:
                claude_response = await self._get_claude_analysis(prompt)
                if claude_response is None:
                    claude_response = "_empty_"
            
            # Save the analysis and input data
            await self.analysis_repo.tweet_data.save_ai_analysis(tweet_id, claude_response, insights)

            return {
                "insights": insights,
                "ai_analysis": claude_response
            }

        except Exception as e:
            logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
            raise

    async def generate_ai_analysis_metrics(self, metrics: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an account based on its tweets"""
        prompt = self._prepare_claude_prompt(insights=None, metrics=metrics, account_data=account_data, type="metrics")
        claude_response = await self._get_claude_analysis(prompt)
        return claude_response
    
    async def generate_ai_analysis_qualitative(self, insights: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an account based on its tweets"""
        cleaned_tweets = self._prepare_tweets_for_prompt(insights)
        prompt = self._prepare_claude_prompt(insights=cleaned_tweets, metrics=None,account_data=account_data, type="qualitative")
        claude_response = await self._get_claude_analysis(prompt)
        return claude_response
       
       
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
    

    def _prepare_claude_prompt(self, insights: Dict[str, Any] | None, metrics: Dict[str, Any] | None, account_data: Dict[str, Any] | None, type: str) -> str:
        """Prepare prompt for Claude based on insights data"""
        if type == "tweet":
            return f"""
            <tweet_data>
            {json.dumps(insights)}
            </tweet_data>

            You are a social media analyst. Analyze this tweet data and provide a concise report with:

            1. Virality Analysis
               - How quickly and widely did this tweet spread?
               - What were the key inflection points?
               - Which accounts had the biggest impact on amplification?

            2. Patterns
               - Unusual engagement patterns
               - Notable audience behaviors
               - Any surprising elements in how this content performed

            3. Recommendations
               - 2-3 specific, actionable suggestions to improve future tweet performance
               - What worked well that should be repeated
               - What could be improved

            Be direct and specific. Format your response in HTML with appropriate styling for readability.
            Wrap each section in <div className='section' id='section-name'> tags, section names being "virality", "patterns", and "recommendations".
            """


        elif type == "metrics":
            return f"""
            You are an AI assistant tasked with analyzing Twitter engagement metrics and providing insightful commentary. You will be given a set of calculated metrics and asked to interpret them, drawing conclusions about the Twitter account's performance and strategy.
            <account_data>
            {json.dumps(account_data)}
            </account_data>
            <metrics>
            {json.dumps(metrics)}
            </metrics>

            Run the following analyses on metrics: optimal length, media usage, quote analysis, favorite and retweet analysis, mention analysis, symbols analysis, urls analysis
        
           Present your analysis in the following format:
           <analysis>
            <section name="optimal length">
            [Your concise insightful commentary on optimal length and word length analysis]
            </section>
            <section name="media usage">
            [Your concise insightful commentary on media usage]
            </section>
            <section name="quote analysis">
            [Your concise insightful commentary on quote analysis]
            </section>
            <section name="favorite and retweet analysis">
            [Your concise insightful commentary on favorite and retweet analysis]
            </section>
            <section name="mention analysis">
            [Your concise insightful commentary on mention analysis]
            </section>
            <section name="symbols analysis">
            [Your concise insightful commentary on symbols analysis]
            </section>
            <section name="urls analysis">
            [Your concise insightful commentary on urls analysis]
            </section>
            <section name="word length analysis">
            [Your concise insightful commentary on word length analysis]
            </section>
            </analysis>
            
            



            """
        


        elif type == "qualitative":
            return f"""

            You are an AI assistant tasked with analyzing top tweets from an account and provide commentary on what made them successful. 
            You will be given a set of tweets and asked to interpret them, drawing conclusions about the Twitter account's performance and strategy.
            <account_data>
            {json.dumps(account_data)}
            </account_data>
            <tweets>
            {json.dumps(insights)}
            </tweets>
            
            Now, try to draw conclusions about the Twitter account's performance and strategy.
           
            Present your analysis in the following format:
            <analysis>
            <section name="content themes">
            [Your through analysis of the tweets]
            </section>
            <section name="most successful tweets">
            [Your through analysis of the tweets]
            </section>
            <section name="authenticity & voice">
            [Your through analysis of the tweets]
            </section>
            <section name="content format">
            [Your through analysis of the tweets]
            </section>
            <section name="growth strategy">
            [Your through analysis of the tweets]
            </section>
            <section name="community engagement">
            [Your through analysis of the tweets]
            </section>
            <section name="success formula">
            [Your through analysis of the tweets]
            </section>

            </analysis>
            
            """


    async def _get_claude_analysis(self, prompt: str) -> str:
        """Get analysis from Claude"""
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error getting Claude analysis: {str(e)}")
            return "Error getting AI analysis"
