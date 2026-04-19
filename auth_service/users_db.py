"""
In-memory user storage (to be replaced with PostgreSQL in production).
"""
from dataclasses import dataclass


@dataclass
class User:
    """User data model."""
    username: str
    hashed_password: str
    totp_secret: str
    allowed_storages: list[str]
    role: str = "user"  # "user" or "admin"


# In-memory storage: {username: User}
users_store: dict[str, User] = {}


def get_user(username: str) -> User | None:
    """Retrieve user by username."""
    return users_store.get(username)


def get_all_users() -> dict[str, User]:
    """Retrieve all users."""
    return users_store.copy()


def user_exists(username: str) -> bool:
    """Check if user already exists."""
    return username in users_store


def create_user(
    username: str,
    hashed_password: str,
    totp_secret: str,
    allowed_storages: list[str],
    role: str = "user"
) -> User:
    """Create and store a new user."""
    user = User(
        username=username,
        hashed_password=hashed_password,
        totp_secret=totp_secret,
        allowed_storages=allowed_storages,
        role=role
    )
    users_store[username] = user
    return user


def delete_user(username: str) -> bool:
    """Delete a user. Returns True if user existed and was deleted."""
    if username in users_store:
        del users_store[username]
        return True
    return False


def update_user_storages(username: str, allowed_storages: list[str]) -> bool:
    """Update allowed storages for a user."""
    user = users_store.get(username)
    if user:
        user.allowed_storages = allowed_storages
        return True
    return False


def update_user_role(username: str, role: str) -> bool:
    """Update role for a user."""
    user = users_store.get(username)
    if user:
        user.role = role
        return True
    return False


def seed_admin_user():
    """Create default admin user on startup if not exists."""
    from .utils.password import hash_password
    from .utils.totp import generate_secret, get_qr_uri

    if not user_exists("admin"):
        totp_secret = generate_secret()
        create_user(
            username="admin",
            hashed_password=hash_password("admin123"),
            totp_secret=totp_secret,
            allowed_storages=["postgres", "mongodb", "s3", "hdfs"],
            role="admin"
        )
        qr_uri = get_qr_uri(totp_secret, "admin", "SmartEnergy")
        print("[SEED] ============================================================")
        print("[SEED] Admin user created!")
        print("[SEED] Username: admin")
        print("[SEED] Password: admin123")
        print(f"[SEED] TOTP Secret: {totp_secret}")
        print(f"[SEED] Add to Google Authenticator manually or scan URI:")
        print(f"[SEED] {qr_uri}")
        print("[SEED] ============================================================")
    else:
        admin = get_user("admin")
        print(f"[SEED] Admin user exists. TOTP secret: {admin.totp_secret}")
