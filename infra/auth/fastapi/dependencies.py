from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Callable
import requests
import json

# Auth0 and API configuration

# ... replace with the actual tenant
AUTH0_DOMAIN = "your-tenant.eu.auth0.com"

# ... this needs to match the "aud" value
API_IDENTIFIER = "https://clientco/api"

# ... this should be fine
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

# Bearer token parser
security = HTTPBearer()

# Load JWKS once (could be memoized or refreshed in production)
jwks = requests.get(JWKS_URL).json()

def get_public_key(token: str):
    
    unverified_header = jwt.get_unverified_header(token)
    
    for key in jwks['keys']:
        
        if key['kid'] == unverified_header['kid']:
            
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        
    raise Exception("Public key not found")

def verify_token_and_scope(token: str) -> dict:
    
    try:
        
        public_key = get_public_key(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=API_IDENTIFIER,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
    
    except jwt.JWTError as e:
        
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")

def require_scope(required_scope: str) -> Callable:
    
    def verifier(credentials: HTTPAuthorizationCredentials = Depends(security)):
        
        claims = verify_token_and_scope(credentials.credentials)
        scopes = claims.get("scope", "").split()
        
        if required_scope not in scopes:
            
            raise HTTPException(status_code=403, detail="Insufficient scope")
            
        return claims
    
    return verifier

# Demo route for protected access
app = FastAPI()

@app.get("/protected-read", dependencies=[Depends(require_scope("read:data"))])
async def protected_read():
    
    return {"message": "Read access granted"}