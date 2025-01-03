from datetime import datetime
import logging
import os
from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
import asyncio
from typing import List, Dict, Any
import uvicorn
from pydantic import BaseModel
from monitor import TweetMonitor
from repositories.tw_data import TweetDataRepository
from repositories.tw_analysis import TweetAnalysisRepository
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
SOCIAL_DATA_API_KEY = os.getenv("SOCIAL_DATA_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


INTERVAL_MINUTES = 5
monitor = TweetMonitor(DB_PATH, SOCIAL_DATA_API_KEY, INTERVAL_MINUTES)
repository = TweetAnalysisRepository(DB_PATH)


class TweetInput(BaseModel):
    tweet_id: str

class AccountInput(BaseModel):
    account_identifier: str  
    action: str  

@app.post("/tweet/monitor/{tweet_id}")
async def monitor_tweet(tweet_id: str, action: str = Query(..., regex="^(start|stop)$")):
    """Start or stop monitoring a tweet"""
    try:
        if action == "start":
            monitor.repo.add_monitored_tweet(tweet_id)
            await monitor.monitor_tweet(tweet_id)
            logger.info(f"Started monitoring tweet {tweet_id} at {int(time.time())}")
            return {"status": "success", "message": f"Now monitoring tweet {tweet_id}"}
        else:  # action == "stop"
            monitor.repo.stop_monitoring_tweet(tweet_id)
            logger.info(f"Stopped monitoring tweet {tweet_id} at {int(time.time())}")
            return {"status": "success", "message": f"Stopped monitoring tweet {tweet_id}"}
    except Exception as e:
        logger.error(f"Error in tweet monitoring action at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


    
@app.post("/account/monitor/stop-all-accounts")
async def stop_all_accounts():
    try:
        monitor.repo.stop_all_accounts()
        logger.info(f"Stopped monitoring all accounts at {int(time.time())}")
        return {"status": "success", "message": f"Stopped monitoring all accounts"}
    except Exception as e:
        logger.error(f"Error stopping all account monitoring at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/account/monitor/start-all-accounts")
async def start_all_accounts():
    try:
        monitor.repo.start_all_accounts()
        logger.info(f"Started monitoring all accounts at {int(time.time())}")
        return {"status": "success", "message": f"Started monitoring all accounts"}
    except Exception as e:
        logger.error(f"Error starting all account monitoring at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweet/feed")
async def get_tweet_feed():
    """Get a feed of all monitored tweets with their latest data"""
    try:
        # Get the feed data
        feed = monitor.repo.get_feed()
        
        return {
            "status": "success", 
            "count": len(feed),
            "feed": feed
        }
    except Exception as e:
        # Add flush=True to error logs as well
        logger.error(f"Error getting tweet feed at {int(time.time())}: {str(e)}")
        
        raise HTTPException(status_code=500, detail="Error retrieving tweet feed")

@app.get("/tweet/{tweet_id}/history")
async def get_tweet_history(tweet_id: str, format: str = Query(..., regex="^(raw|analyzed)$")):
    """Get tweet history in raw or analyzed format"""
    try:
        if format == "raw":
            history = monitor.repo.get_raw_tweet_history(tweet_id)
        else:  # format == "analyzed"
            history = monitor.repo.get_analyzed_tweet_history(tweet_id)
            
        if not history:
            logger.warning(f"Tweet history not found for {tweet_id} at {int(time.time())}")
            raise HTTPException(status_code=404, detail="Tweet not found")
            
        logger.info(f"Retrieved {format} history for tweet {tweet_id} at {int(time.time())}")
        return history
    except Exception as e:
        logger.error(f"Error getting tweet history at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/account/monitor/{account_identifier}")
async def monitor_account(account_identifier: str, action: str = Query(None, regex="^(start|stop)$")):
    """Start or stop monitoring an account"""
    try:
        if action == "start":
            success = await monitor.monitor_account(account_identifier)
            
            if success:
                return {"status": "success", "message": f"Started monitoring account {account_identifier}"}
            else:
                raise HTTPException(status_code=500, detail="Failed to start monitoring account")
        elif action == "stop":
            monitor.repo.stop_monitoring_account(account_identifier)
            return {"status": "success", "message": f"Stopped monitoring account {account_identifier}"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except Exception as e:
        logger.error(f"Error monitoring account at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tweets/start-all") 
async def start_all_tweets():
    try:
        tweets = monitor.repo.get_monitored_tweets()
        started_count = 0
        for tweet in tweets:
            if not tweet['is_active']:
                monitor.repo.add_monitored_tweet(tweet['tweet_id'])
                await monitor.monitor_tweet(tweet['tweet_id'])
                started_count += 1
        logger.info(f"Started monitoring {started_count} inactive tweets at {int(time.time())}")
        return {"status": "success", "message": f"Started monitoring {started_count} inactive tweets"}
    except Exception as e:
        logger.error(f"Error starting all tweet monitoring at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweets")
async def get_monitored_tweets():
    try:
        tweets = monitor.repo.get_monitored_tweets()
        logger.info(f"Retrieved {len(tweets)} monitored tweets at {int(time.time())}")
        return tweets
    except Exception as e:
        logger.error(f"Error getting monitored tweets at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tweets/{tweet_id}")
async def delete_monitored_tweet(tweet_id: str):
    try:
        monitor.repo.delete_monitored_tweet(tweet_id)
        logger.info(f"Deleted tweet {tweet_id} from monitoring at {int(time.time())}")
        return {"status": "success", "message": f"Deleted tweet {tweet_id} from monitoring"}
    except Exception as e:
        logger.error(f"Error deleting monitored tweet at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def periodic_single_tweet_check():
    """Periodic task to check and update tweets"""
    while True:
        try:
            logger.info(f"Running periodic tweet check at {int(time.time())}")
            await monitor.check_and_update_tweets()
        except Exception as e:
            logger.error(f"Error in periodic check at {int(time.time())}: {str(e)}")
        finally:
            # Run check every minute
            await asyncio.sleep(60)

async def periodic_account_check():
    """Periodic task to check and update accounts"""
    while True:
        try:
            logger.info(f"Running periodic account check at {int(time.time())}")
            await monitor.check_and_update_accounts()
        except Exception as e:
            logger.error(f"Error in periodic check at {int(time.time())}: {str(e)}")
        finally:
            # Run check every minute
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start the periodic check on startup"""
    logger.info(f"Starting tweet monitoring background task at {int(time.time())}")
    asyncio.create_task(periodic_single_tweet_check())
    asyncio.create_task(periodic_account_check())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)