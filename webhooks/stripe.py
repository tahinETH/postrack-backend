from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import stripe
import logging
from typing import Dict, Any
from config import config

logger = logging.getLogger(__name__)

stripe.api_key = config.STRIPE_SECRET_KEY
endpoint_secret = config.STRIPE_WEBHOOK_SECRET

router = APIRouter()

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
            secret=endpoint_secret
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
        
        # Add event ID to logs for tracking
        logger.info(f"Processing webhook event: {event.id}")
        
        # Process event in background
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
        "checkout.session": handle_checkout_session_event
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
            pass
        elif event_type == "customer.updated":
            # Handle customer update
            logger.info(f"Customer updated: {customer_id}")
            pass
        elif event_type == "customer.deleted":
            # Handle customer deletion
            logger.info(f"Customer deleted: {customer_id}")
            pass
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
            pass
        elif event_type == "invoice.payment_failed":
            logger.error(f"Invoice {invoice_id} payment failed for customer {customer_id}")
            pass
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
            pass
        elif event_type == "payment_intent.payment_failed":
            error = data.get("last_payment_error", {}).get("message", "Unknown error")
            logger.error(f"Payment {payment_intent_id} failed: {error}")
            pass
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
            pass
        elif event_type == "charge.failed":
            failure_code = data.get("failure_code")
            failure_message = data.get("failure_message")
            logger.error(f"Charge {charge_id} failed: Code={failure_code}, Message={failure_message}")
            pass
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
            pass
        elif event_type == "checkout.session.expired":
            logger.warning(f"Checkout {session_id} expired for customer {customer_id}")
            pass
        else:
            logger.warning(f"Unhandled checkout session event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing checkout session event {event_type}: {str(e)}", exc_info=True)
        raise
