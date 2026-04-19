"""
JWT (JSON Web Token) creation and verification utilities.
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from ..models import TokenPayload


def create_access_token(
    username: str,
    allowed_storages: list[str],
    secret_key: str,
    expires_minutes: int,
    role: str = "user"
) -> tuple[str, int]:
    """
    Create a JWT access token.
    
    Args:
        username: User's username (will be used as 'sub' claim)
        allowed_storages: List of storage systems user can access
        secret_key: Secret key for signing token
        expires_minutes: Token expiration time in minutes
        role: User role ("user" or "admin")
        
    Returns:
        Tuple of (token_string, expires_in_seconds)
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)
    
    payload = {
        "sub": username,
        "role": role,
        "allowed_storages": allowed_storages,
        "exp": expires_at,
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    expires_in_seconds = int(expires_minutes * 60)
    
    return token, expires_in_seconds


def decode_token(token: str, secret_key: str) -> dict | None:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        secret_key: Secret key used to sign the token
        
    Returns:
        Token payload dict if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
