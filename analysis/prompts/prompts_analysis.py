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


def prepare_account_soul_extractor_prompt(example_posts: Dict[str, Any]) -> str:
      return f"""

<example_replies>
{json.dumps(example_posts)}
</example_replies>


<JSON_FORMAT>
{
{
  "profile_summary": "[Write a 1-2 sentence summary capturing the account's main topics, overall tone, and any standout stylistic features.]",
  "persona_and_voice": {
    "core_description": "[Describe the user's apparent persona (e.g., 'industry expert', 'humorist', 'personal journaler') and dominant tones (e.g., 'formal', 'sarcastic', 'enthusiastic').]",
    "indicative_patterns": [
      {
        "pattern": "Common Sentence Openings",
        "description": "[How do tweets typically begin? Note common patterns or phrases.]",
        "example_markers": "[List 1-2 example common opening structures or words.]"
      },
      {
        "pattern": "Expression of Thought/Opinion",
        "description": "[How does the user typically signal opinions or thoughts (e.g., 'I think', direct statements, questions)? Note common markers.]",
        "example_markers": "[List 1-2 example phrases used to express opinion/thought.]"
      },
      {
        "pattern": "Address Style",
        "description": "[Does the user address the audience directly, use informal address, or maintain distance? Provide examples if applicable.]",
        "example_markers": "[List examples like specific address terms or common rhetorical question formats used.]"
      },
      {
        "pattern": "Expression of Certainty/Nuance",
        "description": "[Does the user express high certainty, uncertainty, or acknowledge complexity often? Note typical phrasing.]",
        "example_markers": "[List 1-2 example phrases showing certainty or nuance.]"
      }
    ]
  },
  "cadence_and_flow": {
    "core_description": "[Describe the typical rhythm and flow: e.g., fast-paced, measured, choppy, smooth? Comment on typical sentence length and variation.]",
    "indicative_patterns": [
      {
        "pattern": "Sentence Connectivity",
        "description": "[How are ideas linked within or between sentences (e.g., simple conjunctions, complex clauses, abrupt transitions)?]",
        "example_markers": "[Provide a short example snippet illustrating typical connectivity.]"
      },
      {
        "pattern": "Use of Short Sentences/Fragments",
        "description": "[Are short sentences or fragments used frequently, occasionally, or rarely? For what effect (e.g., emphasis, humor)?]",
        "example_markers": "[List 1-2 examples if used distinctively.]"
      },
      {
        "pattern": "Question Usage",
        "description": "[Note the frequency and typical style of questions (e.g., rhetorical, direct, polling).]",
        "example_markers": "[Provide 1-2 common question formats.]"
      },
      {
        "pattern": "Structural Patterns",
        "description": "[Are there common structural patterns (e.g., lists, comparisons, narratives)? Note if observed.]",
        "example_markers": "[Briefly describe a recurring structure if found.]"
      }
    ]
  },
  "vocabulary_and_texture": {
    "core_description": "[Describe the overall vocabulary: formal, informal, technical, simple, diverse? Any unique textural elements (e.g., specific formatting, emotional language)?]",
    "indicative_patterns": [
      {
        "pattern": "Lexical Mix",
        "description": "[Is there a notable mix of different types of language (e.g., technical & slang, formal & emotional)? Describe the mix.]",
        "example_markers": "[Provide 1-2 examples illustrating the mix if present.]"
      },
      {
        "pattern": "Figurative/Evocative Language",
        "description": "[Does the user employ metaphors, similes, hyperbole, or other evocative language? Note frequency and style.]",
        "example_markers": "[List 1-2 examples if used distinctively.]"
      },
      {
        "pattern": "Signature Words/Phrases",
        "description": "[Are there any recurring words, phrases, or unique coinages that stand out?]",
        "example_markers": "[List 1-2 examples if found.]"
      },
      {
        "pattern": "Capitalization Style",
        "description": "[Describe the typical capitalization: standard sentence case, title case, all lowercase, inconsistent?]",
        "example_markers": "[Provide a brief example illustrating the typical style.]"
      },
      {
        "pattern": "Domain-Specific Jargon",
        "description": "[If applicable, list the key domains and common jargon used.]",
        "example_markers": "[List 3-5 common technical/niche terms if present.]"
      },
      {
        "pattern": "Informal/Slang Usage",
        "description": "[Note frequency and type of informal language, slang, or contractions.]",
        "example_markers": "[List 2-3 common examples if used.]"
      }
    ]
  },
  "punctuation_and_formatting_style": {
    "core_description": "[Describe the general punctuation style: standard, minimal, heavy, creative? Any notable formatting habits (e.g. line breaks)?]",
    "indicative_patterns": [
      {
        "pattern": "Ellipses Usage",
        "description": "[Are ellipses (...) used frequently, occasionally, or rarely? For what effect (e.g., pauses, omission, trailing off)?]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      },
      {
        "pattern": "Emphasis Marks",
        "description": "[Are multiple question/exclamation marks (???, !!!), asterisks (* *), or bolding used for emphasis? Note frequency.]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      },
      {
        "pattern": "Line Breaks Within Tweets",
        "description": "[Are line breaks used for structure or pacing within single tweets? Note frequency and purpose.]",
        "example_markers": "[Confirm yes/no, briefly describe usage if yes.]"
      },
      {
        "pattern": "Parentheses/Dashes",
        "description": "[Are parentheses or em-dashes used for asides, clarifications, or emphasis? Note frequency.]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      }
    ]
  },
  "key_style_takeaways_for_replication": [
    "[List the 3-5 most crucial and distinctive stylistic elements to replicate for this specific account: e.g. usage of lowercase letters, punctuoations, etc.]"
  ]
}
}
</JSON_FORMAT>

Above are the top tweets from an account.B ased on these tweets, I want to create a JSON profile about their posting.
I'll send this JSON to an AI to give it immediate context on how to copy user's writing style.
I wanted you to focus heavily on the style, cadence, and anything that allows you to capture the soul of the writing. 
What i want you to do is to give very concrete examples when describing a value. Tell me in what kind of words, expressions, flows made you think a description.
Use the template shared in JSON_FORMAT. 
"""



