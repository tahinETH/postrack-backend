from fastapi import APIRouter, HTTPException, Query, Depends, Header, BackgroundTasks
import logging
import time
import asyncio
from db.service import Service
from auth.dependencies import auth_middleware
from config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/account", tags=["Account"])
service = Service()
ADMIN_SECRET = config.ADMIN_SECRET

@router.post("/monitor/{account_identifier}")
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
    


@router.get("/analyze/example")
async def get_account_analysis():
    try:
        result = await service.get_account_analysis("example", "example")
        return result
    except Exception as e:
        logger.error(f"Error getting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{account_id}")
async def get_account_analysis(account_id: str, user_id: str = Depends(auth_middleware)):
    try:
        result = await service.get_account_analysis(account_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/{screen_name}")
async def analyze_account(
    screen_name: str,
    background_tasks: BackgroundTasks,
    new_fetch: bool = Query(default=True),
    user_id: str = Depends(auth_middleware),
):
    """Analyze an account"""
    try:
        background_tasks.add_task(service.analyze_account, screen_name, new_fetch, user_id)
        return {"status": "success", "message": "Account analysis started"}
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing account {screen_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/analyze/{account_id}")
async def delete_account_analysis(account_id:str, user_id: str = Depends(auth_middleware)):
    """Delete account analysis"""
    try:
        result = await service.delete_account_analysis(user_id, account_id)
        return {"status": "success", "message": f"Account analysis for {account_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting account analysis at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin routes
@router.get("/admin/analyze/{account_id}")
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

@router.post("/admin/analyze/{screen_name}")
async def admin_analyze_account(
    screen_name: str,
    background_tasks: BackgroundTasks,
    new_fetch: bool = Query(default=True),
    admin_secret: str = Header(None)
):
    """Analyze an account"""
    try:
        if admin_secret != ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid admin secret")
        user_id = "admin"
        background_tasks.add_task(service.analyze_account, screen_name, new_fetch, user_id)
        return {"status": "success", "message": "Account analysis started"}
    except ValueError as e:
        if str(e) == "Analysis tracking limit reached for user's tier":
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing account {screen_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/analyze/{account_id}")
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
