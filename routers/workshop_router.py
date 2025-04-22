from fastapi import APIRouter, HTTPException, Depends
import logging
import time
from db.service import Service
from auth.dependencies import auth_middleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workshop", tags=["Workshop"])
service = Service()

class StandaloneInput(BaseModel):
    input_text: str
    account_id: str = None
    additional_commands: str
    is_thread: bool

class InspirationInput(BaseModel):
    tweet_id: str
    account_id: str = None
    is_thread: bool
    additional_commands: str

class RefinementInput(BaseModel):
    tweet_text: str
    account_id: str = None
    additional_commands: str

class VisualizationInput(BaseModel):
    tweet_text: str

@router.post("/standalone")
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

@router.post("/inspiration")
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

@router.post("/refinement")
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

@router.post("/visualization")
async def get_visualization_ideas(
    input_data: VisualizationInput,
    user_id: str = Depends(auth_middleware)
):
    try:
        ideas = await service.get_visualization_ideas(user_id,input_data.tweet_text)
        return {"status": "success", "ideas": ideas}
    except Exception as e:
        logger.error(f"Error getting visualization ideas at {int(time.time())}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 