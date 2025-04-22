from fastapi import APIRouter, HTTPException, Query, Depends
import logging
import time
from db.service import Service
from auth.dependencies import auth_middleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tweet", tags=["Tweet"])
service = Service()

@router.get("/feed")
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

@router.post("/monitor/{tweet_id}")
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

@router.post("/analyze/{tweet_id}")
async def analyze_tweet(tweet_id: str, user_id: str = Depends(auth_middleware)):
    """Analyze a tweet"""
    try:
        result = await service.analyze_tweet(tweet_id, with_ai=True)
        return result
    except Exception as e:
        logger.error(f"Error analyzing tweet {tweet_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tweet_id}/history")
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
    




@router.get("/feed/example")
async def get_tweet_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str = Query(default="time", regex="^(time|views)$"),
    sort: str = Query(default="desc", regex="^(asc|desc)$"),
):
    """Get a paginated feed of all monitored tweets with their latest data"""
    try:
        feed = await service.get_user_feed(
            "example",
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
