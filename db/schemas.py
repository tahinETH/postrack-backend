from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, BigInteger, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MonitoredAccount(Base):
    __tablename__ = 'monitored_accounts'
    account_id = Column(String, primary_key=True)
    screen_name = Column(String)
    created_at = Column(Integer, nullable=False)
    last_check = Column(Integer)
    is_active = Column(Boolean, default=False)
    account_details = Column(String)

class MonitoredTweet(Base):
    __tablename__ = 'monitored_tweets'
    tweet_id = Column(String, primary_key=True)
    user_screen_name = Column(String)
    account_id = Column(String)
    created_at = Column(Integer, nullable=False)
    last_check = Column(Integer)
    is_active = Column(Boolean, default=True)

class TweetDetail(Base):
    __tablename__ = 'tweet_details'
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, ForeignKey('monitored_tweets.tweet_id'), nullable=False)
    data_json = Column(String, nullable=False)
    captured_at = Column(Integer, nullable=False)

class TweetComment(Base):
    __tablename__ = 'tweet_comments'
    comment_id = Column(String, primary_key=True)
    tweet_id = Column(String, ForeignKey('monitored_tweets.tweet_id'), nullable=False)
    data_json = Column(String, nullable=False)
    captured_at = Column(Integer, nullable=False)

class TweetQuote(Base):
    __tablename__ = 'tweet_quotes'
    quote_id = Column(String, primary_key=True)
    tweet_id = Column(String, ForeignKey('monitored_tweets.tweet_id'), nullable=False)
    data_json = Column(String, nullable=False)
    captured_at = Column(Integer, nullable=False)

class TweetRetweeter(Base):
    __tablename__ = 'tweet_retweeters'
    user_id = Column(String, primary_key=True)
    tweet_id = Column(String, ForeignKey('monitored_tweets.tweet_id'), primary_key=True)
    data_json = Column(String, nullable=False)
    captured_at = Column(Integer, nullable=False)

class AIAnalysis(Base):
    __tablename__ = 'ai_analysis'
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, ForeignKey('monitored_tweets.tweet_id'), nullable=False)
    analysis = Column(String, nullable=False)
    input_data = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)

class AccountAnalysis(Base):
    __tablename__ = 'account_analysis'
    id = Column(Integer, primary_key=True)
    account_id = Column(String, ForeignKey('monitored_accounts.account_id'), nullable=False)
    top_tweets = Column(JSON, nullable=True)  # Store top tweets data
    metrics = Column(JSON, nullable=True)  # Engagement rates, growth trends etc
    quantitative_analysis = Column(JSON, nullable=True)  # Engagement rates, growth trends etc
    qualitative_analysis = Column(String, nullable=True)  # Overall account analysis textc
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

class SubscriptionTier(Base):
    __tablename__ = 'subscription_tiers'
    tier_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)  # Price in cents
    features = Column(JSON)
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    
    # Subscription related fields
    current_tier = Column(String, default="tier0")  # free tier by default
    current_period_start = Column(Integer, nullable=True)
    current_period_end = Column(Integer, nullable=True)
    
    # Stripe specific fields
    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    
    # Additional metadata
    fe_metadata = Column(JSON, nullable=True)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)


class UserTrackedItem(Base):
    __tablename__ = "user_tracked_items"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tracked_type = Column(String, nullable=False)  # 'tweet' or 'account'
    tracked_id = Column(String, nullable=False)
    tracked_account_name = Column(String, nullable=True)  # Only for accounts
    captured_at = Column(Integer, nullable=False)

class APICall(Base):
    __tablename__ = 'api_calls'
    monitor_timestamp = Column(Integer, primary_key=True)
    tweet_details_calls = Column(Integer)
    retweet_api_calls = Column(Integer)
    quote_api_calls = Column(Integer)
    comment_api_calls = Column(Integer)
    total_api_calls = Column(Integer)

