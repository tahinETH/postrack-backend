import json
from typing import Dict, Any, List



def prepare_content_inspiration_prompt(example_posts: Dict[str, Any], tweet: str, additional_commands: str) -> str:
    return f"""
    You are an AI assistant helping a social media content creator generate ideas for new posts. Your task is to suggest topics and points to explore based on their previous content and a provided resource.

    <example_posts>
    {json.dumps(example_posts)}
    </example_posts>

    <tweet_to_reply_to>
    {tweet}
    </tweet_to_reply_to>

    <additional_commands_from_user>
    {additional_commands}
    </additional_commands_from_user>

    The tweet_to_reply_to contains a tweet or thread.
    Generate tweet ideas to respond to, ask a question to, or expand upon the content shared. 
    Provide potential conversation points, topics, orthogonal/parallel ideas and frameworks to explore.

    Return your response in the following JSON format:

    {{
        "dependent_ideas": [
            {{
                "id": 1,
                "idea": "First reply or quote tweet idea (ask a question, expand upon the content, or respond to the tweet_to_reply_to) drawn from example posts - be specific",
                "rationale": "Why this connects to the tweet_to_reply_to"
            }},
            {{
                "id": 2, 
                "idea": "Second reply or quote tweet idea (ask a question, expand upon the content, or respond to the tweet_to_reply_to) drawn from example posts - be specific",
                "rationale": "Why this connects to the tweet_to_reply_to"
            }},
            {{
                "id": 3,
                "idea": "Third reply or quote tweet idea (ask a question, expand upon the content, or respond to the tweet_to_reply_to) drawn from example posts - be specific", 
                "rationale": "Why this connects to the tweet_to_reply_to"
            }}
        ],
        "independent_ideas": [
            {{
                "id": 1,
                "idea": "First creative/esoteric reply or quote tweet idea to tweet_to_reply_to drawn from example posts - be specific",
                "rationale": "Why this connects to the tweet_to_reply_to"
            }},
            {{
                "id": 2,
                "idea": "Second creative/esoteric reply or quote tweet idea to tweet_to_reply_to drawn from example posts - be specific",
                "rationale": "Why this connects to the tweet_to_reply_to"
            }},
            {{
                "id": 3,
                "idea": "Third creative/esoteric reply or quote tweet idea to tweet_to_reply_to drawn from example posts - be specific",
                "rationale": "Why this connects to the tweet_to_reply_to"
            }}
        ],
        "additional_instructions_output": "Output based on any additional instructions provided"
    }}

    For independent ideas, be very creative and include esoteric/outlier ideas. Do not provide actual posts to share - only areas to explore. Do not use em dashes or ellipses.
    """





def prepare_tweet_example_generator_prompt(inspiration: str, example_posts: Dict[str, Any], discussion_source: str, additional_commands: str) -> str:
    return f"""
    You are an AI assistant tasked with generating example tweets based on a discussion source. Your goal is to generate engaging tweets that match the style and tone of the example posts while exploring the provided topic ideas.

    First, carefully review these example posts to understand the desired style and tone:

    <example_posts>
    {json.dumps(example_posts)}
    </example_posts>

    <discussion_source>
    {discussion_source}
    </discussion_source>

    <topic_ideas>
    {inspiration}
    </topic_ideas>


    <additional_commands_from_user>
    {additional_commands}
    </additional_commands_from_user>

    Topic ideas have been generated to explore how to engage with the discussion source with a reply or quote tweet.
    Generate example tweets for each topic idea in the topic_ideas section. Follow the style and tone of the example posts.

    Return your response in the following JSON format:

    {{
        "dependent_ideas": [
            {{
                "1": "First tweet generated based on the first dependent idea",
                "2": "Second tweet generated based on the second dependent idea", 
                "3": "Third tweet generated based on the third dependent idea"
            }},
        "independent_ideas": [
            {{
                "1": "First tweet generated based on the first independent idea",
                "2": "Second tweet generated based on the second independent idea",
                "3": "Third tweet generated based on the third independent idea"
            }}
    }}

    For each tweet:
    - Keep it within Twitter's character limit
    - Match the voice and style of the example posts
    - Focus on one clear topic or idea
    - Use engaging hooks and strong closings
    - Include appropriate formatting (line breaks, emojis, etc.) when relevant

    Do not include generic placeholder tweets. Each tweet should be specific and ready to post. Do not use em dashes or ellipses.
    """







def prepare_tweet_refinement_prompt(tweet: str, style_analysis: Dict[str, Any], additional_commands: str) -> str:
    
    additional_instructions = ""
    if additional_commands:
        additional_instructions = f"""
        Additional instructions for improvement:
        <additional_commands>
        {additional_commands}
        </additional_commands>
            """

    return f"""
You are an AI assistant tasked with improving a tweet draft looking capturing and transferring the soul of the writing.

<account_soul_info>
{style_analysis}
</account_soul_info>


Original tweet draft:
<tweet_draft>
{tweet}
</tweet_draft>

Additional instructions (prioritize these above all else):
<additional_commands>
{additional_commands}
</additional_commands>

Present your final output in this format. For each tweet, you have a character limit of 1000 characters. I want you to transfer the soul of the writing to the tweet:

<refined_tweets>
1) [First refined tweet]
2) [Second refined tweet]
3) [Third refined tweet]
4) [Fourth refined tweet]
5) [Fifth refined tweet]
</refined_tweets>


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

def prepare_standalone_tweet_prompt(input: str, example_posts: Dict[str, Any] = None, additional_commands: str = None, is_thread: bool = False) -> str:
   
   example_posts_section = ""
   if example_posts:
       example_posts_section = f"""
<example_posts>
{json.dumps(example_posts, indent=2)}
</example_posts>
"""
   
   if is_thread:
       task_description = """
Your task is to create 5 thread ideas with brief elaborations for each idea.
"""
       response_format = """
"thread_ideas": [
    {
        "idea": "First thread idea - be specific",
        "elaboration": "Elaboration on the first thread idea"
    },
    {
        "idea": "Second thread idea - be specific",
        "elaboration": "Elaboration on the second thread idea"
    },
    {
        "idea": "Third thread idea - be specific",
        "elaboration": "Elaboration on the third thread idea"
    },
    {
        "idea": "Fourth thread idea - be specific",
        "elaboration": "Elaboration on the fourth thread idea"
    },
    {
        "idea": "Fifth thread idea - be specific",
        "elaboration": "Elaboration on the fifth thread idea"
    }
]
"""
   else:
       task_description = """
Your task is to create 5 standalone topic ideas with example tweets for each idea.
"""
       response_format = """
"standalone_ideas": [
    {
        "idea": "First standalone idea - be specific",
        "post": "Example tweet for the first standalone idea"
    },
    {
        "idea": "Second standalone idea - be specific",
        "post": "Example tweet for the second standalone idea"
    },
    {
        "idea": "Third standalone idea - be specific",
        "post": "Example tweet for the third standalone idea"
    },
    {
        "idea": "Fourth standalone idea - be specific",
        "post": "Example tweet for the fourth standalone idea"
    },
    {
        "idea": "Fifth standalone idea - be specific",
        "post": "Example tweet for the fifth standalone idea"
    }
]
"""
   
   return(f"""
          
You are a creative AI assistant tasked with generating tweet ideas based on given input. 



{example_posts_section}                    

Now, carefully read and analyze the following input from the user. This is the most important part:
          
<user_input>
{input}
</user_input>

{task_description}

When generating these ideas prioritize the user input above all else. 


Present your response in the following JSON format:



{{
    {response_format}
}}
          """
   )

