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
You are an AI assistant tasked with improving a tweet draft using the Tree of Thoughts methodology. This approach involves exploring multiple reasoning paths, evaluating different possibilities, and systematically searching for the optimal solution.

STEP 1: ANALYSIS
First, analyze both the example posts and draft tweet. Generate 5 different short analyses focusing on:
1) Style elements (sentence structure, word choice, tone)
2) Technical aspects (terminology, concept complexity)
3) Engagement factors (hooks, calls to action, memorability)

For each analysis, explicitly identify what works well and what could be improved. 

STEP 2: BRAINSTORM IMPROVEMENTS
Based on your analyses, generate 5 distinct improvement strategies:
1) Conservative refinement (maintain most structure, enhance key terms)
2) Moderate restructuring (reorganize for better flow while preserving core message)
3) Creative reimagining (maintain core message but with fresh approach)

For each strategy, evaluate its potential effectiveness given the example posts' style.

STEP 3: GENERATE REFINED VERSIONS
Create 5 refined tweets following each improvement strategy. For each refined tweet:
1) Explain your thought process
2) Evaluate its strengths and weaknesses
3) Assign a confidence score (1-10)



Example posts:
<example_posts>
{example_posts}
</example_posts>

Additional instructions (prioritize these above all else):
<additional_commands>
{additional_commands}
</additional_commands>

Original tweet draft:
<tweet_draft>
{tweet}
</tweet_draft>

Present your final output in this format.  Do not use em dashes or ellipses:
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

def prepare_standalone_tweet_prompt(input: str, example_posts: Dict[str, Any] = None, additional_commands: str = None) -> str:
   
   example_posts_section = ""
   if example_posts:
       example_posts_section = f"""
<example_posts>
{json.dumps(example_posts, indent=2)}
</example_posts>
"""
   
   return(f"""
          
You are a creative AI assistant tasked with generating tweet ideas based on given input. Your goal is to create engaging, specific, and resonant tweet topics that capture small, manageable parts of bigger issues or themes.
          

First, carefully read and analyze the following input from the user. This is the most important part:
          
<user_input>
{input}
</user_input>


{example_posts_section}

Your task is to create:
1. Three standalone topic ideas with example tweets for each idea.
2. Three thread ideas with brief elaborations for each idea.

When generating these ideas:
- Take the instructions and focus on specific content themes i can explore from the example_posts
- Prioritize the user input above all else.
- First two ideas should be largely based on the example_posts, the third idea should be more creative and unique
- Do not use em dashes or ellipses.

Present your response in the following JSON format:



{{
    "standalone_ideas": [
        {{
            "idea": "First standalone idea - be specific",
            "post": "Example tweet for the first standalone idea "
        }},
        {{
            "idea": "Second standalone idea - be specific",
            "post": "Example tweet for the second standalone idea"
        }},
        {{
            "idea": "Third standalone idea - be specific",
            "post": "Example tweet for the third standalone idea"
        }}
    ],
    "thread_ideas": [
        {{
            "idea": "First thread idea - be specific",
            "elaboration": "Elaboration on the first thread idea"
        }},
        {{
            "idea": "Second thread idea - be specific",
            "elaboration": "Elaboration on the second thread idea"
        }},
        {{
            "idea": "Third thread idea - be specific",
            "elaboration": "Elaboration on the third thread idea"
        }}
    ]
}}
          """
   )
