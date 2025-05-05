from fastapi import APIRouter, HTTPException, Query, Depends, Header
import logging
import time
from db.service import Service
from auth.dependencies import auth_middleware
from config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/community", tags=["Community"])
service = Service()
ADMIN_SECRET = config.ADMIN_SECRET

@router.post("/analyze/{community_id}")
async def analyze_community(
    community_id: str,
    new_fetch: bool = Query(default=True),
    user_id: str = Depends(auth_middleware),
):
    """Analyze a community"""
    try:
        result = await service.analyze_community(community_id, new_fetch=new_fetch, user_id=user_id)
        return result
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing community {community_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{community_id}")
async def get_community_analysis(community_id: str, user_id: str = Depends(auth_middleware)):
    """Get community analysis"""
    try:
        result = await service.get_community_analysis(community_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting community analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/analyze/{community_id}")
async def delete_community_analysis(community_id:str, user_id: str = Depends(auth_middleware)):
    """Delete community analysis"""
    try:
        result = await service.delete_community_analysis(user_id, community_id)
        return {"status": "success", "message": f"Community analysis for {community_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting community analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/analyze/{community_id}")
async def admin_get_community_analysis(community_id: str, admin_secret: str = Header(None)):
    """Admin endpoint to get community analysis"""
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        result = await service.get_community_analysis(community_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting community analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/analyze/{community_id}")
async def admin_analyze_community(
    community_id: str,
    new_fetch: bool = Query(default=True),
    admin_secret: str = Header(None)
):
    """Admin endpoint to analyze a community"""
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        await service.analyze_community(community_id, new_fetch=new_fetch, user_id=user_id)
        return {"status": "success", "message": "Community analysis started"}
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing community {community_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
