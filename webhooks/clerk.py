from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import os
import logging
from dotenv import load_dotenv
from svix.webhooks import Webhook
from pydantic import BaseModel
from db.users.user_db import UserDataRepository
from config import config
import stripe

load_dotenv()

logger = logging.getLogger(__name__)



class ClerkWebhook(BaseModel):
    type: str
    data: dict

def verify_webhook(request: Request, body: bytes):
    logger.info("Verifying webhook signature")
    # Get required headers
    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp") 
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        logger.error("Missing required webhook headers")
        raise HTTPException(status_code=400, detail="Missing headers")

    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature
    }

    try:
        wh = Webhook(config.CLERK_WEBHOOK_SECRET)
        # Verify will throw an error if invalid
        wh.verify(body.decode(), headers)
        logger.info("Webhook signature verified successfully")
    except Exception as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid signature")

router = APIRouter()

@router.post("/clerk-webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        logger.info("Received webhook request")
        body = await request.body()
        
        verify_webhook(request, body)
        
        # Parse payload
        payload = await request.json()
        event_type = payload.get("type")
        user_data = payload.get("data", {})
        
        logger.info(f"Processing webhook event type: {event_type}")
        
        # Process in background if needed
        background_tasks.add_task(handle_event, event_type, user_data)
        
        return {"message": "Webhook received"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_event(event_type: str, user_data: dict):
    logger.info(f"Handling {event_type} event")
    user_repo = UserDataRepository()

    try:
        if event_type == "user.created":
            logger.info("Processing user creation")
            # Extract user information
            user_id = user_data.get("id")
            email = user_data.get("email_addresses", [{}])[0].get("email_address")
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            fe_metadata = {
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name")
            }
            stripe_customer_id = None
            
            # Create Stripe customer
            try:
                logger.info(f"Creating Stripe customer for user {user_id}")
                stripe_customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata={
                        "clerk_user_id": user_id
                    }
                )
                
                stripe_customer_id = stripe_customer.id
                logger.info(f"Created Stripe customer {stripe_customer.id} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create Stripe customer for user {user_id}: {str(e)}")
                # Continue with user creation even if Stripe customer creation fails
            
            logger.info(f"Creating user record for {user_id}")
            await user_repo.create_user(
                user_id=user_id,
                email=email,
                name=name,
                stripe_customer_id=stripe_customer_id,
                fe_metadata=fe_metadata
            )

        elif event_type == "user.updated":
            logger.info("Processing user update")
            user_id = user_data.get("id")
            updates = {}
            
            email = user_data.get("email_addresses", [{}])[0].get("email_address")
            if email:
                updates["email"] = email
                
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            if name:
                updates["name"] = name
                
            fe_metadata = {
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name")
            }
            updates["fe_metadata"] = fe_metadata

            logger.info(f"Updating user {user_id} with: {updates}")
            await user_repo.update_user(user_id, **updates)

        elif event_type == "user.deleted":
            user_id = user_data.get("id")
            logger.info(f"Processing deletion for user {user_id}")
            await user_repo.delete_user(user_id)
            logger.info(f"Deleted user {user_id}")

    except Exception as e:
        logger.error(f"Error handling {event_type} event: {str(e)}")
        raise
