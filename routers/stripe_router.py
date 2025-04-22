from fastapi import APIRouter, HTTPException, Depends
import logging
import time
from db.service import Service
from auth.dependencies import auth_middleware

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stripe", tags=["Stripe"])
service = Service()

@router.post("/create-checkout-session")
async def create_checkout_session(user_id: str = Depends(auth_middleware)):
    try:
        session = await service.create_checkout_session(user_id)
        return {"status": "success", "session": session}
    except Exception as e:
        logger.error(f"Error creating checkout session at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 