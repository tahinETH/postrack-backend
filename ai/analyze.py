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

    async def analyze_tweet(self, tweet_id: str) -> Dict[str, Any]:
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
            claude_response = await self._get_claude_analysis(prompt)
            
            # Extract detailed analysis sections
            # Extract all detailed analysis sections into a single string
            detailed_analysis = ""
           
            
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
            Here is the tweet performance data in JSON format:

            <tweet_data>
            {json.dumps(insights)}
            </tweet_data>

            You are an experienced social media analyst tasked with analyzing tweet performance data and providing strategic, actionable insights. Your analysis should be accurate, efficient, and presented in a clear, formatted manner.

            Please analyze this data and provide a comprehensive report following these steps:

            1. Parse and examine the JSON data carefully.

            2. Conduct a thorough analysis covering the following areas:

            a) Virality Analysis
            b) Audience Response
            c) Growth Impact
            d) Amplification Patterns

            - List out key metrics and data points you need to consider
            - Show your calculations and intermediate findings
            - Draw initial conclusions based on your findings

            3. Based on your analysis, generate Strategic Insights. Consider both positive aspects of the tweet's performance and areas for improvement.

            4. Compile your findings into a formatted report with the following structure:

            I. Summary of Key Findings
                - Bullet points highlighting the most important insights (3-5 points)

            II. Detailed Analysis
                A. Virality Analysis
                    - Key inflection points in the tweet's spread
                    - Role of verified accounts and high-follower amplifiers
                    - Shifts in engagement patterns over time

                B. Audience Response
                    - Active vs. silent engagement ratio comparison
                    - Quality of engagement (comment/retweet ratios)
                    - Content resonance with casual viewers vs. active participants

                C. Growth Impact
                    - Follower growth patterns
                    - Correlation between verified engagement and follower growth
                    - Performance comparison against platform averages

                D. Amplification Patterns
                    - Profiles of top amplifiers
                    - Content spread patterns
                    - Impact of different engagement types (quotes vs. retweets)

            III. Strategic Insights
                    - Key factors contributing to the tweet's performance
                    - Patterns suggesting optimal posting or engagement strategies
                    - Lessons applicable to future content

            Remember to be concise and direct in your analysis and recommendations. Provide specific, actionable insights that can be applied to improve future social media performance. Answer in HTML format, use text styling to make it more readable.
            For each area, wrap your work inside <div className='section'> tags.
            Begin your analysis now, starting with the Virality Analysis section."""

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
