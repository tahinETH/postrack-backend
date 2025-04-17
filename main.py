import logging
import os
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Path as FastAPIPath
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

app = FastAPI(
    title="Twitter Analytics API",
    description="API for analyzing and monitoring Twitter accounts and tweets",
    version="1.0.0",
    tags=[
        {"name": "User", "description": "User management endpoints"},
        {"name": "Account", "description": "Twitter account monitoring and analysis"},
        {"name": "Tweet", "description": "Tweet monitoring and analysis"},
        {"name": "Workshop", "description": "Tweet writing assistance tools"},
        {"name": "Admin", "description": "Administrative endpoints"}
    ]
)

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

class RefinementInput(BaseModel):
    tweet_text: str
    account_id: str = None
    additional_commands: str

class InspirationInput(BaseModel):
    tweet_id: str
    account_id: str = None
    is_thread: bool
    additional_commands: str

class VisualizationInput(BaseModel):
    tweet_text: str

class StandaloneInput(BaseModel):
    input_text: str
    account_id: str = None
    additional_commands: str
    is_thread: bool
    
@app.get("/user", tags=["User"])
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

@app.post("/account/monitor/{account_identifier}", tags=["Account"])
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

@app.get("/account/analyze/{account_id}", tags=["Account"])
async def get_account_analysis(account_id: str, user_id: str = Depends(auth_middleware)):
    try:
        result = await service.get_account_analysis(account_id, user_id)
        
        return result
    except Exception as e:
        logger.error(f"Error getting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/account/analyze/{screen_name}", tags=["Account"])
async def analyze_account(
    screen_name: str,
    new_fetch: bool = Query(default=True),
    user_id: str = Depends(auth_middleware),
    
):
    """Analyze an account"""
    try:
        asyncio.create_task(service.analyze_account(screen_name, new_fetch=new_fetch, user_id=user_id))
        return {"status": "success", "message": "Account analysis started"}
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing account {screen_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/account/analyze/{account_id}", tags=["Account"])
async def delete_account_analysis(account_id:str, user_id: str = Depends(auth_middleware)):
    """Delete account analysis"""
    try:
        result = await service.delete_account_analysis(user_id, account_id)
        return {"status": "success", "message": f"Account analysis for {account_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweets", tags=["Tweet"])
async def get_monitored_tweets(user_id: str = Depends(auth_middleware)):
    """Get all monitored tweets"""
    try:
        tweets = service.get_monitored_tweets()
        logger.info(f"Retrieved {len(tweets)} monitored tweets at {int(time.time())}")
        return tweets
    except Exception as e:
        logger.error(f"Error getting monitored tweets at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tweet/monitor/{tweet_id}", tags=["Tweet"])
async def monitoring_tweet(
    tweet_id: str, 
    action: str = Query(..., regex="^(start|stop)$"),
    user_id: str = Depends(auth_middleware)
):
    """Start or stop monitoring a tweet"""
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


@app.post("/tweet/analyze/{tweet_id}", tags=["Tweet"])
async def analyze_tweet(tweet_id: str, user_id: str = Depends(auth_middleware)):
    """Analyze a tweet"""
    try:
        result = await service.analyze_tweet(tweet_id, with_ai=True)
        return result
    except Exception as e:
        logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tweet/feed", tags=["Tweet"])
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
    
@app.get("/tweet/feed", tags=["Tweet"])
async def get_tweet_feed_example(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str = Query(default="time", regex="^(time|views)$"),
    sort: str = Query(default="desc", regex="^(asc|desc)$"),
    
):
    """Get a paginated feed of all monitored tweets with their latest data"""
    try:
        feed = await service.get_user_feed(
            "mock_user",
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


@app.get("/tweet/{tweet_id}/history", tags=["Tweet"])
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

@app.post("/workshop/standalone", tags=["Workshop"])
async def get_standalone_tweet_ideas(
    input_data: StandaloneInput,
    user_id: str = Depends(auth_middleware)
):
    try:
        ideas = await service.get_standalone_tweet_ideas(user_id, input_data.input_text, input_data.account_id, input_data.additional_commands, input_data.is_thread)
        return {"status": "success", "ideas": ideas}
    except Exception as e:
        logger.error(f"Error getting standalone tweet ideas at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/workshop/inspiration", tags=["Workshop"])
async def get_tweet_inspiration(
    input_data: InspirationInput,
    user_id: str = Depends(auth_middleware)
):
    try:
        inspiration = await service.get_content_inspiration(input_data.tweet_id, input_data.account_id, input_data.is_thread, user_id, input_data.additional_commands)
        return {"status": "success", "inspiration": inspiration}
    except Exception as e:
        logger.error(f"Error getting tweet inspiration at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workshop/refinement", tags=["Workshop"])
async def refine_tweet(
    input_data: RefinementInput,
    user_id: str = Depends(auth_middleware)
):
    try:
        refinements = await service.get_tweet_refinements(user_id, input_data.tweet_text, input_data.account_id, input_data.additional_commands)
        return {"status": "success", "refinements": refinements}
    except Exception as e:
        logger.error(f"Error getting tweet refinements main at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/workshop/visualization", tags=["Workshop"])
async def get_visualization_ideas(
    input_data: VisualizationInput,
    user_id: str = Depends(auth_middleware)
):
    try:
        ideas = await service.get_visualization_ideas(input_data.tweet_text)
        return {"status": "success", "ideas": ideas}
    except Exception as e:
        logger.error(f"Error getting visualization ideas at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    



@app.get("/admin/account/analyze/{account_id}", tags=["Admin"])
async def admin_get_account_analysis(account_id: str, admin_secret: str = Header(None)):
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        result = await service.get_account_analysis(account_id, user_id)
        
        return result
    except Exception as e:
        logger.error(f"Error getting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/account/analyze/{screen_name}", tags=["Admin"])
async def admin_analyze_account(
    screen_name: str,
    new_fetch: bool = Query(default=True),
    admin_secret: str = Header(None)
):
    """Analyze an account"""
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        asyncio.create_task(service.analyze_account(screen_name, new_fetch=new_fetch, user_id=user_id))
        return {"status": "success", "message": "Account analysis started"}
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing account {screen_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/account/analyze/{account_id}", tags=["Admin"])
async def admin_delete_account_analysis(account_id: str, admin_secret: str = Header(None)):
    """Delete account analysis"""
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        result = await service.delete_account_analysis(user_id, account_id)
        return {"status": "success", "message": f"Account analysis for {account_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





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
        # logger.info(f"Starting tweet monitoring background task at {int(time.time())}")
        asyncio.create_task(service.handle_periodic_checks())

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)