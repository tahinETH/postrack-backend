import json
import logging
import os
import anthropic
from typing import Dict, Any, Optional
from db.tw.structured import TweetStructuredRepository
from config import config

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self, analysis_repo: TweetStructuredRepository):
        self.analysis_repo = analysis_repo
        self.claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def analyze_tweet(self, tweet_id: str, with_ai: bool = False) -> Dict[str, Any]:
        """Get insights and AI analysis for a tweet"""
        try:
            # Get insight data
            insights = await self.analysis_repo.prepare_insight_data(tweet_id)
            if not insights:
                logger.warning(f"No insights found for tweet {tweet_id}")
                return {}

            # Prepare prompt for Claude
            prompt = self._prepare_claude_prompt(insights)
            
            # Get Claude's analysis
            claude_response = None
            if with_ai:
                claude_response = await self._get_claude_analysis(prompt)
            
            # Extract detailed analysis sections
            # Extract all detailed analysis sections into a single string
            
           
            
            # Save the analysis and input data
            await self.analysis_repo.tweet_data.save_ai_analysis(tweet_id, claude_response, insights)

            return {
                "insights": insights,
                "ai_analysis": claude_response
            }

        except Exception as e:
            logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
            raise

    def _prepare_claude_prompt(self, insights: Dict[str, Any]) -> str:
        """Prepare prompt for Claude based on insights data"""
    
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
