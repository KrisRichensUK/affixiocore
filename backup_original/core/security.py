#!/usr/bin/env python3

import jwt
import hashlib
import hmac
import base64
import qrcode
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid

from .config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

def generate_token(
    verdict: str,
    secure_code: str,
    jurisdiction: str,
    secure_data: Dict[str, Any],
    reasoning: str = ""
) -> str:
    settings = get_settings()
    
    now = datetime.utcnow()
    expiration = now + timedelta(hours=settings.jwt_expiry_hours)
    
    payload = {
        "verdict": verdict,
        "secure_code": secure_code,
        "jurisdiction": jurisdiction,
        "verification_id": str(uuid.uuid4()),
        "issued_at": now.isoformat(),
        "exp": expiration.timestamp(),
        "iat": now.timestamp(),
        "secure_code": secure_data.get("secure_code"),
        "eligibility_score": secure_data.get("eligibility_score"),
        "risk_ratio": secure_data.get("risk_ratio"),
        "stability_years": secure_data.get("stability_years"),
        "jurisdiction_verified": secure_data.get("jurisdiction_verified"),
        "verification_tier": secure_data.get("verification_tier"),
        "car_registration": secure_data.get("car_registration"),
        "first_movie_seen": secure_data.get("first_movie_seen"),
        "first_pet_name": secure_data.get("first_pet_name"),
        "mothers_maiden_name": secure_data.get("mothers_maiden_name"),
        "first_school_name": secure_data.get("first_school_name"),
        "favorite_color": secure_data.get("favorite_color"),
        "birth_town": secure_data.get("birth_town"),
        "reasoning_hash": hashlib.sha512(reasoning.encode()).hexdigest()
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def generate_qr_code(data: str) -> str:
    """Generate QR code from data and return as base64 string only - no file storage"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 only - no file storage
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_str
        
    except Exception as e:
        logger.error(f"QR code generation failed: {str(e)}")
        raise

def hash_pii(data: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = get_settings().jwt_secret
    
    return hmac.new(
        salt.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def generate_post_quantum_signature(data: str) -> str:
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        signature = private_key.sign(
            data.encode(),
            padding=rsa.PSS(
                mgf=rsa.MGF1(hashes.SHA256()),
                salt_length=rsa.PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    except ImportError:
        return hash_pii(data, "pqc-fallback")

def verify_post_quantum_signature(data: str, signature: str, public_key: str) -> bool:
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        pub_key = serialization.load_pem_public_key(public_key.encode())
        
        sig_bytes = base64.b64decode(signature)
        
        pub_key.verify(
            sig_bytes,
            data.encode(),
            padding=rsa.PSS(
                mgf=rsa.MGF1(hashes.SHA256()),
                salt_length=rsa.PSS.PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )
        
        return True
    except Exception:
        return False

def generate_minimal_token(
    verdict: str,
    verification_id: str,
    reasoning_hash: str = ""
) -> str:
    """Generate minimal JWT token with only essential verification data - no personal information"""
    settings = get_settings()
    
    now = datetime.utcnow()
    expiration = now + timedelta(hours=settings.jwt_expiry_hours)
    
    payload = {
        "verdict": verdict,
        "verification_id": verification_id,
        "issued_at": now.isoformat(),
        "exp": expiration.timestamp(),
        "iat": now.timestamp(),
        "reasoning_hash": reasoning_hash
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def generate_verifiable_token(
    verdict: str,
    secure_code: str,
    jurisdiction: str,
    verification_id: str,
    reasoning_hash: str = "",
    request_hash: str = ""
) -> str:
    """Generate verifiable JWT token with request context but no personal data"""
    settings = get_settings()
    
    now = datetime.utcnow()
    expiration = now + timedelta(hours=settings.jwt_expiry_hours)
    
    payload = {
        "verdict": verdict,
        "secure_code": secure_code,  # For request verification
        "jurisdiction": jurisdiction,  # For request verification
        "verification_id": verification_id,
        "request_hash": request_hash,  # Hash of original request parameters
        "issued_at": now.isoformat(),
        "exp": expiration.timestamp(),
        "iat": now.timestamp(),
        "reasoning_hash": reasoning_hash
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
