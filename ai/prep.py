from datetime import datetime
from typing import Dict, Any, List
from repositories.tw_analysis import TweetRepository


def prepare_insight_data(analyzed_history: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze tweet history data and prepare insights"""
    if not analyzed_history:
        return {}

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
            comment['timestamp'] = int(timestamp)
            all_commenters.append(comment)
            
    # Remove duplicates and get top commenters by followers
    seen_commenters = {}
    for commenter in sorted(all_commenters, key=lambda x: x['followers_count'], reverse=True):
        if commenter['screen_name'] not in seen_commenters:
            seen_commenters[commenter['screen_name']] = commenter
    top_commenters = list(seen_commenters.values())[:10]

    # Time Analysis
    time_metrics = []
    for timestamp, metrics in analyzed_history['engagement_metrics'].items():
        total_engagement = (metrics['favorite_count'] + metrics['retweet_count'] + 
                          metrics['reply_count'] + metrics['quote_count'])
        time_metrics.append({
            'timestamp': int(timestamp),
            'total_engagement': total_engagement,
            'views': metrics['views_count'],
            'time_of_day': datetime.fromtimestamp(int(timestamp)).hour
        })

    # Silent Engagement Analysis
    silent_engagement = []
    for timestamp, metrics in analyzed_history['engagement_metrics'].items():
        silent = metrics['bookmark_count']
        active = (metrics['favorite_count'] + metrics['retweet_count'] + 
                 metrics['reply_count'] + metrics['quote_count'])
        silent_engagement.append({
            'timestamp': int(timestamp),
            'silent_ratio': silent / metrics['views_count'] if metrics['views_count'] else 0,
            'silent_to_active_ratio': silent / active if active else 0
        })

    # Comment-to-Retweet Ratio
    comment_retweet_ratio = []
    for metrics in analyzed_history['engagement_metrics'].values():
        ratio = metrics['reply_count'] / metrics['retweet_count'] if metrics['retweet_count'] else 0
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
            'timestamp': int(timestamp),
            'verified_engagement': verified_activity,
            'engagement_change': next_engagement - current_engagement
        })

    # Quote vs Regular Retweet Analysis
    quote_retweet_analysis = []
    for timestamp, metrics in analyzed_history['engagement_metrics'].items():
        quote_ratio = metrics['quote_count'] / metrics['retweet_count'] if metrics['retweet_count'] else 0
        quote_retweet_analysis.append({
            'timestamp': int(timestamp),
            'quote_ratio': quote_ratio,
            'quotes': metrics['quote_count'],
            'retweets': metrics['retweet_count']
        })

    # Follower Growth Analysis
    follower_growth = []
    follower_items = list(analyzed_history['user_followers'].items())
    for i, (timestamp, count) in enumerate(follower_items):
        growth = count - follower_items[i-1][1] if i > 0 else 0
        if growth != 0:
            follower_growth.append({
                'timestamp': int(timestamp),
                'growth': growth,
                'total_followers': count
            })

    # Calculate peak engagement time
    peak_engagement = max(time_metrics, key=lambda x: x['total_engagement'])

    # Group time metrics by hour
    time_distribution = {}
    for metric in time_metrics:
        hour = metric['time_of_day']
        if hour not in time_distribution:
            time_distribution[hour] = []
        time_distribution[hour].append(metric)

    return {
        'top_amplifiers': {
            'retweeters': top_retweeters,
            'commenters': top_commenters
        },
        'engagement_analysis': {
            'time_distribution': time_distribution,
            'peak_engagement_time': peak_engagement['timestamp'],
            'silent_engagement': {
                'average_silent_ratio': sum(s['silent_ratio'] for s in silent_engagement) / len(silent_engagement),
                'peak_silent_ratio': max(s['silent_ratio'] for s in silent_engagement)
            },
            'comment_retweet_ratio': {
                'average': sum(c['ratio'] for c in comment_retweet_ratio) / len(comment_retweet_ratio),
                'trend': comment_retweet_ratio[-5:]
            }
        },
        'verified_impact': {
            'average_change_after_verified': sum(v['engagement_change'] for v in verified_impact 
                                               if v['verified_engagement'] > 0) / 
                                           len([v for v in verified_impact if v['verified_engagement'] > 0]),
            'total_verified_engagements': sum(v['verified_engagement'] for v in verified_impact)
        },
        'quote_analysis': {
            'average_quote_ratio': sum(q['quote_ratio'] for q in quote_retweet_analysis) / len(quote_retweet_analysis),
            'total_quotes': quote_retweet_analysis[-1]['quotes'],
            'quote_trend': quote_retweet_analysis[-5:]
        },
        'growth_metrics': {
            'total_growth': sum(g['growth'] for g in follower_growth),
            'peak_growth': max(follower_growth, key=lambda x: x['growth']),
            'growth_during_peak_engagement': next((g for g in follower_growth 
                                                 if g['timestamp'] == peak_engagement['timestamp']), None)
        }
    }
