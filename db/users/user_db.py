from datetime import datetime
import json
from typing import Optional, Dict, Any, List
from db.migrations import get_async_session
from db.schemas import User, UserTrackedItem
from sqlalchemy import select
from config import config
import stripe
import logging

logger = logging.getLogger(__name__)

class UserDataRepository():
    async def create_user(self, user_id: str, email: str, stripe_customer_id: Optional[str] = None, name: Optional[str] = None,
                   current_tier: Optional[str] = None, fe_metadata: Optional[Dict] = None) -> None:
        try:
            now = int(datetime.now().timestamp())
            async with get_async_session() as session:
                new_user = User(
                    id=user_id,
                    email=email,
                    name=name,
                    stripe_customer_id=stripe_customer_id,
                    current_tier=current_tier or 'tier0',
                    fe_metadata=fe_metadata,
                    created_at=now,
                    updated_at=now
                )
                session.add(new_user)
                await session.commit()
            logger.info(f"Created user {user_id}")
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {str(e)}")
            raise

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with get_async_session() as session:
            result = await session.execute(
                select(User).filter(User.id == user_id)
            )
            user = result.scalars().first()
            
            if user:
                # Get tracked items
                tracked_items = await self.get_tracked_items(user.id)
                
                return {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'current_tier': user.current_tier,
                    'stripe_customer_id': user.stripe_customer_id,
                    'current_period_start': user.current_period_start,
                    'current_period_end': user.current_period_end,
                    'fe_metadata': user.fe_metadata,
                    'tracked_items': tracked_items,
                    
                }
            return None

    async def update_user(self, user_id: str, **updates: Any) -> bool:
        """Update user fields"""
        try:
            valid_fields = {'email', 'name', 'current_tier', 
                          'current_period_start', 'current_period_end', 'fe_metadata'}
            
            async with get_async_session() as session:
                result = await session.execute(
                    select(User).filter(User.id == user_id)
                )
                user = result.scalars().first()
                
                if not user:
                    return False
                    
                for field, value in updates.items():
                    if field in valid_fields:
                        setattr(user, field, value)
                
                await session.commit()
                logger.info(f"Updated user {user_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise

    async def delete_user(self, user_id: str) -> bool:
        
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(User).filter(User.id == user_id)
                )
                user = result.scalars().first()
                if user:
                    await session.delete(user)
                    await session.commit()
                    logger.info(f"Deleted user {user_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise

    async def add_tracked_item(self, user_id: str, tracked_type: str, tracked_id: str, tracked_account_name: Optional[str] = None) -> bool:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(UserTrackedItem).filter(
                        UserTrackedItem.user_id == user_id,
                        UserTrackedItem.tracked_type == tracked_type,
                        UserTrackedItem.tracked_id == tracked_id
                    )
                )
                existing_item = result.scalars().first()
                
                if existing_item:
                    logger.info(f"Tracked {tracked_type} {tracked_id} already exists for user {user_id}")
                    return True
                    
                now = int(datetime.now().timestamp())
                tracked_item = UserTrackedItem(
                    user_id=user_id,
                    tracked_type=tracked_type,
                    tracked_id=tracked_id,
                    tracked_account_name=tracked_account_name,
                    captured_at=now
                )
                session.add(tracked_item)
                await session.commit()
                
            logger.info(f"Added tracked {tracked_type} {tracked_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding tracked item for user {user_id}: {str(e)}")
            raise

    async def remove_tracked_item(self, user_id: str, tracked_type: str, tracked_id: str) -> bool:
        """Remove a tracked item for a user"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(UserTrackedItem).filter(
                        UserTrackedItem.user_id == user_id,
                        UserTrackedItem.tracked_type == tracked_type,
                        UserTrackedItem.tracked_id == tracked_id
                    )
                )
                tracked_item = result.scalars().first()
                if tracked_item:
                    await session.delete(tracked_item)
                    await session.commit()
            logger.info(f"Removed tracked {tracked_type} {tracked_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing tracked item for user {user_id}: {str(e)}")
            raise

    async def get_tracked_items(self, user_id: str) -> Dict[str, List[str]]:
        """Get all tracked items for a user"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(UserTrackedItem).filter(
                        UserTrackedItem.user_id == user_id,
                        UserTrackedItem.tracked_type.in_(['tweet', 'account', 'analysis', 'community_analysis'])
                    )
                )
                tracked_items = result.scalars().all()
                if not tracked_items:
                    return {'tweets': [], 'accounts': [], 'analysis': [], 'community_analysis': []}
                items = {'tweets': [], 'accounts': [], 'analysis': [], 'community_analysis': []}
                for item in tracked_items:
                    if item.tracked_type == 'tweet':
                        items['tweets'].append(item.tracked_id)
                    elif item.tracked_type == 'account':
                        items['accounts'].append(item.tracked_id)
                    elif item.tracked_type == 'analysis':
                        items['analysis'].append(item.tracked_id)
                    elif item.tracked_type == 'community_analysis':
                        items['community_analysis'].append(item.tracked_id)
                return items
                
        except Exception as e:
            logger.error(f"Error getting tracked items for user {user_id}: {str(e)}")
            raise
   

    async def is_tweet_tracked(self, tweet_id: str) -> bool:
        """Check if a tweet is being tracked by any user"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(UserTrackedItem).filter(
                        UserTrackedItem.tracked_type == 'tweet',
                        UserTrackedItem.tracked_id == tweet_id
                    )
                )
                tracked_item = result.scalars().first()
                return tracked_item is not None
        except Exception as e:
            logger.error(f"Error checking if tweet {tweet_id} is tracked: {str(e)}")
            raise


    async def get_user_by_stripe_customer(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Stripe customer ID"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(User).filter(User.stripe_customer_id == stripe_customer_id)
                )
                user = result.scalars().first()
                
                if user:
                    # Get tracked items
                    tracked_items = await self.get_tracked_items(user.id)
                    
                    return {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'current_tier': user.current_tier,
                        'current_period_start': user.current_period_start,
                        'current_period_end': user.current_period_end,
                        'fe_metadata': user.fe_metadata,
                        'tracked_items': tracked_items
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user by Stripe customer ID {stripe_customer_id}: {str(e)}")
            raise


    async def update_user_subscription(self, user_id: str, subscription_data: Dict[str, Any]) -> bool:
        """Update user's subscription details from Stripe data"""
        try:
            tier = subscription_data.get('tier', 'tier0')
            period_start = subscription_data.get('current_period_start')
            period_end = subscription_data.get('current_period_end')
            
            updates = {
                'current_tier': tier,
                'updated_at': int(datetime.now().timestamp())
            }
            
            if period_start:
                updates['current_period_start'] = period_start
            if period_end:
                updates['current_period_end'] = period_end
                
            logger.info(f"Updating subscription for user {user_id} to tier {tier}")
            return await self.update_user(user_id, **updates)
        except Exception as e:
            logger.error(f"Error updating subscription for user {user_id}: {str(e)}")
            raise



    async def handle_subscription_cancellation(self, user_id: str) -> bool:
        """Reset user to free tier when subscription is cancelled"""
        try:
            updates = {
                'current_tier': 'tier0',
                'current_period_start': None,
                'current_period_end': None,
                'updated_at': int(datetime.now().timestamp())
            }
            
            logger.info(f"Cancelling subscription for user {user_id}")
            return await self.update_user(user_id, **updates)
        except Exception as e:
            logger.error(f"Error cancelling subscription for user {user_id}: {str(e)}")
            raise



    async def process_payment_failure(self, user_id: str, payment_data: Dict[str, Any]) -> bool:
        """Handle failed payment scenarios"""
        try:
            # Log the payment failure
            failure_message = payment_data.get('failure_message', 'Unknown error')
            failure_code = payment_data.get('failure_code', 'unknown')
            
            logger.error(f"Payment failure for user {user_id}: {failure_code} - {failure_message}")
            
            # You might want to update user metadata or status here
            # For now, we're just logging the failure
            
            return True
        except Exception as e:
            logger.error(f"Error processing payment failure for user {user_id}: {str(e)}")
            raise



    async def handle_subscription_update(self, user_id: str, subscription_data: Dict[str, Any]) -> bool:
        """Process subscription changes (upgrades/downgrades)"""
        try:
            # Extract relevant subscription data
            tier = subscription_data.get('tier', 'tier0')
            period_start = subscription_data.get('current_period_start')
            period_end = subscription_data.get('current_period_end')
            
            updates = {
                'current_tier': tier,
                'updated_at': int(datetime.now().timestamp())
            }
            
            if period_start:
                updates['current_period_start'] = period_start
            if period_end:
                updates['current_period_end'] = period_end
                
            logger.info(f"Updating subscription for user {user_id} to tier {tier}")
            return await self.update_user(user_id, **updates)
        except Exception as e:
            logger.error(f"Error updating subscription for user {user_id}: {str(e)}")
            raise

    async def create_checkout_session(self, user_id: str) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(User).filter(User.id == user_id)
                )
                user = result.scalars().first()
                
                if not user:
                    raise ValueError(f"User {user_id} not found")

                # Create Stripe checkout session
                stripe_session = stripe.checkout.Session.create(
                    success_url='https://app.postrack.ai',
                    mode='subscription',
                    line_items=[{
                        'price': config.TIER1_PRICE_ID,
                        'quantity': 1
                    }],
                    customer=user.stripe_customer_id,
                    subscription_data={
                        'trial_period_days': 7
                    }
                )

                logger.info(f"Created checkout session for user {user_id}")
                return {
                    'session_id': stripe_session.id,
                    'url': stripe_session.url
                }

        except Exception as e:
            logger.error(f"Error creating checkout session for user {user_id}: {str(e)}")
            raise

