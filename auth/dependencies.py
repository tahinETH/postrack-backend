# auth/dependencies.py
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import authenticate_request, AuthenticateRequestOptions
import os

class ClerkAuthMiddleware(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.clerk = Clerk(bearer_auth=os.getenv('CLERK_SECRET_KEY'))

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        try:
            request_state = self.clerk.authenticate_request(
                request,
                AuthenticateRequestOptions(
                    authorized_parties=['your-domain.com']  # Replace with your domain
                )
            )
            
            if not request_state.is_signed_in:
                raise HTTPException(status_code=401, detail=request_state.reason)
                
            # Add user info to request state
            request.state.user_id = request_state.payload.get('sub')
            request.state.session = request_state.payload
            
            return request_state.payload.get('sub')  # Returns user_id
            
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

# Create instance to use as dependency
auth_middleware = ClerkAuthMiddleware()