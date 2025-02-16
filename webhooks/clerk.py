from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import os
import sqlite3
import logging
from dotenv import load_dotenv
from svix.webhooks import Webhook
from pydantic import BaseModel
from db.users.user_db import UserDataRepository

load_dotenv()

logger = logging.getLogger(__name__)

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")
DB_PATH = os.getenv("DB_PATH")


class ClerkWebhook(BaseModel):
    type: str
    data: dict

def verify_webhook(request: Request, body: bytes):
    # Get required headers
    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp") 
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=400, detail="Missing headers")

    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature
    }

    try:
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        # Verify will throw an error if invalid
        wh.verify(body.decode(), headers)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid signature")

router = APIRouter()

@router.post("/clerk-webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.body()
        
        # Verify signature first
        verify_webhook(request, body)
        
        # Parse payload
        payload = await request.json()
        event_type = payload.get("type")
        user_data = payload.get("data", {})

        # Process in background if needed
        background_tasks.add_task(handle_event, event_type, user_data)
        
        return {"message": "Webhook received"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def handle_event(event_type: str, user_data: dict):
    conn = sqlite3.connect(DB_PATH)
    user_repo = UserDataRepository(conn)

    try:
        if event_type == "user.created":
            # Extract user information
            user_id = user_data.get("id")
            email = user_data.get("email_addresses", [{}])[0].get("email_address")
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            fe_metadata = {
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name")
            }

            user_repo.create_user(
                user_id=user_id,
                email=email,
                name=name,
                fe_metadata=fe_metadata
            )

        elif event_type == "user.updated":
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

            user_repo.update_user(user_id, **updates)

    except Exception as e:
        logger.error(f"Error handling {event_type} event: {str(e)}")
        raise
    finally:
        conn.close()