def prepare_account_soul_extractor_prompt_community(example_posts: Dict[str, Any]) -> str:
      return f"""

<example_posts>
{json.dumps(example_posts)}
</example_posts>


<JSON_FORMAT>
{
{
  "profile_summary": "[Write a 1-2 sentence summary capturing the community's main topics, overall tone, and any standout stylistic features.]",
  "persona_and_voice": {
    "core_description": "[Describe the community's apparent personas (e.g., 'industry expert', 'humorist', 'personal journaler') and dominant tones (e.g., 'formal', 'sarcastic', 'enthusiastic').]",
    "indicative_patterns": [
      {
        "pattern": "Common Sentence Openings",
        "description": "[How do tweets typically begin? Note common patterns or phrases.]",
        "example_markers": "[List 1-2 example common opening structures or words.]"
      },
      {
        "pattern": "Expression of Thought/Opinion",
        "description": "[How does the community typically signal opinions or thoughts (e.g., 'I think', direct statements, questions)? Note common markers.]",
        "example_markers": "[List 1-2 example phrases used to express opinion/thought.]"
      },
      {
        "pattern": "Address Style",
        "description": "[Does the community address the audience directly, use informal address, or maintain distance? Provide examples if applicable.]",
        "example_markers": "[List examples like specific address terms or common rhetorical question formats used.]"
      },
      {
        "pattern": "Expression of Certainty/Nuance",
        "description": "[Does the community express high certainty, uncertainty, or acknowledge complexity often? Note typical phrasing.]",
        "example_markers": "[List 1-2 example phrases showing certainty or nuance.]"
      }
    ]
  },
  "cadence_and_flow": {
    "core_description": "[Describe the typical rhythm and flow: e.g., fast-paced, measured, choppy, smooth? Comment on typical sentence length and variation.]",
    "indicative_patterns": [
      {
        "pattern": "Sentence Connectivity",
        "description": "[How are ideas linked within or between sentences (e.g., simple conjunctions, complex clauses, abrupt transitions)?]",
        "example_markers": "[Provide a short example snippet illustrating typical connectivity.]"
      },
      {
        "pattern": "Use of Short Sentences/Fragments",
        "description": "[Are short sentences or fragments used frequently, occasionally, or rarely? For what effect (e.g., emphasis, humor)?]",
        "example_markers": "[List 1-2 examples if used distinctively.]"
      },
      {
        "pattern": "Question Usage",
        "description": "[Note the frequency and typical style of questions (e.g., rhetorical, direct, polling).]",
        "example_markers": "[Provide 1-2 common question formats.]"
      },
      {
        "pattern": "Structural Patterns",
        "description": "[Are there common structural patterns (e.g., lists, comparisons, narratives)? Note if observed.]",
        "example_markers": "[Briefly describe a recurring structure if found.]"
      }
    ]
  },
  "vocabulary_and_texture": {
    "core_description": "[Describe the overall vocabulary: formal, informal, technical, simple, diverse? Any unique textural elements (e.g., specific formatting, emotional language)?]",
    "indicative_patterns": [
      {
        "pattern": "Lexical Mix",
        "description": "[Is there a notable mix of different types of language (e.g., technical & slang, formal & emotional)? Describe the mix.]",
        "example_markers": "[Provide 1-2 examples illustrating the mix if present.]"
      },
      {
        "pattern": "Figurative/Evocative Language",
        "description": "[Do the community employ metaphors, similes, hyperbole, or other evocative language? Note frequency and style.]",
        "example_markers": "[List 1-2 examples if used distinctively.]"
      },
      {
        "pattern": "Signature Words/Phrases",
        "description": "[Are there any recurring words, phrases, or unique coinages that stand out?]",
        "example_markers": "[List 1-2 examples if found.]"
      },
      {
        "pattern": "Capitalization Style",
        "description": "[Describe the typical capitalization: standard sentence case, title case, all lowercase, inconsistent?]",
        "example_markers": "[Provide a brief example illustrating the typical style.]"
      },
      {
        "pattern": "Domain-Specific Jargon",
        "description": "[If applicable, list the key domains and common jargon used.]",
        "example_markers": "[List 3-5 common technical/niche terms if present.]"
      },
      {
        "pattern": "Informal/Slang Usage",
        "description": "[Note frequency and type of informal language, slang, or contractions.]",
        "example_markers": "[List 2-3 common examples if used.]"
      }
    ]
  },
  "punctuation_and_formatting_style": {
    "core_description": "[Describe the general punctuation style: standard, minimal, heavy, creative? Any notable formatting habits (e.g. line breaks)?]",
    "indicative_patterns": [
      {
        "pattern": "Ellipses Usage",
        "description": "[Are ellipses (...) used frequently, occasionally, or rarely? For what effect (e.g., pauses, omission, trailing off)?]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      },
      {
        "pattern": "Emphasis Marks",
        "description": "[Are multiple question/exclamation marks (???, !!!), asterisks (* *), or bolding used for emphasis? Note frequency.]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      },
      {
        "pattern": "Line Breaks Within Tweets",
        "description": "[Are line breaks used for structure or pacing within single tweets? Note frequency and purpose.]",
        "example_markers": "[Confirm yes/no, briefly describe usage if yes.]"
      },
      {
        "pattern": "Parentheses/Dashes",
        "description": "[Are parentheses or em-dashes used for asides, clarifications, or emphasis? Note frequency.]",
        "example_markers": "[Provide 1 example if used distinctively.]"
      }
    ]
  },
  "key_style_takeaways_for_replication": [
    "[List the 3-5 most crucial and distinctive stylistic elements to replicate for this specific account: e.g. usage of lowercase letters, punctuoations, etc.]"
  ]
}
}
</JSON_FORMAT>

Above are the top tweets from a community. Based on these tweets, I want to create a JSON profile about their posting.
I'll send this JSON to an AI to give it immediate context on how to copy community's writing style and make a post fitting for the community.
I wanted you to focus heavily on the style, cadence, and anything that allows you to capture the soul of the writing. 
What i want you to do is to give very concrete examples when describing a value. Tell me in what kind of words, expressions, flows made you think a description.
Use the template shared in JSON_FORMAT. 
"""


