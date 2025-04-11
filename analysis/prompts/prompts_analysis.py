from typing import Dict, Any, List
import json

def prepare_tweet_ai_analysis_prompt(insights: Dict[str, Any] | None, metrics: Dict[str, Any] | None, account_data: Dict[str, Any] | None) -> str:
    
    
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


    
        
    


 
    

def prepare_account_ai_analysis_quantitative_prompt(metrics: Dict[str, Any] | None, account_data: Dict[str, Any] | None) -> str:
    
    return f"""
            You are an AI assistant tasked with analyzing Twitter engagement metrics and providing insightful commentary. You will be given a set of calculated metrics and asked to interpret them, drawing conclusions about the Twitter account's performance and strategy.
            <account_data>
            {json.dumps(account_data)}
            </account_data>
            <metrics>
            {json.dumps(metrics)}
            </metrics>

            Run the following analyses on metrics: optimal length, media usage, quote analysis, favorite and retweet analysis, mention analysis, symbols analysis, urls analysis.
        
        Present your analysis in the following format:
        <analysis>
            <section name="optimal length">
            [Your concise analytical, insightful, bullet pointed commentary on optimal length and word length analysis]
            </section>
            <section name="media usage">
            [Your concise analytical, insightful, bullet pointed commentary on media usage]
            </section>
            <section name="quote analysis">
            [Your concise analytical, insightful, bullet pointed commentary on quote analysis]
            </section>
            <section name="temporal analysis">
            [Your concise analytical, insightful, bullet pointed commentary on temporal analysis]
            </section>
            <section name="favorite and retweet analysis">
            [Your concise analytical, insightful, bullet pointed commentary on favorite and retweet analysis]
            </section>
            <section name="mention analysis">
            [Your concise analytical, insightful, bullet pointed commentary on mention analysis]
            </section>
            <section name="symbols analysis">
            [Your concise analytical, insightful, bullet pointed commentary on symbols analysis]
            </section>
            <section name="urls analysis">
            [Your concise analytical, insightful, bullet pointed commentary on urls analysis]
            </section>
            <section name="word length analysis">
            [Your concise analytical, insightful, bullet pointed commentary on word length analysis]
            </section>
            </analysis>
            
            
            Use bullet points. 


            """

def prepare_account_ai_analysis_qualitative_prompt(insights: Dict[str, Any] | None, account_data: Dict[str, Any] | None) -> str:

       
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
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="most successful tweets">
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="authenticity & voice">
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="content format">
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="growth strategy">
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="community engagement">
        [Your through analysis of the tweets, bullet pointed]
        </section>
        <section name="success formula">
        [Your through analysis of the tweets, bullet pointed]
        </section>

        </analysis>

        Use bullet points.
        
        """