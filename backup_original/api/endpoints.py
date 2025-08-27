#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
import logging
import time

from ..logic.models import VerificationRequest, VerificationResponse
from ..core.stateless_engine import StatelessEngine
from ..utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/verify", response_model=VerificationResponse)
async def verify_eligibility(
    request: VerificationRequest,
    http_request: Request,
    engine: StatelessEngine = Depends(StatelessEngine)
):
    start_time = time.time()
    
    try:
        logger.info(f"Processing verification request for secure code: {request.secure_code[:3]}***")
        
        result = await engine.process_request(request)
        
        process_time = time.time() - start_time
        logger.info(f"Verification completed in {process_time:.3f}s - Verdict: {result.verdict}")
        
        return result
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/verify-request")
async def verify_original_request(
    token: str,
    secure_code: str,
    jurisdiction: str,
    client_id: str = None
):
    """Verify that the provided request parameters match the original request in the token"""
    try:
        from ..core.security import verify_token
        import hashlib
        
        payload = verify_token(token)
        
        # Recreate the request hash
        request_data = f"{secure_code}:{jurisdiction}:{client_id or 'none'}"
        request_hash = hashlib.sha256(request_data.encode()).hexdigest()
        
        # Verify the request parameters match
        token_secure_code = payload.get("secure_code")
        token_jurisdiction = payload.get("jurisdiction")
        token_request_hash = payload.get("request_hash")
        
        if (secure_code != token_secure_code or 
            jurisdiction != token_jurisdiction or 
            request_hash != token_request_hash):
            return {
                "verified": False,
                "reason": "Request parameters do not match original verification"
            }
        
        return {
            "verified": True,
            "verdict": payload.get("verdict"),
            "verification_id": payload.get("verification_id"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp")
        }
        
    except Exception as e:
        logger.error(f"Request verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token or verification failed")

@router.get("/verify-qr/{token}")
async def verify_qr_token(token: str):
    try:
        from ..core.security import verify_token
        payload = verify_token(token)
        
        return {
            "verified": True,
            "verdict": payload.get("verdict"),
            "secure_code": payload.get("secure_code"),  # For request verification
            "jurisdiction": payload.get("jurisdiction"),  # For request verification
            "verification_id": payload.get("verification_id"),
            "request_hash": payload.get("request_hash"),  # For request integrity
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp"),
            "reasoning_hash": payload.get("reasoning_hash")
        }
        
    except Exception as e:
        logger.error(f"QR token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.get("/qr-image/{token}")
async def get_qr_image(token: str):
    try:
        from ..core.security import generate_qr_code
        qr_code_data = generate_qr_code(token)
        
        import base64
        image_data = base64.b64decode(qr_code_data)
        
        return Response(
            content=image_data,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=verification-{token[:8]}.png"}
        )
        
    except Exception as e:
        logger.error(f"QR image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="QR generation failed")

@router.get("/rules")
async def get_rules():
    try:
        from ..core.config import get_settings
        settings = get_settings()
        return {"rules": settings.rules}
    except Exception as e:
        logger.error(f"Failed to retrieve rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rules")

@router.get("/endpoints")
async def get_endpoints():
    try:
        from ..core.config import get_settings
        settings = get_settings()
        return {"endpoints": settings.endpoints}
    except Exception as e:
        logger.error(f"Failed to retrieve endpoints: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve endpoints")
