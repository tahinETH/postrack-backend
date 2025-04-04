import json
from typing import Dict, Any, List


def prepare_llm_prompt(insights: Dict[str, Any] | None, metrics: Dict[str, Any] | None, account_data: Dict[str, Any] | None, type: str) -> str:
    
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
        [Your concise analytical, insightful, bullet pointed commentary on optimal length and word length analysis]
        </section>
        <section name="media usage">
        [Your concise analytical, insightful, bullet pointed commentary on media usage]
        </section>
        <section name="quote analysis">
        [Your concise analytical, insightful, bullet pointed commentary on quote analysis]
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
    




def prepare_content_inspiration_prompt(example_posts:  Dict[str, Any], tweet: str, additional_commands: str) -> str:
     
     
     

     return(
        f"""
         You are an AI assistant helping a social media content creator generate ideas for new posts. Your task is to suggest topics and points to explore based on their previous content and a provided resource.

        <example_posts>
        {json.dumps(example_posts)}
        </example_posts>

        <discussion_source>
        {tweet}
        </discussion_source>

        <additional_commands_from_user>
        {additional_commands}
        </additional_commands_from_user>

        dicussion_source contains a tweet or a thread. i want you to help me come up with ideas to respond to or expand upon the content shared under discussion_source. Please generate a list of potential conversation points, topics, orthogonal or parallel ideas and frameworks that i can explore in response to the content shared. i want you to provide your topic ideas in TWO different sections: 

        5 ideas that you get from example_posts, following the format below: 

        <dependent_ideas>
        1) A way to engage with the discussion source

        Example: An example of a reply or quote tweet that does this

        1) A way to engage with the discussion source
        
        Example: An example of a reply or quote tweet that does this
        ...
        </dependent_ideas>

        
        5 ideas that you think are good fit even though they are not discussed in the example_posts, following the format below: 
        
        <independent_ideas>
        1) A way to engage with the discussion source

        Example: An example of a reply or quote tweet that does this
        
        1) A way to engage with the discussion source
        
        Example: An example of a reply or quote tweet that does this
        ...
        </independent_ideas>

        <additional_instructions>
        Output based on the additional instructions.
        </additional_instructions>

        for independent ideas, i want you to be very creative, providing also esoteric and outlier ideas. 
        do not provide posts to share. give me areas i can explore. always enclose your response in tags.
        
       

        

        """
        )


def prepare_tweet_refinement_prompt(tweet: str, example_posts: Dict[str, Any], additional_commands: str) -> str:
    additional_instructions = ""
    if additional_commands:
        additional_instructions = f"""
Additional instructions for improvement:
<additional_commands>
{additional_commands}
</additional_commands>
            """

    return f"""
You are an AI assistant tasked with improving a tweet draft. Your goal is to enhance the tweet's language, suggest alternative wordings, and propose relevant technical terms, while keeping the style consistent with the provided example posts.

First, carefully review these example posts to understand the desired style and tone:

<example_posts>
{json.dumps(example_posts)}
</example_posts>

<additional_instructions>
{additional_instructions}
</additional_instructions>


Now, here's the tweet draft you need to improve:

<tweet_draft>
{tweet}
</tweet_draft>

i want the tweet to look and sound like the example posts, adapting the tone, style, etc. give me improvements: language_improvements, alternative_wordings, cadence_improvements, technical_suggestions. 

present it in html tags in the following format:

Refined Tweet:
<refined_tweets>
1) 1st Refined Tweet
2) 2nd Refined Tweet
3) 3rd Refined Tweet
</refined_tweets>

Language Improvements: 
<language_improvements>
1) 1st Potential Improvement Option
2) 2nd Potential Improvement Option
3) 3rd Potential Improvement Option
...
</language_improvements>

<alternative_wordings>
1) 1st Potential Improvement Option
2) 2nd Potential Improvement Option
3) 3rd Potential Improvement Option
...
</alternative_wordings>

<cadence_improvements>
1) 1st Potential Improvement Option
2) 2nd Potential Improvement Option
3) 3rd Potential Improvement Option
...
</cadence_improvements>

<technical_suggestions>
1) 1st Potential Improvement Option
2) 2nd Potential Improvement Option
3) 3rd Potential Improvement Option
...
</technical_suggestions>

<improved_tweet_versions>
1) 1st Improved Tweet Version
2) 2nd Improved Tweet Version
...
</improved_tweet_versions>



<additional_instructions>
Output based on the additional instructions.
</additional_instructions>


always prioritize the additional instructions above all else. just give me content with tags and nothing more. 
"""



def prepare_visualization_prompt(post: str) -> str:
    return f"""
Below is a tweet post idea. Your task is to suggest media that would either support (clarify, illustrate, or reinforce) or expand (add depth, emotion, or additional perspective) on the content of the tweet.

<post>
{post}
</post>
Suggest 3 media types or specific examples that could be created or sourced from existing material (e.g., video clips, infographics, historical images, screenshots, diagrams, memes, etc.). Include short notes on how each one connects to or enhances the tweet.
Propose 2 ideas for AI-generated images that could be used. Include a short description of the idea and a text prompt that can be used to generate the image (using a tool like Midjourney, DALL·E, etc.). Make sure the generated media ties directly into the theme, tone, or message of the tweet.

Organize your response into two sections:

<existing_media>
[1st media type]
[2nd media type]
[3rd media type]
</existing_media>

<ai>
[1st AI-generated image]
[2nd AI-generated image]
</ai>

Only include visuals that are likely to increase engagement or improve comprehension. Avoid generic or unrelated visuals.
"""

def prepare_new_content_inspiration_prompt(input: str, example_posts: Dict[str, Any] = None) -> str:
   
   example_posts_section = ""
   if example_posts:
       example_posts_section = f"""
<example_posts>
{json.dumps(example_posts, indent=2)}
</example_posts>
"""
   
   return(f"""
<unstructured_input>
{input}
</unstructured_input>
{example_posts_section}

based on what i did this week under unstructured_input, i want you to give me topics i can post about. give me 10 standalone topic ideas and 10 thread ideas.


Do not give me tweets. I want topic ideas. Be very specific. We are inspired by this quote: "The bigger the issue, the smaller you write. Remember that. You don't write about the horrors of war. No. You write about a kid's burnt socks lying on the road. You pick the smallest manageable part of the big thing, and you work off the resonance"
          """
   )
