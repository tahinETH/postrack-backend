from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import logging
from typing import Dict, Any
from config import config
from db.users.user_db import UserDataRepository
from analysis.account import AccountAnalyzer
from db.tw.structured import TweetStructuredRepository

logger = logging.getLogger(__name__)

router = APIRouter()
user_db = UserDataRepository()
analysis_repo = TweetStructuredRepository()
account_analyzer = AccountAnalyzer(analysis_repo, config.SOCIAL_DATA_API_KEY)

@router.post("/fe-ws")
async def handle_frontend_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming frontend webhooks for account analysis completion."""
    try:
        # Log incoming webhook request
        logger.info(f"Received frontend webhook from {request.client.host}")
        
        payload = await request.json()
        
        # Validate required fields
        if not all(k in payload for k in ["user_id", "account_id", "event_type"]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        user_id = payload["user_id"]
        account_id = payload["account_id"]
        event_type = payload["event_type"]
        
        logger.info(f"Processing frontend webhook: {event_type} for user {user_id}")
        
        if event_type == "account_analysis_request":
            # Add the analysis task to background tasks
            background_tasks.add_task(process_account_analysis, user_id, account_id)
            return {"status": "success", "message": "Account analysis request received"}
        else:
            logger.warning(f"Unhandled frontend webhook event type: {event_type}")
            return {"status": "error", "message": "Unsupported event type"}

    except HTTPException as he:
        # Log the full exception for debugging
        logger.error(f"HTTP Exception in frontend webhook handler: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in frontend webhook handler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_account_analysis(user_id: str, account_id: str):
    """Process account analysis in the background."""
    try:
        logger.info(f"Starting account analysis for user {user_id}, account {account_id}")
        
        # Get account data
        account = await analysis_repo.get_account_by_id(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return
        
        # Run the analysis
        analysis_result = await account_analyzer.analyze_account(
            account_id=account_id,
            new_fetch=True,
            account_data=account.get('account_details'),
            user_id=user_id
        )
        
        logger.info(f"Account analysis completed for user {user_id}, account {account_id}")
        
        # Update user's account analysis status if needed
        user = await user_db.get_user(user_id)
        if user:
            # You could update a status field or send a notification here
            pass
            
    except Exception as e:
        logger.error(f"Error processing account analysis: {str(e)}", exc_info=True)
