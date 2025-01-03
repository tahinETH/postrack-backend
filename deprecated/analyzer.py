import json
from datetime import datetime
from typing import Dict, List, Set
import glob
import os

class TweetMonitor:
    def __init__(self, tweet_id: str):
        self.tweet_id = tweet_id
        self.timestamps: Set[int] = set()
        self.engagement_metrics: Dict[int, Dict] = {}
        self.comments_tracking: Dict[int, List[Dict]] = {}
        self.retweeters_tracking: Dict[int, List[Dict]] = {}
        
    @staticmethod
    def get_timestamp_from_filename(filename: str) -> int:
        """Extract timestamp from filename and convert to unix timestamp"""
        # Expects format: tweet_ID_type_YYYYMMDD_HHMMSS.json
        date_str = filename.split('_')[-2]
        time_str = filename.split('_')[-1].replace('.json', '')
        dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        return int(dt.timestamp())
    
    @staticmethod
    def get_all_timestamps(directory: str, tweet_id: str) -> List[int]:
        """Get all unique timestamps from available files"""
        pattern = f"{directory}/tweet_{tweet_id}_*_*.json"
        timestamps = set()
        for filename in glob.glob(pattern):
            ts = TweetMonitor.get_timestamp_from_filename(filename)
            timestamps.add(ts)
        return sorted(list(timestamps))
    
    @staticmethod
    def get_files_for_timestamp(directory: str, tweet_id: str, timestamp: int) -> Dict[str, str]:
        """Get all files for a specific timestamp"""
        dt = datetime.fromtimestamp(timestamp)
        timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
        
        files = {
            'details': f"{directory}/tweet_{tweet_id}_details_{timestamp_str}.json",
            'comments': f"{directory}/tweet_{tweet_id}_comments_{timestamp_str}.json",
            'retweeters': f"{directory}/tweet_{tweet_id}_retweeters_{timestamp_str}.json"
        }
        
        # Verify files exist
        for file_type, filepath in files.items():
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Missing {file_type} file for timestamp {timestamp}")
                
        return files

    def process_timestamp(self, timestamp: int, details_json: str, comments_json: str, retweeters_json: str) -> None:
        """Process data for a single timestamp"""
        self.timestamps.add(timestamp)
        
        # Process details (engagement metrics)
        details = json.loads(details_json)
        self.engagement_metrics[timestamp] = {
            'quote_count': details['quote_count'],
            'reply_count': details['reply_count'],
            'retweet_count': details['retweet_count'],
            'favorite_count': details['favorite_count'],
            'views_count': details['views_count'],
            'bookmark_count': details['bookmark_count']
        }
        
        # Process comments
        comments = json.loads(comments_json)
        existing_comment_ids = set()
        for ts in self.comments_tracking.values():
            for comment in ts:
                existing_comment_ids.add(comment['id'])
                
        new_comments = []
        for comment in comments['data']:
            if comment['id'] not in existing_comment_ids:
                new_comments.append({
                    'id': comment['id'],
                    'favorite_count': comment['favorite_count'],
                    'views_count': comment['views_count'],
                    'bookmark_count': comment['bookmark_count'],
                    'screen_name': comment['user']['screen_name'],
                    'followers_count': comment['user']['followers_count']
                })
        
        if new_comments:
            self.comments_tracking[timestamp] = new_comments
            
        # Process retweeters
        retweeters = json.loads(retweeters_json)
        existing_retweeter_names = set()
        for ts in self.retweeters_tracking.values():
            for retweeter in ts:
                existing_retweeter_names.add(retweeter['screen_name'])
                
        new_retweeters = []
        for retweeter in retweeters['data']:
            if retweeter['screen_name'] not in existing_retweeter_names:
                new_retweeters.append({
                    'screen_name': retweeter['screen_name'],
                    'followers_count': retweeter['followers_count']
                })
                
        if new_retweeters:
            self.retweeters_tracking[timestamp] = new_retweeters

    def process_all_files(self, directory: str = '.') -> None:
        """Process all available files for the tweet"""
        timestamps = self.get_all_timestamps(directory, self.tweet_id)
        
        for ts in timestamps:
            try:
                files = self.get_files_for_timestamp(directory, self.tweet_id, ts)
                
                # Read files
                with open(files['details'], 'r') as f:
                    details_json = f.read()
                with open(files['comments'], 'r') as f:
                    comments_json = f.read()
                with open(files['retweeters'], 'r') as f:
                    retweeters_json = f.read()
                    
                self.process_timestamp(ts, details_json, comments_json, retweeters_json)
                print(f"Processed timestamp: {ts}")
                
            except Exception as e:
                print(f"Error processing timestamp {ts}: {str(e)}")
                continue
    
    def get_engagement_changes(self) -> Dict:
        """Get engagement metric changes between timestamps"""
        sorted_timestamps = sorted(self.timestamps)
        changes = {}
        
        for i in range(1, len(sorted_timestamps)):
            prev_ts = sorted_timestamps[i-1]
            curr_ts = sorted_timestamps[i]
            
            changes[curr_ts] = {
                metric: self.engagement_metrics[curr_ts][metric] - self.engagement_metrics[prev_ts][metric]
                for metric in self.engagement_metrics[curr_ts].keys()
            }
            
        return changes

    def get_summary_data(self) -> Dict:
        """Get all data in a format suitable for JSON export"""
        return {
            'tweet_id': self.tweet_id,
            'timestamps': sorted(list(self.timestamps)),
            'engagement_metrics': self.engagement_metrics,
            'comments_tracking': self.comments_tracking,
            'retweeters_tracking': self.retweeters_tracking,
            'engagement_changes': self.get_engagement_changes()
        }
    
    def print_summary(self) -> None:
        """Print a summary of all tracked changes"""
        sorted_timestamps = sorted(self.timestamps)
        
        print("=== Engagement Metrics ===")
        for ts in sorted_timestamps:
            print(f"\nTimestamp: {ts}")
            for metric, value in self.engagement_metrics[ts].items():
                print(f"{metric}: {value}")
                
        print("\n=== New Comments ===")
        for ts in sorted_timestamps:
            if ts in self.comments_tracking:
                print(f"\nTimestamp: {ts}")
                for comment in self.comments_tracking[ts]:
                    print(f"- @{comment['screen_name']} "
                          f"(followers: {comment['followers_count']}) "
                          f"[♥️ {comment['favorite_count']} "
                          f"👁️ {comment['views_count']} "
                          f"🔖 {comment['bookmark_count']}]")
                    
        print("\n=== New Retweeters ===")
        for ts in sorted_timestamps:
            if ts in self.retweeters_tracking:
                print(f"\nTimestamp: {ts}")
                for retweeter in self.retweeters_tracking[ts]:
                    print(f"- @{retweeter['screen_name']} "
                          f"(followers: {retweeter['followers_count']})")

def main():
    # Directory containing the JSON files
    data_dir = "."
    
    # Initialize monitor
    tweet_id = "1873069737112219895"
    monitor = TweetMonitor(tweet_id)
    
    # Process all available files
    monitor.process_all_files(data_dir)
    
    # Print summary
    monitor.print_summary()
    
    # Get and print engagement changes
    changes = monitor.get_engagement_changes()
    print("\n=== Engagement Changes ===")
    for ts, metrics in changes.items():
        print(f"\nChanges at {ts}:")
        for metric, change in metrics.items():
            if change != 0:
                print(f"{metric}: {'+' if change > 0 else ''}{change}")
    
    # Export all data to JSON file
    output_file = f"tweet_{tweet_id}_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(monitor.get_summary_data(), f, indent=4)
    print(f"\nAnalysis data exported to {output_file}")

if __name__ == "__main__":
    main()