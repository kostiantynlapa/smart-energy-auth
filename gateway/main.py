"""
API Gateway for Smart Energy Project.

Features:
- JWT token validation
- RBAC enforcement based on allowed_storages claim
- Route requests to appropriate database services
- Mock responses for MVP
"""
from datetime import timezone
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")

# Initialize FastAPI app
app = FastAPI(
    title="Smart Energy API Gateway",
    description="Gateway for routing requests to data storage services with JWT/RBAC",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Data query request schema."""
    db_type: str = Field(..., description="Database type: 'postgres', 'mongodb', etc.")
    query: str = Field(default="", description="Query string or filter")


class QueryResponse(BaseModel):
    """Mock query response schema."""
    result: str
    source: str
    message: str | None = None


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # username
    role: str = "user"  # "user" or "admin"
    allowed_storages: list[str] = Field(default_factory=list)
    exp: int


def extract_token(authorization: str | None) -> str:
    """
    Extract JWT token from Authorization header.
    
    Accepts both formats:
    - "Bearer <token>"
    - "<token>" (without Bearer prefix)
    
    Args:
        authorization: Authorization header value
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: 401 if header is missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    authorization = authorization.strip()
    
    # Check if it has "Bearer" prefix
    if authorization.lower().startswith("bearer "):
        # Remove "Bearer " prefix and return token
        return authorization[7:].strip()
    else:
        # Return the token as-is (without Bearer prefix)
        return authorization


def validate_token(token: str) -> TokenPayload:
    """
    Validate and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload with decoded claims
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Create TokenPayload to validate structure
        token_payload = TokenPayload(
            sub=payload.get("sub"),
            allowed_storages=payload.get("allowed_storages", []),
            exp=payload.get("exp")
        )
        
        return token_payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def check_storage_access(token_payload: TokenPayload, db_type: str) -> None:
    """
    Check if user has access to the requested storage.
    
    Args:
        token_payload: Decoded JWT token payload
        db_type: Requested database type
        
    Raises:
        HTTPException: 403 if storage is not in allowed_storages
    """
    if db_type not in token_payload.allowed_storages:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to storage: {db_type}"
        )


@app.post("/query", response_model=QueryResponse)
async def query(
    request_body: QueryRequest,
    authorization: str | None = Header(None)
):
    """
    Route query request to appropriate database service after JWT/RBAC validation.
    
    Requires:
    - Authorization: Bearer <JWT> header with valid token
    - Token must include requested db_type in allowed_storages claim
    
    Returns mock response for MVP.
    
    Raises:
        HTTPException: 401 for invalid/expired token
        HTTPException: 403 if user not allowed to access db_type
    """
    # Extract JWT token from header
    token = extract_token(authorization)
    
    # Validate token
    token_payload = validate_token(token)
    
    # Check RBAC: verify db_type is in allowed_storages
    check_storage_access(token_payload, request_body.db_type)
    
    # Token is valid and user has access to the storage
    # Return mock response (would route to actual service in production)
    return QueryResponse(
        result="mock data from " + request_body.db_type,
        source=request_body.db_type,
        message=f"Query executed on {request_body.db_type} for user {token_payload.sub}"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """Root endpoint with gateway information."""
    return {
        "name": "Smart Energy API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "query": "POST /query - Execute query with JWT authorization"
        }
    }
