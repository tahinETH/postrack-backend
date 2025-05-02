import logging
import asyncio
from typing import Dict, Any, List, Tuple
from db.tw.structured import TweetStructuredRepository
from db.tw.account_db import AccountRepository
from api_client import TwitterAPIClient

from analysis.ai import AIAnalyzer
logger = logging.getLogger(__name__)


class AccountAnalyzer:
    def __init__(self, analysis_repo: TweetStructuredRepository, api_key: str):
        self.analysis_repo = analysis_repo
        self.accounts = AccountRepository()
        self.ai = AIAnalyzer(analysis_repo)
        self.api_client = TwitterAPIClient(api_key)

    async def _fetch_account_tweets(self, screen_name: str) -> List[Dict[str, Any]]:
        """Fetch the top tweets for an account"""
        reply_tweets = await self.api_client.api_get_account_by_id_top_tweets(screen_name, limit=50, replies=True)
        non_reply_tweets = await self.api_client.api_get_account_by_id_top_tweets(screen_name, limit=50, replies=False)
        tweets = reply_tweets + non_reply_tweets
        
        return tweets
    
    async def get_account_analysis(self, account_id: str, user_id: str) -> Dict[str, Any]:
        """Get account analysis"""
        existing_analysis = await self.accounts.get_account_analysis(account_id, user_id)
        
        return existing_analysis
        

    async def clean_account_top_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        
        cleaned_tweets = []
        for tweet in tweets:
            
            cleaned_tweet = {
                'tweet_created_at': tweet.get('tweet_created_at'),
                'id': tweet.get('id'),
                'id_str': tweet.get('id_str'), 
                'full_text': tweet.get('full_text', ''),
                'favorite_count': tweet.get('favorite_count', 0),
                'retweet_count': tweet.get('retweet_count', 0),
                'reply_count': tweet.get('reply_count', 0),
                'quote_count': tweet.get('quote_count', 0),
                'views_count': 0 if tweet.get('views_count') is None else tweet.get('views_count'),
                'bookmark_count': tweet.get('bookmark_count', 0),
                'is_quote_status': tweet.get('is_quote_status', False),
                'quoted_status_id_str': tweet.get('quoted_status_id_str'),
                'retweeted_status': tweet.get('retweeted_status'),
                'entities': tweet.get('entities'),
                'source': tweet.get('source')
            }
            cleaned_tweets.append(cleaned_tweet)
        
        return cleaned_tweets

        
    async def run_metrics_analysis(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await asyncio.to_thread(self._run_metrics_analysis, tweets)
    
    def _run_metrics_analysis(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = {}
        
        # Basic engagement metrics
        favorite_counts = [t.get('favorite_count', 0) for t in tweets]
        views_counts = [t.get('views_count', 0) for t in tweets]
        
        metrics['favorite_counts'] = {
            'min': min(favorite_counts) if favorite_counts else 0,
            'max': max(favorite_counts) if favorite_counts else 0,
            'avg': sum(favorite_counts) / len(favorite_counts) if favorite_counts else 0,
            'total': sum(favorite_counts) if favorite_counts else 0
        }
        
        metrics['views_counts'] = {
            'min': min(views_counts) if views_counts else 0,
            'max': max(views_counts) if views_counts else 0,
            'avg': sum(views_counts) / len(views_counts) if views_counts else 0,
            'total': sum(views_counts) if views_counts else 0
        }
        
        # Quote tweet analysis
        quote_tweets = [t for t in tweets if t.get('is_quote_status', False)]
        non_quote_tweets = [t for t in tweets if not t.get('is_quote_status', False)]
        
        metrics['quote_analysis'] = {
            'quote_tweets': {
                'count': len(quote_tweets),
                'percentage': len(quote_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in quote_tweets) / len(quote_tweets) if quote_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in quote_tweets) / len(quote_tweets) if quote_tweets else 0
            },
            'non_quote_tweets': {
                'count': len(non_quote_tweets), 
                'percentage': len(non_quote_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in non_quote_tweets) / len(non_quote_tweets) if non_quote_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in non_quote_tweets) / len(non_quote_tweets) if non_quote_tweets else 0
            }
        }
        
        # Media analysis
        def has_media(tweet):
            entities = tweet.get('entities', {})
            return bool(entities.get('media', []))
            
        media_tweets = [t for t in tweets if has_media(t)]
        non_media_tweets = [t for t in tweets if not has_media(t)]
        
        metrics['media_analysis'] = {
            'with_media': {
                'count': len(media_tweets),
                'percentage': len(media_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in media_tweets) / len(media_tweets) if media_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in media_tweets) / len(media_tweets) if media_tweets else 0
            },
            'without_media': {
                'count': len(non_media_tweets),
                'percentage': len(non_media_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in non_media_tweets) / len(non_media_tweets) if non_media_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in non_media_tweets) / len(non_media_tweets) if non_media_tweets else 0
            }
        }

        # User mentions analysis
        def has_mentions(tweet):
            entities = tweet.get('entities', {})
            return bool(entities.get('user_mentions', []))
            
        mention_tweets = [t for t in tweets if has_mentions(t)]
        non_mention_tweets = [t for t in tweets if not has_mentions(t)]
        
        metrics['mentions_analysis'] = {
            'with_mentions': {
                'count': len(mention_tweets),
                'percentage': len(mention_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in mention_tweets) / len(mention_tweets) if mention_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in mention_tweets) / len(mention_tweets) if mention_tweets else 0
            },
            'without_mentions': {
                'count': len(non_mention_tweets),
                'percentage': len(non_mention_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in non_mention_tweets) / len(non_mention_tweets) if non_mention_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in non_mention_tweets) / len(non_mention_tweets) if non_mention_tweets else 0
            }
        }

        # Symbols analysis
        def has_symbols(tweet):
            entities = tweet.get('entities', {})
            return bool(entities.get('symbols', []))
            
        symbol_tweets = [t for t in tweets if has_symbols(t)]
        non_symbol_tweets = [t for t in tweets if not has_symbols(t)]
        
        metrics['symbols_analysis'] = {
            'with_symbols': {
                'count': len(symbol_tweets),
                'percentage': len(symbol_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in symbol_tweets) / len(symbol_tweets) if symbol_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in symbol_tweets) / len(symbol_tweets) if symbol_tweets else 0
            },
            'without_symbols': {
                'count': len(non_symbol_tweets),
                'percentage': len(non_symbol_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in non_symbol_tweets) / len(non_symbol_tweets) if non_symbol_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in non_symbol_tweets) / len(non_symbol_tweets) if non_symbol_tweets else 0
            }
        }

        # URLs analysis
        def has_urls(tweet):
            entities = tweet.get('entities', {})
            return bool(entities.get('urls', []))
            
        url_tweets = [t for t in tweets if has_urls(t)]
        non_url_tweets = [t for t in tweets if not has_urls(t)]
        
        metrics['urls_analysis'] = {
            'with_urls': {
                'count': len(url_tweets),
                'percentage': len(url_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in url_tweets) / len(url_tweets) if url_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in url_tweets) / len(url_tweets) if url_tweets else 0
            },
            'without_urls': {
                'count': len(non_url_tweets),
                'percentage': len(non_url_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in non_url_tweets) / len(non_url_tweets) if non_url_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in non_url_tweets) / len(non_url_tweets) if non_url_tweets else 0
            }
        }

        # Word length analysis
        def get_word_count(text):
            return len([w for w in text.split() if w.strip()])
            
        word_counts = [(t, get_word_count(t.get('full_text', ''))) for t in tweets]
        
        metrics['word_length'] = {
            'short': {  # 1-25 words
                'count': len([t for t,c in word_counts if c <= 25]),
                'avg_favorites': sum(t.get('favorite_count', 0) for t,c in word_counts if c <= 25) / len([t for t,c in word_counts if c <= 25]) if any(c <= 25 for _,c in word_counts) else 0,
                'avg_views': sum(t.get('views_count', 0) for t,c in word_counts if c <= 25) / len([t for t,c in word_counts if c <= 25]) if any(c <= 25 for _,c in word_counts) else 0
            },
            'medium': {  # 26-50 words
                'count': len([t for t,c in word_counts if 25 < c <= 50]),
                'avg_favorites': sum(t.get('favorite_count', 0) for t,c in word_counts if 25 < c <= 50) / len([t for t,c in word_counts if 25 < c <= 50]) if any(25 < c <= 50 for _,c in word_counts) else 0,
                'avg_views': sum(t.get('views_count', 0) for t,c in word_counts if 25 < c <= 50) / len([t for t,c in word_counts if 25 < c <= 50]) if any(25 < c <= 50 for _,c in word_counts) else 0
            },
            'long': {  # 50+ words
                'count': len([t for t,c in word_counts if c > 50]),
                'avg_favorites': sum(t.get('favorite_count', 0) for t,c in word_counts if c > 50) / len([t for t,c in word_counts if c > 50]) if any(c > 50 for _,c in word_counts) else 0,
                'avg_views': sum(t.get('views_count', 0) for t,c in word_counts if c > 50) / len([t for t,c in word_counts if c > 50]) if any(c > 50 for _,c in word_counts) else 0
            }
        }

        # Source analysis
        iphone_tweets = [t for t in tweets if t.get('source', '').find('Twitter for iPhone') != -1]
        web_tweets = [t for t in tweets if t.get('source', '').find('Twitter Web App') != -1]

        metrics['source_analysis'] = {
            'iphone': {
                'count': len(iphone_tweets),
                'percentage': len(iphone_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in iphone_tweets) / len(iphone_tweets) if iphone_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in iphone_tweets) / len(iphone_tweets) if iphone_tweets else 0
            },
            'web': {
                'count': len(web_tweets),
                'percentage': len(web_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in web_tweets) / len(web_tweets) if web_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in web_tweets) / len(web_tweets) if web_tweets else 0
            },
        }

        # Time of day analysis
        from datetime import datetime
        
        def get_hour_bucket(tweet):
            tweet_created_at = tweet.get('tweet_created_at')
            if not tweet_created_at:
                return 'unknown'  # Or handle missing timestamp however you prefer
            
            created_at = datetime.strptime(tweet_created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            hour = created_at.hour
            if 5 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 17:
                return 'afternoon'
            elif 17 <= hour < 22:
                return 'evening'
            else:
                return 'night'

        morning_tweets = [t for t in tweets if get_hour_bucket(t) == 'morning']
        afternoon_tweets = [t for t in tweets if get_hour_bucket(t) == 'afternoon']
        evening_tweets = [t for t in tweets if get_hour_bucket(t) == 'evening']
        night_tweets = [t for t in tweets if get_hour_bucket(t) == 'night']

        metrics['time_analysis'] = {
            'morning': {  # 5:00-11:59
                'count': len(morning_tweets),
                'percentage': len(morning_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in morning_tweets) / len(morning_tweets) if morning_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in morning_tweets) / len(morning_tweets) if morning_tweets else 0,
                
            },
            'afternoon': {  # 12:00-16:59
                'count': len(afternoon_tweets),
                'percentage': len(afternoon_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in afternoon_tweets) / len(afternoon_tweets) if afternoon_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in afternoon_tweets) / len(afternoon_tweets) if afternoon_tweets else 0,
            },
            'evening': {  # 17:00-21:59
                'count': len(evening_tweets),
                'percentage': len(evening_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in evening_tweets) / len(evening_tweets) if evening_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in evening_tweets) / len(evening_tweets) if evening_tweets else 0,
            },
            'night': {  # 22:00-4:59
                'count': len(night_tweets),
                'percentage': len(night_tweets) / len(tweets) * 100 if tweets else 0,
                'avg_favorites': sum(t.get('favorite_count', 0) for t in night_tweets) / len(night_tweets) if night_tweets else 0,
                'avg_views': sum(t.get('views_count', 0) for t in night_tweets) / len(night_tweets) if night_tweets else 0,
            }
        }

        return metrics
    
    async def run_quantitative_analysis(self, metrics: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        quantitative_analysis = await self.ai.generate_ai_analysis_metrics(metrics, account_data)
        return quantitative_analysis
    
    async def run_qualitative_analysis(self,  metrics: Dict[str, Any], account_data: Dict[str, Any]) -> Dict[str, Any]:
        qualitative_analysis = await self.ai.generate_ai_analysis_qualitative(metrics, account_data)
        return qualitative_analysis
    
    async def run_soul_extractor(self, example_posts: Dict[str, Any]) -> Dict[str, Any]:
        soul_extractor = await self.ai.generate_ai_analysis_soul_extractor(example_posts)
        return soul_extractor


    async def analyze_account(self, account_id: str, new_fetch: bool = False, account_data: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        try:
            # Initial account setup remains synchronous since we need this data
            account = await self.accounts.get_account_by_id(account_id)
            if not account:
                account = {
                    'account_details': account_data,
                    'screen_name': account_data['screen_name'],
                    'account_id': account_data['id_str']
                }
                await self.accounts.upsert_account(account_id, account['screen_name'], account['account_details'], update_existing=True, is_active=False)

            screen_name = account.get('screen_name')
            existing_analysis = await self.accounts.get_account_analysis(account_id, user_id)
            account_data = account['account_details']

            # If we don't need new analysis, return existing data immediately
            if not new_fetch and existing_analysis:
                return {
                    "metrics": existing_analysis.get('metrics'),
                    "quantitative_analysis": existing_analysis.get('quantitative_analysis'),
                    "qualitative_analysis": existing_analysis.get('qualitative_analysis'),
                    "style_analysis": existing_analysis.get('style_analysis')
                }

            # Create background task for the analysis
            async def run_analysis():
                try:
                    # Initialize empty analysis record
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        status="in_progress"
                    )

                    # Fetch and clean tweets
                    tweets = await self._fetch_account_tweets(screen_name)
                    cleaned_tweets = await self.clean_account_top_tweets(tweets)
                    print(cleaned_tweets)
                    
                    # Save cleaned tweets immediately
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        top_tweets=cleaned_tweets,
                        status="processing"
                    )

                    # Run metrics analysis first
                    metrics = await self.run_metrics_analysis(cleaned_tweets)
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        metrics=metrics,
                        status="processing"
                    )

                    # Run quantitative analysis after metrics
                    quantitative_analysis = await self.run_quantitative_analysis(metrics, account_data)
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        quantitative_analysis=quantitative_analysis,
                        status="processing"
                    )

                    # Run qualitative and style analysis in parallel
                    qualitative_analysis, style_analysis = await asyncio.gather(
                        self.run_qualitative_analysis(cleaned_tweets, account_data),
                        self.run_soul_extractor(cleaned_tweets)
                    )

                    # Save final results
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        qualitative_analysis=qualitative_analysis,
                        style_analysis=style_analysis,
                        status="completed"
                    )

                except Exception as e:
                    logger.error(f"Background analysis failed for account {account_id}: {str(e)}")
                    await self.accounts.save_account_analysis(
                        user_id,
                        account_id,
                        status="failed",
                        error=str(e)
                    )

            # Create the background task
            asyncio.create_task(run_analysis(), name=f"analysis_{account_id}")

            # Return immediately with a status indicating analysis is in progress
            return {
                "status": "in_progress",
                "account_id": account_id,
                "message": "Analysis has started and will be updated incrementally"
            }

        except Exception as e:
            logger.error(f"Error analyzing account tweets: {str(e)}")
            raise
