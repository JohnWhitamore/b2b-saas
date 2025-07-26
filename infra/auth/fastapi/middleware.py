from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# ... swap this with Auth0's verification if needed
import jwt

class TokenMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        try:
            
            # ... replace with actual key and encryption method
            payload = jwt.decode(token, "your-secret", algorithms=["HS256"])
            request.state.scopes = payload.get("scopes", [])
            
        except jwt.InvalidTokenError:
            
            request.state.scopes = []
            
        return await call_next(request)