from fastapi import APIRouter, HTTPException, Depends
import logging
import time
from db.service import Service
from auth.dependencies import auth_middleware

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])
service = Service()

@router.get("")
async def get_user(user_id: str = Depends(auth_middleware)):
    """Get user details"""
    try:
        user = await service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error getting user details at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 