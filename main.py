import logging
import os
from fastapi import FastAPI
import asyncio
import uvicorn
from db.migrations import connect_and_migrate
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config import config
import tracemalloc

from webhooks.clerk import router as clerk_router
from webhooks.stripe import router as stripe_router
from webhooks.fe_ws import router as fe_ws_router
from routers.user_router import router as user_router
from routers.account_router import router as account_router
from routers.tweet_router import router as tweet_router
from routers.workshop_router import router as workshop_router
from routers.stripe_router import router as stripe_payment_router

from db.service import Service

tracemalloc.start()
load_dotenv()

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

# Include routers
app.include_router(clerk_router)
app.include_router(stripe_router)
app.include_router(fe_ws_router)
app.include_router(user_router)
app.include_router(account_router)
app.include_router(tweet_router)
app.include_router(workshop_router)
app.include_router(stripe_payment_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = Service()

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
        asyncio.create_task(service.handle_periodic_checks())

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)