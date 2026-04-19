"""
TOTP (Time-based One-Time Password) utilities using pyotp and qrcode.
"""
import base64
import io
import qrcode
import pyotp


def generate_secret() -> str:
    """
    Generate a random base32-encoded secret for TOTP.
    
    Returns:
        Random base32 secret suitable for TOTP
    """
    return pyotp.random_base32()


def get_qr_uri(secret: str, username: str, issuer_name: str = "SmartEnergy") -> str:
    """
    Generate a provisioning URI for TOTP that can be encoded as QR code.
    
    Args:
        secret: Base32-encoded TOTP secret
        username: Username to display in authenticator app
        issuer_name: Issuer name (e.g., "SmartEnergy")
        
    Returns:
        Provisioning URI compatible with Google Authenticator
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer_name)


def generate_qr_code_base64(uri: str) -> str:
    """
    Generate a QR code PNG image and encode as base64 string.
    
    Args:
        uri: Provisioning URI to encode in QR code
        
    Returns:
        Base64-encoded PNG image of QR code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Create PIL image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    return img_base64


def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a TOTP code against a secret.
    
    Args:
        secret: Base32-encoded TOTP secret
        code: TOTP code to verify (usually 6 digits)
        valid_window: Number of 30-second windows to check before/after current time.
                     1 means ±30 seconds clock drift tolerance.
        
    Returns:
        True if code is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    result = totp.verify(code, valid_window=valid_window)
    if not result:
        import time
        print(f"[TOTP DEBUG] Current time: {time.time()}, Expected code: {totp.now()}, Got: {code}")
    return result
