import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from db.migrations import get_async_session
from db.tw.tweet_db import TweetDataRepository
from db.users.user_db import UserDataRepository
from db.tw.account_db import AccountRepository


class TweetStructuredRepository():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tweet_data = TweetDataRepository()
        self.user_data = UserDataRepository()
        self.accounts = AccountRepository()
        

    async def process_engagement_metrics(self, tweet_details: Dict) -> Dict[str, int]:
        """Extract engagement metrics from tweet details"""
        return {
            'quote_count': tweet_details.get('quote_count', 0),
            'reply_count': tweet_details.get('reply_count', 0),
            'retweet_count': tweet_details.get('retweet_count', 0),
            'favorite_count': tweet_details.get('favorite_count', 0),
            'views_count': tweet_details.get('views_count', 0),
            'bookmark_count': tweet_details.get('bookmark_count', 0)
        }
    
    async def get_streak_data(self, feed_data: List[Dict]) -> Dict[str, Any]:
        """Get streak data for a user's tweets"""
        # Get all monitored tweets for the user
        
        if not feed_data:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "total_posts": 0,
                "average_posts_per_day": 0,
                "contribution_map": {}
            }

        # Create contribution map
        contribution_map = {}
        for item in feed_data:
            if 'created_at' in item:
                # Parse ISO format date string (2025-03-18T12:28:44.000000Z)
                created_date = datetime.strptime(item['created_at'].split('T')[0], '%Y-%m-%d')
                tweet_date = created_date.strftime('%Y-%m-%d')
                contribution_map[tweet_date] = contribution_map.get(tweet_date, 0) + 1

        # Calculate current streak
        current_streak = 0
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(365):
            date_str = today.strftime('%Y-%m-%d')
            if date_str in contribution_map:
                current_streak += 1
                today = today - timedelta(days=1)
            else:
                break
        # Calculate longest streak
        longest_streak = 0
        current_longest = 0
        dates = sorted(contribution_map.keys())

        for i in range(len(dates)):
            current_date = datetime.strptime(dates[i], '%Y-%m-%d')
            prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d') if i > 0 else None

            if prev_date and (current_date - prev_date).days == 1:
                current_longest += 1
            else:
                current_longest = 1

            longest_streak = max(longest_streak, current_longest)

        # Calculate average posts per day (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        posts_last_30_days = sum(
            count for date, count in contribution_map.items()
            if datetime.strptime(date, '%Y-%m-%d') >= thirty_days_ago
        )
        average_posts = round(posts_last_30_days / 30, 1)

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_posts": len(feed_data),
            "average_posts_per_day": average_posts,
            "contribution_map": contribution_map
        }

    async def get_user_feed(self, user_id: str, skip: int = 0, limit: int = 20, type: str = "time", sort: str = "desc") -> Dict[str, Any]:
        """Get latest data for all monitored tweets for a user with pagination"""
        logger = logging.getLogger(__name__)

        # Get all monitored tweets for the user
        monitored_tweets = await self.tweet_data.get_tweets_for_user(user_id)
        total_count = len(monitored_tweets) if monitored_tweets else 0
        
        tracked_items = await self.user_data.get_tracked_items(user_id)
        tracked_accounts = []

        if tracked_items.get('analysis'):
            for account_id in tracked_items['analysis']:
                account = await self.accounts.get_account_by_id(account_id)
                if account:
                    tracked_accounts.append({
                        'account_id': account['account_id'],
                        'screen_name': account['screen_name'],
                        'is_active': account['is_active'],
                        'last_check': account['last_check'],
                        'created_at': account['created_at'],
                        'account_details': account['account_details'],
                        'tracking_type': 'analysis'
                    })

        
        if tracked_items.get('accounts'):
            for account_id in tracked_items['accounts']:
                account = await self.accounts.get_account_by_id(account_id)
                if account:
                    tracked_accounts.append({
                        'account_id': account['account_id'],
                        'screen_name': account['screen_name'],
                        'is_active': account['is_active'],
                        'last_check': account['last_check'],
                        'created_at': account['created_at'],
                        'account_details': account['account_details'],
                        'tracking_type': 'account'
                    })

        feed_data = []

        if monitored_tweets:
            for tweet in monitored_tweets:
                # Get latest tweet details
                latest_details = await self.tweet_data.get_latest_tweet_details(tweet['tweet_id'])
                if not latest_details:
                    logger.warning(f"No details found for tweet_id: {tweet['tweet_id']}")
                    continue

                tweet_data = latest_details
                captured_at = int(datetime.now().timestamp())
                engagement = await self.process_engagement_metrics(tweet_data)

                feed_item = {
                    'tweet_id': tweet['tweet_id'],
                    'is_monitored': bool(tweet['is_active']),
                    'tracking_type': tweet['tracking_type'],
                    'tracked_id': tweet['tracked_id'],
                    'author': {
                        'id': tweet_data.get('author_id') or tweet_data.get('user', {}).get('id'),
                        'screen_name': tweet_data.get('user', {}).get('screen_name') or tweet_data.get('author_username'),
                        'followers_count': tweet_data.get('user', {}).get('followers_count', 0),
                        'profile_image_url_https': tweet_data.get('user', {}).get('profile_image_url_https', '').replace('_normal', '')
                    },
                    'engagement_metrics': engagement,
                    'total_comments': tweet_data.get('reply_count', 0),
                    'total_retweeters': tweet_data.get('retweet_count', 0),
                    'total_quotes': tweet_data.get('quote_count', 0),
                    'last_updated': captured_at,
                    'created_at': tweet_data.get('tweet_created_at')
                }

                text = tweet_data.get('full_text') or tweet_data.get('text')
                if text:
                    feed_item['text'] = text

                feed_data.append(feed_item)

        # Separate individual tweets and account tweets
        individual_tweets = [tweet for tweet in feed_data if tweet['tracking_type'] == 'individual']
        account_tweets = [tweet for tweet in feed_data if tweet['tracking_type'] == 'account']
        
        # Define reverse_sort before using it
        reverse_sort = sort.lower() == "desc"
        
        # Sort based on type and sort parameters
        if type == "time":
            sort_key = 'created_at'
            # Sort account tweets
            account_tweets = sorted(account_tweets, key=lambda x: x[sort_key], reverse=reverse_sort)
        else:  # type == "view"
            # Sort account tweets by views count
            account_tweets = sorted(account_tweets, key=lambda x: x['engagement_metrics']['views_count'], reverse=reverse_sort)
        
        # Combine with individual tweets always at the start
        sorted_feed = individual_tweets + account_tweets
        
        # Apply pagination AFTER sorting
        paginated_feed = sorted_feed[skip:skip + limit] if sorted_feed else []

        # Get streak data using feed_data (all feed items, not just paginated ones)
        streak_data = await self.get_streak_data(feed_data)

        return {
            'total_count': total_count,
            'tweets': paginated_feed,
            'tracked_accounts': tracked_accounts,
            'streak_data': streak_data
        }


    async def get_raw_tweet_history(self, tweet_id: str) -> Dict[str, Any]:
        """Get raw, unprocessed history data for a tweet"""
        # Get latest tweet details
        details = await self.tweet_data.get_all_tweet_details(tweet_id)
        
        # Get comments
        comments = await self.tweet_data.get_tweet_comments(tweet_id)
        
        # Get retweeters 
        retweeters = await self.tweet_data.get_tweet_retweeters(tweet_id)

        # Get Quotes
        quotes = await self.tweet_data.get_tweet_quotes(tweet_id)

        return {
            'tweet_id': tweet_id,
            'details': [
                {'data': json.loads(d[0]), 'captured_at': d[1]} 
                for d in details
            ],
            'comments': [
                {'data': json.loads(comment.data_json), 'captured_at': comment.captured_at} 
                for comment in comments
            ],
            'retweeters': [
                {'data': json.loads(retweeter.data_json), 'captured_at': retweeter.captured_at} 
                for retweeter in retweeters
            ],
            'quotes': [
                {'data': json.loads(quote.data_json), 'captured_at': quote.captured_at} 
                for quote in quotes
            ]
        }

    async def get_analyzed_tweet_history(self, tweet_id: str) -> Dict[str, Any]:
        """Get processed and analyzed history data for a tweet"""
        # Get latest tweet details
        details = await self.tweet_data.get_all_tweet_details(tweet_id)

        if not details:
            return {}
            
        engagement_metrics = {}
        full_text = None
        user_info = None
        user_followers = {}
        
        for detail_json, captured_at in details:
            detail = json.loads(detail_json)
            engagement_metrics[captured_at] = await self.process_engagement_metrics(detail)
            
            if detail.get('full_text'):
                full_text = detail['full_text']
            if detail.get('user'):
                user_info = {
                    'id': detail['user'].get('id'),
                    'screen_name': detail['user'].get('screen_name'),
                    'profile_image_url_https': detail['user'].get('profile_image_url_https', '').replace('_normal', '')
                }
                user_followers[captured_at] = detail['user'].get('followers_count', 0)
            
        engagement_changes = {}
        timestamps = sorted(engagement_metrics.keys())
        for i in range(1, len(timestamps)):
            prev_ts = timestamps[i-1]
            curr_ts = timestamps[i]
            
            engagement_changes[curr_ts] = {
                metric: (engagement_metrics[curr_ts][metric] or 0) - (engagement_metrics[prev_ts][metric] or 0)
                for metric in engagement_metrics[curr_ts].keys()
            }
            
        comments_tracking = {}
        verified_replies = {}

        # Get comments
        comments = await self.tweet_data.get_tweet_comments(tweet_id)
        
        existing_comment_ids = set()
        for comment_json, captured_at in comments:
            comment = json.loads(comment_json)
            if comment['id'] not in existing_comment_ids:
                if captured_at not in comments_tracking:
                    comments_tracking[captured_at] = []
                    verified_replies[captured_at] = 0
                
                is_verified = comment.get('user', {}).get('verified', False)
                if is_verified:
                    verified_replies[captured_at] += 1
                    
                comments_tracking[captured_at].append({
                    'id': comment['id'],
                    'favorite_count': comment.get('favorite_count', 0),
                    'views_count': comment.get('views_count', 0),
                    'bookmark_count': comment.get('bookmark_count', 0),
                    'screen_name': comment.get('user', {}).get('screen_name'),
                    'followers_count': comment.get('user', {}).get('followers_count', 0),
                    'verified': is_verified,
                    'profile_image_url_https': comment.get('user', {}).get('profile_image_url_https', '').replace('_normal', '')
                })
                existing_comment_ids.add(comment['id'])
        
        retweeters_tracking = {}
        verified_retweets = {}
        
        # Get retweeters
        retweeters = await self.tweet_data.get_tweet_retweeters(tweet_id)
        
        existing_retweeter_names = set()
        for retweeter in retweeters:
            # Check if retweeter is already a dictionary, if not convert it to JSON
            if isinstance(retweeter, dict):
                retweeter_data = retweeter
                captured_at = int(datetime.now().timestamp())  # Use current timestamp as fallback
            else:
                # Assuming retweeter has data and timestamp attributes
                retweeter_data = json.loads(retweeter.data) if hasattr(retweeter, 'data') else {}
                captured_at = retweeter.captured_at if hasattr(retweeter, 'captured_at') else int(datetime.now().timestamp())

            if retweeter_data.get('screen_name') and retweeter_data['screen_name'] not in existing_retweeter_names:
                if captured_at not in retweeters_tracking:
                    retweeters_tracking[captured_at] = []
                    verified_retweets[captured_at] = 0
                    
                is_verified = retweeter_data.get('verified', False)
                if is_verified:
                    verified_retweets[captured_at] += 1
                    
                retweeters_tracking[captured_at].append({
                    'screen_name': retweeter_data['screen_name'],
                    'followers_count': retweeter_data.get('followers_count', 0),
                    'verified': is_verified,
                    'profile_image_url_https': retweeter_data.get('profile_image_url_https', '').replace('_normal', '')
                })
                existing_retweeter_names.add(retweeter_data['screen_name'])

        quotes_tracking = {}
        verified_quotes = {}
        
        # Get quotes
        quotes = await self.tweet_data.get_tweet_quotes(tweet_id)
        
        existing_quote_ids = set()
        for quote_obj in quotes:
            quote = json.loads(quote_obj.data_json)  # Assuming TweetQuote has a quote_json field
            if quote['id'] not in existing_quote_ids:
                captured_at = quote_obj.captured_at  # Assuming TweetQuote has a captured_at field
                
                if captured_at not in quotes_tracking:
                    quotes_tracking[captured_at] = []
                    verified_quotes[captured_at] = 0
                    
                is_verified = quote.get('user', {}).get('verified', False)
                if is_verified:
                    verified_quotes[captured_at] += 1
                    
                quotes_tracking[captured_at].append({
                    'id': quote['id'],
                    'favorite_count': quote.get('favorite_count', 0),
                    'views_count': quote.get('views_count', 0),
                    'bookmark_count': quote.get('bookmark_count', 0),
                    'screen_name': quote.get('user', {}).get('screen_name'),
                    'followers_count': quote.get('user', {}).get('followers_count', 0),
                    'verified': is_verified,
                    'profile_image_url_https': quote.get('user', {}).get('profile_image_url_https', '').replace('_normal', '')
                })
                existing_quote_ids.add(quote['id'])
        
        for ts in engagement_metrics:
            engagement_metrics[ts].update({
                'verified_replies': verified_replies.get(ts, 0),
                'verified_retweets': verified_retweets.get(ts, 0),
                'verified_quotes': verified_quotes.get(ts, 0)
            })

        ai_analysis_row = await self.tweet_data.get_ai_analysis(tweet_id)
        
        ai_analysis = None
        
        if ai_analysis_row:
            input_data = json.loads(ai_analysis_row[1])
            
            # Add profile pictures to top amplifiers
            if 'top_amplifiers' in input_data:
                # Add profile pics for commenters
                if 'commenters' in input_data['top_amplifiers']:
                    for commenter in input_data['top_amplifiers']['commenters']:
                        # Look up commenter in comments_tracking to get profile pic
                        for ts, comments in comments_tracking.items():
                            for comment in comments:
                                if comment['screen_name'] == commenter['screen_name']:
                                    commenter['profile_image_url_https'] = comment['profile_image_url_https']
                                    break
                            if 'profile_image_url' in commenter:
                                break
                
                # Add profile pics for retweeters  
                if 'retweeters' in input_data['top_amplifiers']:
                    for retweeter in input_data['top_amplifiers']['retweeters']:
                        # Look up retweeter in retweeters_tracking to get profile pic
                        for ts, retweeters in retweeters_tracking.items():
                            for rt in retweeters:
                                if rt['screen_name'] == retweeter['screen_name']:
                                    retweeter['profile_image_url_https'] = rt['profile_image_url_https']
                                    break
                            if 'profile_image_url' in retweeter:
                                break

                # Add profile pics for quoters
                if 'quoters' in input_data['top_amplifiers']:
                    for quoter in input_data['top_amplifiers']['quoters']:
                        # Look up quoter in quotes_tracking to get profile pic
                        for ts, quotes in quotes_tracking.items():
                            for quote in quotes:
                                if quote['screen_name'] == quoter['screen_name']:
                                    quoter['profile_image_url_https'] = quote['profile_image_url_https']
                                    break
                            if 'profile_image_url' in quoter:
                                break
            
            ai_analysis = {
                'analysis': ai_analysis_row[0],
                'input_data': input_data
            }
        
        return {
            'tweet_id': tweet_id,
            'full_text': full_text,
            'user': user_info,
            'timestamps': timestamps,
            'engagement_metrics': engagement_metrics,
            'engagement_changes': engagement_changes,
            'comments_tracking': comments_tracking,
            'retweeters_tracking': retweeters_tracking,
            'quotes_tracking': quotes_tracking,
            'user_followers': user_followers,
            'ai_analysis': ai_analysis
        }

    async def prepare_insight_data(self, tweet_id: str) -> Dict[str, Any]:
        """Analyze tweet history data and prepare insights"""
        analyzed_history = await self.get_analyzed_tweet_history(tweet_id)
        if not analyzed_history:
            return {}

        # Handle empty data cases
        if not analyzed_history['retweeters_tracking'] and not analyzed_history['comments_tracking']:
            return {
                'top_amplifiers': {
                    'quoters': [],
                    'retweeters': [],
                    'commenters': []
                },
                'engagement_analysis': {
                    'peak_engagement_time': None,
                    'silent_engagement': {
                        'average_silent_ratio': 0,
                        'peak_silent_ratio': 0
                    },
                    'comment_retweet_ratio': {
                        'average': 0,
                        'trend': []
                    }
                },
                'verified_impact': {
                    'average_change_after_verified': 0,
                    'total_verified_engagements': 0
                },
                'quote_analysis': {
                    'average_quote_ratio': 0,
                    'total_quotes': 0,
                    'quote_trend': []
                },
                'comment_analysis': {
                    'average_comment_ratio': 0,
                    'total_comments': 0,
                    'comment_trend': []
                },
                'growth_metrics': {
                    'total_growth': 0,
                    'peak_growth': None,
                    'growth_during_peak_engagement': None
                }
            }

        # Top Amplifiers Analysis
        all_retweeters = []
        for retweeters in analyzed_history['retweeters_tracking'].values():
            all_retweeters.extend(retweeters)
            
        # Remove duplicates and get top retweeters by followers
        seen_retweeters = {}
        for retweeter in all_retweeters:
            if retweeter['screen_name'] not in seen_retweeters:
                seen_retweeters[retweeter['screen_name']] = {
                    'screen_name': retweeter['screen_name'],
                    'followers_count': retweeter['followers_count'],
                    'verified': retweeter['verified']
                }
        top_retweeters = sorted(seen_retweeters.values(), 
                            key=lambda x: x['followers_count'], 
                            reverse=True)[:10]

        # Get all commenters with timestamps
        all_commenters = []
        for timestamp, comments in analyzed_history['comments_tracking'].items():
            for comment in comments:
                filtered_comment = {
                    'screen_name': comment['screen_name'],
                    'followers_count': comment['followers_count'],
                    'verified': comment['verified'],
                    'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat()
                }
                all_commenters.append(filtered_comment)
                
        # Remove duplicates and get top commenters by followers
        
        seen_commenters = {}
        for commenter in sorted(all_commenters, key=lambda x: x['followers_count'], reverse=True):
            if commenter['screen_name'] not in seen_commenters:
                seen_commenters[commenter['screen_name']] = commenter
        top_commenters = list(seen_commenters.values())[:10]
        
        # Get all quoters with timestamps
        all_quoters = []
        for timestamp, quotes in analyzed_history['quotes_tracking'].items():
            for quote in quotes:
                filtered_quote = {
                    'screen_name': quote['screen_name'],
                    'followers_count': quote['followers_count'],
                    'verified': quote['verified'],
                    'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat()
                }
                all_quoters.append(filtered_quote)
                
        # Remove duplicates and get top quoters by followers
        seen_quoters = {}
        for quoter in sorted(all_quoters, key=lambda x: x['followers_count'], reverse=True):
            if quoter['screen_name'] not in seen_quoters:
                seen_quoters[quoter['screen_name']] = quoter
        top_quoters = list(seen_quoters.values())[:10]

        # Time Analysis
        time_metrics = []
        for timestamp, metrics in analyzed_history['engagement_metrics'].items():
            total_engagement = (metrics['favorite_count'] + metrics['retweet_count'] + 
                            metrics['reply_count'] + metrics['quote_count'])
            time_metrics.append({
                'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                'total_engagement': total_engagement,
                'views': metrics['views_count']
            })

        # Silent Engagement Analysis
        silent_engagement = []
        for timestamp, metrics in analyzed_history['engagement_metrics'].items():
            silent = metrics['bookmark_count']
            active = (metrics['favorite_count'] + metrics['retweet_count'] + 
                    metrics['reply_count'] + metrics['quote_count'])
            silent_engagement.append({
                'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                'silent_ratio': silent / max(metrics['views_count'], 1),  # Protect division by zero
                'silent_to_active_ratio': silent / max(active, 1)  # Protect division by zero
            })

        # Comment-to-Retweet Ratio
        comment_retweet_ratio = []
        for metrics in analyzed_history['engagement_metrics'].values():
            ratio = metrics['reply_count'] / max(metrics['retweet_count'], 1)  # Protect division by zero
            comment_retweet_ratio.append({
                'ratio': ratio,
                'total_comments': metrics['reply_count'],
                'total_retweets': metrics['retweet_count']
            })

        # Verified Impact Analysis
        verified_impact = []
        metrics_list = list(analyzed_history['engagement_metrics'].items())
        for i, (timestamp, metrics) in enumerate(metrics_list[:-1]):
            verified_activity = metrics['verified_replies'] + metrics['verified_retweets']
            current_engagement = (metrics['favorite_count'] + metrics['retweet_count'] + 
                                metrics['reply_count'] + metrics['quote_count'])
            next_metrics = metrics_list[i + 1][1]
            next_engagement = (next_metrics['favorite_count'] + next_metrics['retweet_count'] + 
                            next_metrics['reply_count'] + next_metrics['quote_count'])
            
            verified_impact.append({
                'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                'verified_engagement': verified_activity,
                'engagement_change': next_engagement - current_engagement
            })

        # Quote vs Regular Retweet Analysis
        quote_retweet_analysis = []
        for timestamp, metrics in analyzed_history['engagement_metrics'].items():
            quote_ratio = metrics['quote_count'] / max(metrics['retweet_count'], 1)  # Protect division by zero
            quote_retweet_analysis.append({
                'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                'quote_ratio': quote_ratio,
                'quotes': metrics['quote_count'],
                'retweets': metrics['retweet_count']
            })

        # Comment Analysis
        comment_analysis = []
        for timestamp, metrics in analyzed_history['engagement_metrics'].items():
            comment_ratio = metrics['reply_count'] / max(metrics['favorite_count'], 1)  # Protect division by zero
            comment_analysis.append({
                'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                'comment_ratio': comment_ratio,
                'comments': metrics['reply_count'],
                'favorites': metrics['favorite_count']
            })

        # Follower Growth Analysis
        follower_growth = []
        follower_items = list(analyzed_history['user_followers'].items())
        for i, (timestamp, count) in enumerate(follower_items):
            growth = count - follower_items[i-1][1] if i > 0 else 0
            if growth != 0:
                follower_growth.append({
                    'timestamp': datetime.utcfromtimestamp(int(timestamp)).isoformat(),
                    'growth': growth,
                    'total_followers': count
                })

        # Calculate peak engagement time
        peak_engagement = max(time_metrics, key=lambda x: x['total_engagement']) if time_metrics else {'timestamp': None, 'total_engagement': 0}

        # Protect division by zero in averages
        verified_impact_with_engagement = [v for v in verified_impact if v['verified_engagement'] > 0]
        average_change_after_verified = (sum(v['engagement_change'] for v in verified_impact_with_engagement) / 
                                       max(len(verified_impact_with_engagement), 1))  # Protect division by zero
        
        average_silent_ratio = (sum(s['silent_ratio'] for s in silent_engagement) / 
                              max(len(silent_engagement), 1))  # Protect division by zero
        
        average_comment_retweet_ratio = (sum(c['ratio'] for c in comment_retweet_ratio) / 
                                       max(len(comment_retweet_ratio), 1))  # Protect division by zero
        
        average_quote_ratio = (sum(q['quote_ratio'] for q in quote_retweet_analysis) / 
                             max(len(quote_retweet_analysis), 1))  # Protect division by zero

        average_comment_ratio = (sum(c['comment_ratio'] for c in comment_analysis) / 
                               max(len(comment_analysis), 1))  # Protect division by zero

        # Handle empty follower_growth
        peak_growth = max(follower_growth, key=lambda x: x['growth']) if follower_growth else None
        growth_during_peak = (
            next((g for g in follower_growth if g['timestamp'] == peak_engagement['timestamp']), None)
            if peak_engagement['timestamp'] and follower_growth
            else None
        )

        return {
            'top_amplifiers': {
                'retweeters': top_retweeters,
                'commenters': top_commenters,
                'quoters': top_quoters
            },
            'engagement_analysis': {
                'peak_engagement_time': peak_engagement['timestamp'],
                'silent_engagement': {
                    'average_silent_ratio': average_silent_ratio,
                    'peak_silent_ratio': max((s['silent_ratio'] for s in silent_engagement), default=0)
                },
                'comment_retweet_ratio': {
                    'average': average_comment_retweet_ratio,
                    'trend': comment_retweet_ratio[-5:] if comment_retweet_ratio else []
                }
            },
            'verified_impact': {
                'average_change_after_verified': average_change_after_verified,
                'total_verified_engagements': sum(v['verified_engagement'] for v in verified_impact)
            },
            'quote_analysis': {
                'average_quote_ratio': average_quote_ratio,
                'total_quotes': quote_retweet_analysis[-1]['quotes'] if quote_retweet_analysis else 0,
                'quote_trend': quote_retweet_analysis[-5:] if quote_retweet_analysis else []
            },
            'comment_analysis': {
                'average_comment_ratio': average_comment_ratio,
                'total_comments': comment_analysis[-1]['comments'] if comment_analysis else 0,
                'comment_trend': comment_analysis[-5:] if comment_analysis else []
            },
            'growth_metrics': {
                'total_growth': sum(g['growth'] for g in follower_growth),
                'peak_growth': peak_growth,
                'growth_during_peak_engagement': growth_during_peak
            }
        }
    