def prepare_account_reply_extractor_prompt(example_replies: Dict[str, Any]) -> str:
    return f"""
<example_replies>
{json.dumps(example_replies)}
</example_replies>

<JSON_FORMAT>
{{
  "reply_profile_summary": "[1‑2 sentences on typical reply themes, overall stance, and tone.]",

  "source_tweet_alignment": {{
    "default_stance": "[agree / neutral / challenge / playful / other]",
    "stance_frequency_breakdown": {{
      "agree": "[%]", "neutral": "[%]", "challenge": "[%]", "playful": "[%]", "other": "[%]"
    }}
  }},

  "audience_address_style": {{
    "core_description": "[How they address the author/audience.]",
    "indicative_patterns": [
      {{
        "pattern": "Handle vs Name Usage",
        "description": "[Do they use @handle, first name, both?]",
        "example_markers": "[\"@alice\", \"Alice —\"]"
      }},
      {{
        "pattern": "Second‑Person Framing",
        "description": "[Direct 'you', rhetorical questions, etc.]",
        "example_markers": "[\"you missed …?\", \"ever tried …?\"]"
      }}
    ]
  }},

  "reference_and_context_handling": {{
    "direct_quote_usage": "[never / occasional / frequent]",
    "mention_usage": "[opening / closing / inline / none]",
    "context_depth": "[single‑line / multi‑sentence / mini‑thread]"
  }},

  "cadence_and_flow": {{
    "core_description": "[Pace, sentence length, flow in replies.]",
    "length_vs_source_ratio": "[<0.5× / ≈1× / >2×]",
    "indicative_patterns": [
      {{
        "pattern": "Sentence Connectivity",
        "description": "[Conjunctions, abrupt breaks, etc.]",
        "example_markers": "[short illustrative snippet]"
      }},
      {{
        "pattern": "Question Usage",
        "description": "[Rhetorical vs genuine questions to OP.]",
        "example_markers": "[\"What if …?\", \"Thoughts?\"]"
      }}
    ]
  }},

  "vocabulary_and_texture": {{
    "core_description": "[Formal/informal, emojis, jargon in replies.]",
    "indicative_patterns": [
      {{
        "pattern": "Emojis / GIF shorthand",
        "description": "[Frequency, placement.]",
        "example_markers": "[\"😂\", \"🔥\"]"
      }},
      {{
        "pattern": "Signature Reply Phrases",
        "description": "[Recurring reply‑specific phrases.]",
        "example_markers": "[\"fair point\", \"+1\"]"
      }}
    ]
  }},

  "punctuation_and_formatting_style": {{
    "core_description": "[Ellipses, exclamations, line breaks inside replies.]",
    "indicative_patterns": [
      {{
        "pattern": "Ellipses Usage",
        "description": "[rate & purpose]",
        "example_markers": "[\"so…\", \"well…\"]"
      }},
      {{
        "pattern": "Line Breaks",
        "description": "[yes/no; how used for pacing.]",
        "example_markers": "[confirm usage]"
      }}
    ]
  }},

  "engagement_goal_cues": {{
    "calls_to_action": "[ask for RTs? invite opinions? rarely?]",
    "humour_hooks": "[gif? sarcasm? none?]"
  }},

  "key_reply_style_takeaways_for_replication": [
    "[3‑5 bullet points: most critical style rules for replies]"
  ]
}}
</JSON_FORMAT>

Above are real replies from an account. Analyse **only the replies** and fill every JSON field with <10 concise lines each, always citing concrete phrases where asked.
"""
