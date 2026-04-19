"""
FastAPI Authentication Microservice for Smart Energy Project.

Features:
- User registration with TOTP (2FA) setup
- User login with password + TOTP verification → JWT
- In-memory user storage
- Admin interface for user management
"""
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from .config import settings
from .models import (
    RegisterRequest, RegisterResponse, LoginRequest, TokenResponse,
    TokenPayload, AdminUserCreate, AdminStorageUpdate,
    AdminUserList
)
from .users_db import (
    user_exists, create_user, get_user, get_all_users, delete_user,
    update_user_storages, update_user_role, seed_admin_user
)
from .utils.password import hash_password, verify_password
from .utils.totp import generate_secret, get_qr_uri, generate_qr_code_base64, verify_totp
from .utils.jwt import create_access_token, decode_token

# Initialize FastAPI app
app = FastAPI(
    title="Smart Energy Auth Service",
    description="Authentication microservice for Smart Energy data storage management",
    version="1.0.0"
)

# Add CORS middleware (allow all origins for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Admin dependency
async def get_admin_user(authorization: str | None = Header(None)) -> TokenPayload:
    """
    Dependency to check admin access.
    
    Extracts JWT from Authorization header and verifies admin role.
    
    Raises:
        HTTPException: 401 if token invalid, 403 if not admin
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = parts[1]
    
    try:
        payload = decode_token(token, settings.SECRET_KEY)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Check if user has admin role
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/register", response_class=FileResponse)
async def get_register():
    """
    Serve the registration HTML page.
    """
    register_html = Path(__file__).parent.parent / "auth_ui" / "index.html"
    if not register_html.exists():
        raise HTTPException(status_code=404, detail="Registration page not found")
    return register_html


@app.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """
    Register a new user and setup TOTP-based 2FA.
    
    Returns a QR code (base64 PNG) for Google Authenticator and the raw secret.
    
    Raises:
        HTTPException: 400 if username already exists
    """
    # Check if username already exists
    if user_exists(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    hashed_password = hash_password(request.password)
    
    # Generate TOTP secret
    totp_secret = generate_secret()
    
    # Generate provisioning URI and QR code
    provisioning_uri = get_qr_uri(
        secret=totp_secret,
        username=request.username,
        issuer_name="SmartEnergy"
    )
    qr_code_base64 = generate_qr_code_base64(provisioning_uri)
    
    # Save user to storage
    create_user(
        username=request.username,
        hashed_password=hashed_password,
        totp_secret=totp_secret,
        allowed_storages=request.allowed_storages or []
    )
    
    return RegisterResponse(
        qr_code_base64=qr_code_base64,
        totp_secret=totp_secret
    )


@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with password and TOTP code, return JWT token.
    
    The JWT contains user claims and allowed storage systems for RBAC.
    
    Raises:
        HTTPException: 401 for invalid credentials (generic message for security)
    """
    print(f"[LOGIN] Attempting login for user: {request.username}")
    
    # Find user
    user = get_user(request.username)
    if user is None:
        print(f"[LOGIN] User {request.username} not found")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"[LOGIN] User found. Verifying password...")
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        print(f"[LOGIN] Password verification failed for {request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"[LOGIN] Password verified. Verifying TOTP code: {request.totp_code}")
    print(f"[LOGIN] User TOTP secret: {user.totp_secret}")
    # Verify TOTP code with ±30s clock drift tolerance
    if not verify_totp(user.totp_secret, request.totp_code, valid_window=1):
        print(f"[LOGIN] TOTP verification failed for {request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"[LOGIN] TOTP verified successfully!")
    # Create JWT token
    token, expires_in = create_access_token(
        username=request.username,
        allowed_storages=user.allowed_storages,
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        role=user.role
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in
    )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================


@app.get("/admin/users", response_model=list[AdminUserList])
async def admin_list_users(admin: TokenPayload = Depends(get_admin_user)):
    """
    List all users with their roles and allowed storages.
    
    Requires admin role.
    """
    all_users = get_all_users()
    return [
        AdminUserList(
            username=user.username,
            role=user.role,
            allowed_storages=user.allowed_storages
        )
        for user in all_users.values()
    ]


@app.post("/admin/users", response_model=dict)
async def admin_create_user(
    request: AdminUserCreate,
    admin: TokenPayload = Depends(get_admin_user)
):
    """
    Create a new user (admin only).
    
    Requires admin role.
    """
    # Check if username already exists
    if user_exists(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    hashed_password = hash_password(request.password)
    
    # Generate TOTP secret
    totp_secret = generate_secret()
    
    # Create user with role
    create_user(
        username=request.username,
        hashed_password=hashed_password,
        totp_secret=totp_secret,
        allowed_storages=request.allowed_storages or [],
        role=request.role
    )
    
    return {
        "message": "User created successfully",
        "username": request.username,
        "role": request.role
    }


@app.patch("/admin/users/{username}/storages")
async def admin_update_storages(
    username: str,
    request: AdminStorageUpdate,
    admin: TokenPayload = Depends(get_admin_user)
):
    """
    Update allowed storages for a user (admin only).
    
    Requires admin role.
    """
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_user_storages(username, request.allowed_storages)
    
    return {
        "message": "Storages updated successfully",
        "username": username,
        "allowed_storages": request.allowed_storages
    }


@app.patch("/admin/users/{username}/role")
async def admin_update_role(
    username: str,
    request: dict,  # {"role": "admin" or "user"}
    admin: TokenPayload = Depends(get_admin_user)
):
    """
    Update user role (admin only).
    
    Requires admin role.
    """
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = request.get("role", "user")
    if role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'")
    
    update_user_role(username, role)
    
    return {
        "message": "Role updated successfully",
        "username": username,
        "role": role
    }


@app.delete("/admin/users/{username}")
async def admin_delete_user(
    username: str,
    admin: TokenPayload = Depends(get_admin_user)
):
    """
    Delete a user (admin only).
    
    Prevents self-deletion for safety.
    
    Requires admin role.
    """
    # Prevent self-deletion
    if username == admin.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    delete_user(username)
    
    return {
        "message": "User deleted successfully",
        "username": username
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "name": "Smart Energy Auth Service",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin",
        "health": "/health"
    }


# Mount static UI files
auth_ui_path = Path(__file__).parent.parent / "auth_ui"
admin_ui_path = Path(__file__).parent.parent / "admin_ui"

if auth_ui_path.exists():
    app.mount("/register", StaticFiles(directory=str(auth_ui_path), html=True), name="register")

if admin_ui_path.exists():
    app.mount("/admin", StaticFiles(directory=str(admin_ui_path), html=True), name="admin")


# Seed admin user on startup
@app.on_event("startup")
async def startup_event():
    """Initialize admin user on startup."""
    seed_admin_user()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
