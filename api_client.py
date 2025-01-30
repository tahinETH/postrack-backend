import requests
import aiohttp
from typing import Optional, Dict, Any
import json
from datetime import datetime

class TwitterAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        
    async def get_user_details_by_screen_name(self, screen_name: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/user/{screen_name}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    return await response.json()
        except Exception as e:
            print(f"Error getting user details: {str(e)}")
            return None

    async def get_tweet_details(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    return await response.json()
        except Exception as e:
            print(f"Error getting tweet details: {str(e)}")
            return None
            
    async def get_tweet_comments(self, tweet_id: str, to_user: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            all_comments = []
            next_cursor = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    if to_user:
                        url = f'https://api.socialdata.tools/twitter/search?query=conversation_id:{tweet_id} to:{to_user}'
                    else:
                        url = f'https://api.socialdata.tools/twitter/search?query=conversation_id:{tweet_id}'
                        
                    params = {'cursor': next_cursor} if next_cursor else {}
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                    
                    if 'tweets' in data:
                        all_comments.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return {'data': all_comments}
        except Exception as e:
            print(f"Error getting comments: {str(e)}")
            return None
            
    async def get_tweet_retweeters(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_retweeters = []
            next_cursor = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}/retweeted_by'
                    params = {'cursor': next_cursor} if next_cursor else {}
                    
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                    
                    if 'users' in data:
                        all_retweeters.extend(data['users'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return {'data': all_retweeters}
        except Exception as e:
            print(f"Error getting retweeters: {str(e)}")
            return None

    async def get_user_tweets(self, username: str, since_timestamp: Optional[int] = None) -> Optional[list]:
        try:
            all_tweets = []
            next_cursor = None
            
            query = f'from:{username}'
            if since_timestamp:
                query += f' since_time:{since_timestamp}'
                
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/search'
                    params = {'query': query}
                    if next_cursor:
                        params['cursor'] = next_cursor
                        
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return all_tweets
        except Exception as e:
            print(f"Error getting user tweets: {str(e)}")
            return None
        

    async def get_top_tweets(self, username: str) -> Optional[list]:
        try:
            all_tweets = []
            next_cursor = None
            
            query = f'from:{username}'
          
           
                
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/search'
                    params = {'query': query,
                              'type': 'top'}
                    if next_cursor:
                        params['cursor'] = next_cursor
                        
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return all_tweets
        except Exception as e:
            print(f"Error getting user tweets: {str(e)}")
            return None    