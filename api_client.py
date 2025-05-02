import requests
import aiohttp
from typing import Optional, Dict, Any
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TwitterAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        
    async def api_get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/user/{account_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    data = await response.json()
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting user details")
                        return None
                    return data
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return None
    
    async def api_get_account_by_screen_name(self, screen_name: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/user/{screen_name}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    data = await response.json()
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting user details")
                        return None
                    return data
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return None
    async def api_get_list_tweets(self, list_id: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        try:
            all_tweets = []
            next_cursor = None
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/list/{list_id}/tweets'
                    params = {}
                    if next_cursor:
                        params['cursor'] = next_cursor
                        
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting list tweets")
                        return None
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                        
                        # Break if we've reached the desired limit
                        if len(all_tweets) >= limit:
                            all_tweets = all_tweets[:limit]
                            break
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                   
            return all_tweets
        except Exception as e:
            logger.error(f"Error getting list tweets: {str(e)}")
            return None
        


    async def api_get_account_by_id_top_tweets(self, screen_name: str, limit: int = 50, replies: bool = False) -> Optional[Dict[str, Any]]:
        try:
            all_tweets = []
            next_cursor = None
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/search'
                    params = {
                        'query': f'from:{screen_name} {"-filter:replies" if not replies else "filter:replies"}',
                        'type': 'Top'
                    }
                    if next_cursor:
                        params['cursor'] = next_cursor
                        
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting user's top tweets")
                        return None
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                        
                        # Break if we've reached the desired limit
                        if len(all_tweets) >= limit:
                            all_tweets = all_tweets[:limit]
                            break
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
            
            return all_tweets
        except Exception as e:
            logger.error(f"Error getting user's top tweets: {str(e)}")
            return None

    async def api_get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    data = await response.json()
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting tweet details")
                        return None
                    
                    return data
        except Exception as e:
            logger.error(f"Error getting tweet details: {str(e)}")
            return None
        
    async def api_get_thread_tweets(self, thread_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_tweets = []
            next_cursor = None
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/thread/{thread_id}'
                    params = {'cursor': next_cursor} if next_cursor else {}
                    
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting thread tweets")
                        return None
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
            
            
            return all_tweets
        except Exception as e:
            logger.error(f"Error getting thread tweets: {str(e)}")
            return None
     
    async def api_get_tweet_comments(self, tweet_id: str, to_user: Optional[str] = None, since_timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            all_comments = []
            next_cursor = None
            async with aiohttp.ClientSession() as session:
                while True:
                    if to_user:
                        url = f'https://api.socialdata.tools/twitter/search?query=conversation_id:{tweet_id} to:{to_user} {"since_time:",since_timestamp if since_timestamp else ""}'
                    else:
                        url = f'https://api.socialdata.tools/twitter/search?query=conversation_id:{tweet_id} {"since_time:",since_timestamp if since_timestamp else ""}'
                        
                    params = {'cursor': next_cursor} if next_cursor else {}
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting tweet comments")
                        return None
                    
                    if 'tweets' in data:
                        all_comments.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                   
            return {'data': all_comments}
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return None
            
    async def api_get_tweet_retweeters(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_retweeters = []
            next_cursor = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}/retweeted_by'
                    params = {'cursor': next_cursor} if next_cursor else {}
                    
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting tweet retweeters")
                        return None
                    
                    if 'users' in data:
                        all_retweeters.extend(data['users'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return {'data': all_retweeters}
        except Exception as e:
            logger.error(f"Error getting retweeters: {str(e)}")
            return None
        
    async def api_get_tweet_quotes(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_quotes = []
            next_cursor = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}/quotes'
                    params = {'cursor': next_cursor} if next_cursor else {}
                    
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting tweet quotes")
                        return None
                    
                    if 'tweets' in data:
                        all_quotes.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
                    
            return {'data': all_quotes}
        except Exception as e:
            logger.error(f"Error getting quote tweets: {str(e)}")
            return None
    async def api_get_latest_user_tweets(self, username: str, since_timestamp: Optional[int] = None) -> Optional[list]:
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
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting user tweets")
                        return None
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
            
            return all_tweets
        except Exception as e:
            logger.error(f"Error getting user tweets: {str(e)}")
            return None


    async def api_get_community_top_tweets(self, community_id: str, limit: int = 100) -> Optional[list[Dict[str, Any]]]:
        """Get top tweets from a Twitter community"""
        try:
            all_tweets = []
            next_cursor = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f'https://api.socialdata.tools/twitter/community/{community_id}/tweets'
                    params = {
                        'type': 'Top'
                    }
                    if next_cursor:
                        params['cursor'] = next_cursor
                        
                    async with session.get(url, headers=self.get_headers(), params=params) as response:
                        data = await response.json()
                        
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting community top tweets")
                        return None
                    
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                        
                        # Break if we've reached the desired limit
                        if len(all_tweets) >= limit:
                            all_tweets = all_tweets[:limit]
                            break
                    
                    next_cursor = data.get('next_cursor')
                    if not next_cursor:
                        break
            
            return all_tweets
        except Exception as e:
            logger.error(f"Error getting community top tweets: {str(e)}")
            return None

    async def api_get_community(self, community_id: str) -> Optional[Dict[str, Any]]:
        """Get community details"""
        try:
            url = f'https://api.socialdata.tools/twitter/community/{community_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    data = await response.json()
                    if data.get('status') == 'error' and data.get('message') == 'Insufficient balance':
                        logger.error("Insufficient balance when getting community details")
                        return None
                    return data
        except Exception as e:
            logger.error(f"Error getting community details: {str(e)}")
            return None