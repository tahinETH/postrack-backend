from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import stripe
import logging
from typing import Dict, Any
from config import config
from db.users.user_db import UserDataRepository

logger = logging.getLogger(__name__)

stripe.api_key = config.STRIPE_SECRET_KEY
raw_secret_from_config = config.STRIPE_WEBHOOK_SECRET
cleaned_secret = str(raw_secret_from_config).strip()
endpoint_secret = cleaned_secret 


router = APIRouter()
user_db = UserDataRepository()

def verify_stripe_webhook(request: Request, body: bytes) -> Dict[str, Any]:
    """Verify and construct Stripe webhook event with better error handling."""
    stripe_signature = request.headers.get("stripe-signature")

    if not stripe_signature:
        logger.error("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature, 
            secret=f"{endpoint_secret}"
        )
        return event
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid signature: {str(e)}")

@router.post("/stripe-webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming Stripe webhooks with improved logging and error handling."""
    try:
        # Log incoming webhook request
        logger.info(f"Received webhook from {request.client.host}")
        
        body = await request.body()
        
        event = verify_stripe_webhook(request, body)
        
        logger.info(f"Processing webhook event: {event.id}")
        
        background_tasks.add_task(handle_event, event)
        
        return {"status": "success", "event_id": event.id}

    except HTTPException as he:
        # Log the full exception for debugging
        logger.error(f"HTTP Exception in webhook handler: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_event(event: Dict[str, Any]):
    """Process Stripe events with improved error handling and logging."""
    event_type = event["type"]
    event_id = event["id"]
    data = event["data"]["object"]
    
    logger.info(f"Processing Stripe event: {event_type} (ID: {event_id})")

    # Map event types to their handlers
    event_handlers = {
        "customer": handle_customer_event,
        "invoice": handle_invoice_event,
        "payment_intent": handle_payment_intent_event,
        "charge": handle_charge_event,
        "checkout.session": handle_checkout_session_event,
        "subscription": handle_subscription_event
    }

    try:
        # Get the appropriate handler based on event type prefix
        handler = next(
            (handler for prefix, handler in event_handlers.items() 
             if event_type.startswith(prefix)),
            None
        )

        if handler:
            await handler(event_type, data)
        else:
            logger.warning(f"Unhandled event type: {event_type} (ID: {event_id})")

    except Exception as e:
        logger.error(
            f"Error handling {event_type} event (ID: {event_id}): {str(e)}", 
            exc_info=True
        )
        raise

async def handle_customer_event(event_type: str, data: Dict[str, Any]):
    """Handle customer related events with proper logging and error handling."""
    try:
        customer_id = data.get("id")
        if not customer_id:
            raise ValueError("Customer ID missing from event data")
            
        logger.info(f"Processing customer event {event_type} for customer {customer_id}")

        if event_type == "customer.created":
            # Handle customer creation
            logger.info(f"New customer created: {customer_id}")
            # No need to create user here as it's handled during signup
        elif event_type == "customer.updated":
            # Handle customer update
            logger.info(f"Customer updated: {customer_id}")
            # Get user by stripe customer ID and update if needed
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user:
                # Update user details if needed
                pass
        elif event_type == "customer.deleted":
            # Handle customer deletion
            logger.info(f"Customer deleted: {customer_id}")
            # Consider handling user account cleanup
        else:
            logger.warning(f"Unhandled customer event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing customer event {event_type}: {str(e)}", exc_info=True)
        raise

async def handle_invoice_event(event_type: str, data: Dict[str, Any]):
    """Handle invoice related events with proper logging and error handling."""
    try:
        invoice_id = data.get("id")
        if not invoice_id:
            raise ValueError("Invoice ID missing from event data")
            
        customer_id = data.get("customer")
        amount = data.get("amount_paid")
        
        logger.info(f"Processing invoice event {event_type} for invoice {invoice_id}")

        if event_type == "invoice.paid":
            logger.info(f"Invoice {invoice_id} paid: Amount={amount}, Customer={customer_id}")
            # Get user by stripe customer ID
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user:

                subscription_data = {
                    'tier': 'tier1', 
                    'current_period_start': data.get('period_start'),
                    'current_period_end': data.get('period_end')
                }

                await user_db.update_user_subscription(user['id'], subscription_data)

        elif event_type == "invoice.payment_failed":
            logger.error(f"Invoice {invoice_id} payment failed for customer {customer_id}")
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user:
                payment_data = {
                    'failure_message': data.get('failure_message'),
                    'failure_code': data.get('failure_code')
                }
                await user_db.process_payment_failure(user['id'], payment_data)
        else:
            logger.warning(f"Unhandled invoice event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing invoice event {event_type}: {str(e)}", exc_info=True)
        raise

async def handle_payment_intent_event(event_type: str, data: Dict[str, Any]):
    """Handle payment intent related events with proper logging and error handling."""
    try:
        payment_intent_id = data.get("id")
        if not payment_intent_id:
            raise ValueError("Payment Intent ID missing from event data")
            
        amount = data.get("amount")
        customer_id = data.get("customer")
        
        logger.info(f"Processing payment intent event {event_type} for payment {payment_intent_id}")

        if event_type == "payment_intent.succeeded":
            logger.info(f"Payment {payment_intent_id} succeeded: Amount={amount}, Customer={customer_id}")
            # Payment success is usually handled via invoice.paid
        elif event_type == "payment_intent.payment_failed":
            error = data.get("last_payment_error", {}).get("message", "Unknown error")
            logger.error(f"Payment {payment_intent_id} failed: {error}")
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user:
                payment_data = {
                    'failure_message': error,
                    'failure_code': data.get("last_payment_error", {}).get("code", "unknown")
                }
                await user_db.process_payment_failure(user['id'], payment_data)
        else:
            logger.warning(f"Unhandled payment intent event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing payment intent event {event_type}: {str(e)}", exc_info=True)
        raise

async def handle_charge_event(event_type: str, data: Dict[str, Any]):
    """Handle charge related events with proper logging and error handling."""
    try:
        charge_id = data.get("id")
        if not charge_id:
            raise ValueError("Charge ID missing from event data")
            
        amount = data.get("amount")
        customer_id = data.get("customer")
        
        logger.info(f"Processing charge event {event_type} for charge {charge_id}")

        if event_type == "charge.succeeded":
            logger.info(f"Charge {charge_id} succeeded: Amount={amount}, Customer={customer_id}")
            # Successful charges are usually handled via invoice.paid
        elif event_type == "charge.failed":
            failure_code = data.get("failure_code")
            failure_message = data.get("failure_message")
            logger.error(f"Charge {charge_id} failed: Code={failure_code}, Message={failure_message}")
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user:
                payment_data = {
                    'failure_message': failure_message,
                    'failure_code': failure_code
                }
                await user_db.process_payment_failure(user['id'], payment_data)
        else:
            logger.warning(f"Unhandled charge event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing charge event {event_type}: {str(e)}", exc_info=True)
        raise

async def handle_checkout_session_event(event_type: str, data: Dict[str, Any]):
    """Handle checkout session related events with proper logging and error handling."""
    try:
        session_id = data.get("id")
        if not session_id:
            raise ValueError("Checkout Session ID missing from event data")
            
        customer_id = data.get("customer")
        payment_status = data.get("payment_status")
        
        logger.info(f"Processing checkout session event {event_type} for session {session_id}")

        if event_type == "checkout.session.completed":
            logger.info(f"Checkout {session_id} completed: Customer={customer_id}, Status={payment_status}")
            # Get user by stripe customer ID
            user = await user_db.get_user_by_stripe_customer(customer_id)
            if user and payment_status == "paid":
                # Update subscription details based on the checkout session
                subscription_data = {
                    'tier': 'tier1',  # Determine tier from checkout session
                    'current_period_start': int(data.get('created', 0)),
                    'current_period_end': None  # This would come from the subscription object
                }
                await user_db.update_user_subscription(user['id'], subscription_data)
        elif event_type == "checkout.session.expired":
            logger.warning(f"Checkout {session_id} expired for customer {customer_id}")
            # No action needed for expired checkout sessions
        else:
            logger.warning(f"Unhandled checkout session event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing checkout session event {event_type}: {str(e)}", exc_info=True)
        raise

async def handle_subscription_event(event_type: str, data: Dict[str, Any]):
    """Handle subscription related events with proper logging and error handling."""
    try:
        subscription_id = data.get("id")
        if not subscription_id:
            raise ValueError("Subscription ID missing from event data")
            
        customer_id = data.get("customer")
        status = data.get("status")
        
        logger.info(f"Processing subscription event {event_type} for subscription {subscription_id}")

        # Get user by stripe customer ID
        user = await user_db.get_user_by_stripe_customer(customer_id)
        if not user:
            logger.warning(f"User not found for customer {customer_id}")
            return

        if event_type == "subscription.created":
            logger.info(f"Subscription {subscription_id} created: Customer={customer_id}, Status={status}")
            # Handle new subscription
            subscription_data = {
                'tier': 'tier1',  # Determine tier from subscription plan
                'current_period_start': data.get('current_period_start'),
                'current_period_end': data.get('current_period_end')
            }
            await user_db.update_user_subscription(user['id'], subscription_data)
            
        elif event_type == "subscription.updated":
            logger.info(f"Subscription {subscription_id} updated: Customer={customer_id}, Status={status}")
            # Handle subscription update
            subscription_data = {
                'tier': 'tier1',  # Determine tier from subscription plan
                'current_period_start': data.get('current_period_start'),
                'current_period_end': data.get('current_period_end')
            }
            await user_db.handle_subscription_update(user['id'], subscription_data)
            
        elif event_type == "subscription.deleted" or event_type == "subscription.canceled":
            logger.info(f"Subscription {subscription_id} ended: Customer={customer_id}")
            # Handle subscription cancellation
            await user_db.handle_subscription_cancellation(user['id'])
            
        else:
            logger.warning(f"Unhandled subscription event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing subscription event {event_type}: {str(e)}", exc_info=True)
        raise
