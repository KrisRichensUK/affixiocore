#!/usr/bin/env python3

import logging
import logging.handlers
import sys
from typing import Optional, Dict
from datetime import datetime
import hashlib
import hmac

from ..core.config import get_settings

def setup_logging():
    settings = get_settings()
    
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                'affixio.log',
                maxBytes=10*1024*1024,
                backupCount=5
            )
        ]
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

class PseudonymisedLogger:
    def __init__(self, salt: Optional[str] = None):
        self.salt = salt or get_settings().jwt_secret
    
    def hash_identifier(self, identifier: str) -> str:
        return hmac.new(
            self.salt.encode(),
            identifier.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def log_verification_request(self, nino: str, jurisdiction: str, client_id: Optional[str] = None):
        hashed_nino = self.hash_identifier(nino)
        hashed_client = self.hash_identifier(client_id) if client_id else "none"
        
        logger = get_logger("audit")
        logger.info(
            f"VERIFICATION_REQUEST | "
            f"nino_hash={hashed_nino} | "
            f"jurisdiction={jurisdiction} | "
            f"client_hash={hashed_client} | "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_verification_result(self, nino: str, verdict: str, reasoning: str):
        hashed_nino = self.hash_identifier(nino)
        reasoning_hash = hashlib.sha256(reasoning.encode()).hexdigest()
        
        logger = get_logger("audit")
        logger.info(
            f"VERIFICATION_RESULT | "
            f"nino_hash={hashed_nino} | "
            f"verdict={verdict} | "
            f"reasoning_hash={reasoning_hash} | "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_data_access(self, nino: str, source: str, success: bool):
        hashed_nino = self.hash_identifier(nino)
        
        logger = get_logger("audit")
        logger.info(
            f"DATA_ACCESS | "
            f"nino_hash={hashed_nino} | "
            f"source={source} | "
            f"success={success} | "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict[str, str]] = None):
        logger = get_logger("audit")
        
        context_str = ""
        if context:
            hashed_context = {}
            for key, value in context.items():
                if "id" in key.lower() or "nino" in key.lower():
                    hashed_context[key] = self.hash_identifier(value)
                else:
                    hashed_context[key] = value
            context_str = f" | context={hashed_context}"
        
        logger.error(
            f"ERROR | "
            f"type={error_type} | "
            f"message={error_message} | "
            f"timestamp={datetime.utcnow().isoformat()}"
            f"{context_str}"
        )

