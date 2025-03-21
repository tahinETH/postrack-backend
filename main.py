
import logging
import os
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Path as FastAPIPath, BackgroundTasks
import asyncio
from typing import Optional
import uvicorn
from pydantic import BaseModel
from db.migrations import connect_and_migrate


from db.service import Service
from config import config
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config import config
import time

import tracemalloc
from auth.dependencies import auth_middleware
from webhooks.clerk import router as clerk_router
from webhooks.stripe import router as stripe_router

tracemalloc.start()
load_dotenv()

ADMIN_SECRET = config.ADMIN_SECRET


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(clerk_router)
app.include_router(stripe_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





service = Service()

class TweetInput(BaseModel):
    tweet_id: str

class AccountInput(BaseModel):
    account_identifier: str  
    action: str  

@app.get("/user")
async def get_user(user_id: str = Depends(auth_middleware)):
    """Get user details"""
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error getting user details at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Account endpoints
@app.post("/account/monitor/{account_identifier}")
async def monitoring_account(
    account_identifier: str, 
    action: str = Query(None, regex="^(start|stop)$"),
    user_id: str = Depends(auth_middleware)
):
    """Start or stop monitoring an account"""
    try:
        
        success = await service.handle_account_monitoring(user_id, account_identifier, action)
        if success:
            return {"status": "success", "message": f"{action.title()}ed monitoring account {account_identifier}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to {action} monitoring account")
    except ValueError as e:
        if str(e) == "Account tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error monitoring account at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Tweet endpoints
@app.get("/tweets")
async def get_monitored_tweets(user_id: str = Depends(auth_middleware)):
    try:
        tweets = service.get_monitored_tweets()
        logger.info(f"Retrieved {len(tweets)} monitored tweets at {int(time.time())}")
        return tweets
    except Exception as e:
        logger.error(f"Error getting monitored tweets at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/tweet/monitor/{tweet_id}")
async def monitoring_tweet(
    tweet_id: str, 
    action: str = Query(..., regex="^(start|stop)$"),
    user_id: str = Depends(auth_middleware)
):
    try:
        success = await service.handle_tweet_monitoring(user_id, tweet_id, action)
        if success:
            return {"status": "success", "message": f"{action.title()}ed monitoring tweet {tweet_id}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to {action} monitoring tweet")
    except ValueError as e:
        if str(e) == "Tweet tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in tweet monitoring action at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/account/analyze/{account_id}")
async def get_account_analysis(account_id: str):
    """Get account analysis"""
    try:
        result = await service.get_account_analysis(account_id)
        return result
    except Exception as e:
        logger.error(f"Error getting account analysis at {int(time.time())}: {str(e)}")



@app.post("/account/analyze/{account_id}")
async def analyze_account(
    account_id: str,
    new_fetch: bool = Query(default=True),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Analyze an account"""
    try:
        background_tasks.add_task(service.analyze_account, account_id, new_fetch=new_fetch)
        return {"status": "success", "message": "Account analysis started"}
    except Exception as e:
        logger.error(f"Error analyzing account {account_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tweet/analyze/{tweet_id}")
async def analyze_tweet(tweet_id: str, user_id: str = Depends(auth_middleware)):
    """Analyze a tweet"""
    try:
        result = await service.analyze_tweet(tweet_id, with_ai=True)
        return result
    except Exception as e:
        logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweet/feed")
async def get_tweet_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str = Query(default="time", regex="^(time|views)$"),
    sort: str = Query(default="desc", regex="^(asc|desc)$"),
    auth_user: str = Depends(auth_middleware)
):
    """Get a paginated feed of all monitored tweets with their latest data"""
    try:
        feed = await service.get_user_feed(
            auth_user,
            skip=(page - 1) * page_size,
            limit=page_size,
            type=type,
            sort=sort
        )
        
        return {
            "status": "success",
            "page": page,
            "page_size": page_size,
            "total_count": feed["total_count"],
            "has_next": page * page_size < feed["total_count"],
            "has_previous": page > 1,
            "feed": feed
        }
    except Exception as e:
        logger.error(f"Error getting tweet feed at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving tweet feed")


@app.get("/tweet/{tweet_id}/history")
async def get_tweet_history(
    tweet_id: str, 
    format: str = Query(..., regex="^(raw|analyzed)$"),
    user_id: str = Depends(auth_middleware)
):
    """Get tweet history in raw or analyzed format"""
    try:
        history = await service.get_tweet_history(tweet_id, format)
        if not history:
            raise HTTPException(status_code=404, detail="Tweet not found")
        return history
    except Exception as e:
        logger.error(f"Error getting tweet history at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





""" @app.post("/admin/account/monitor/all-accounts")
async def manage_all_accounts(action: str = Query(..., regex="^(start|stop)$"), admin_secret: str = Header(None)):
    if not admin_secret or admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    try:
        success = await service.handle_all_accounts(action)
        if success:
            return {"status": "success", "message": f"{action.title()}ed monitoring all accounts"}
        raise HTTPException(status_code=500, detail=f"Failed to {action} monitoring all accounts")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error {action}ing all account monitoring at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
     """
"""     
@app.post("/admin/tweets/{action}")
async def handle_all_tweets(
    action: str = FastAPIPath(..., regex="^(start|stop)$"),
    admin_secret: str = Header(None)
):
    if not admin_secret or admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    try:
        success = await service.handle_all_tweets(action)
        if success:
            return {"status": "success", "message": f"Successfully {action}ed tweets"}
        raise HTTPException(status_code=500, detail=f"Failed to {action} tweets")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error handling all tweets at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) """

# Background tasks


@app.on_event("startup")
async def startup_event():
    """Initialize database and start the periodic check on startup"""
    try:
        
        if not config.DB_PATH:
            raise ValueError("DB_PATH environment variable not set")
            
        # Run migrations
        await connect_and_migrate(config.DB_PATH)
        logger.info("Database migrations completed successfully")
        
        # Start periodic checks
        logger.info(f"Starting tweet monitoring background task at {int(time.time())}")
        asyncio.create_task(service.handle_periodic_checks())
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)