#!/usr/bin/env python3

import asyncio
from typing import Dict, Any, List, Tuple
import logging
import uuid
import hashlib

from .config import get_settings
from .security import generate_token, generate_qr_code
from ..logic.connectors import DataConnectorManager
from ..logic.rules import RuleEngine
from ..logic.models import VerificationRequest, VerificationResponse
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StatelessEngine:
    def __init__(self):
        self.settings = get_settings()
        self.connector_manager = DataConnectorManager(self.settings.endpoints)
        self.rule_engine = RuleEngine(self.settings.rules)
        
    async def process_request(self, request: VerificationRequest) -> VerificationResponse:
        try:
            logger.info(f"Starting verification process for secure code: {request.secure_code[:3]}***")
            logger.info(f"Request security_answers: {request.security_answers}")
            
            context = {
                "secure_code": request.secure_code,
                "jurisdiction": request.jurisdiction,
                "client_id": request.client_id
            }
            
            secure_data = await self._fetch_secure_data(request.secure_code)
            if secure_data:
                context.update(secure_data)
                
                # Validate security answers if provided (BEFORE rule evaluation)
                if request.security_answers:
                    logger.info(f"Security answers provided: {list(request.security_answers.keys())}")
                    security_validation = self._validate_security_answers(request.security_answers, secure_data)
                    if not security_validation['valid']:
                        logger.warning(f"Security answers validation failed: {security_validation['reason']}")
                        return VerificationResponse(
                            verdict="NO",
                            jwt_token="",
                            qr_code=""
                        )
                    logger.info("Security answers validation passed")
                else:
                    logger.info("No security answers provided")
            
            verdict, reasoning = await self._evaluate_rules(context)
            
            # Generate verifiable token with request context but no personal data
            verification_id = str(uuid.uuid4())
            reasoning_hash = hashlib.sha512(reasoning.encode()).hexdigest()
            
            # Create request hash for verification
            request_data = f"{request.secure_code}:{request.jurisdiction}:{request.client_id or 'none'}"
            request_hash = hashlib.sha256(request_data.encode()).hexdigest()
            
            token = generate_verifiable_token(
                verdict=verdict,
                secure_code=request.secure_code,
                jurisdiction=request.jurisdiction,
                verification_id=verification_id,
                reasoning_hash=reasoning_hash,
                request_hash=request_hash
            )
            
            # Generate QR code without file storage
            qr_code = generate_qr_code(token)
            logger.info(f"QR code generated successfully, length: {len(qr_code)}")
            
            logger.info(f"Verification completed - Verdict: {verdict}")
            
            return VerificationResponse(
                verdict=verdict,
                jwt_token=token,
                qr_code=qr_code
            )
            
        except Exception as e:
            logger.error(f"Verification process failed: {str(e)}")
            raise
        finally:
            self._cleanup()
    
    async def _fetch_secure_data(self, secure_code: str) -> Dict[str, Any]:
        try:
            secure_data = await self.connector_manager.fetch_secure_data(secure_code)
            logger.info(f"Successfully fetched secure data for code: {secure_code[:3]}***")
            return secure_data
        except Exception as e:
            logger.warning(f"Failed to fetch secure data: {str(e)}")
            return {}
    
    async def _evaluate_rules(self, context: Dict[str, Any]) -> Tuple[str, str]:
        try:
            verdict, reasoning = self.rule_engine.evaluate(context)
            logger.info(f"Rule evaluation completed - Verdict: {verdict}")
            return verdict, reasoning
        except Exception as e:
            logger.error(f"Rule evaluation failed: {str(e)}")
            return "NO_DECISION", f"Rule evaluation error: {str(e)}"
    
    def _validate_security_answers(self, provided_answers: Dict[str, str], secure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HMRC-style security answers against stored data"""
        try:
            valid_fields = [
                'car_registration', 'first_movie_seen', 'first_pet_name', 
                'mothers_maiden_name', 'first_school_name', 'favorite_color', 'birth_town'
            ]
            
            # Check if at least one security answer is provided
            if not provided_answers:
                return {
                    'valid': False,
                    'reason': 'No security answer provided'
                }
            
            # Validate the provided answer against stored data (case-insensitive)
            for field, provided_answer in provided_answers.items():
                if field not in valid_fields:
                    return {
                        'valid': False,
                        'reason': f'Invalid security question field: {field}'
                    }
                
                if not provided_answer or not provided_answer.strip():
                    return {
                        'valid': False,
                        'reason': f'Empty security answer for: {field}'
                    }
                
                provided = provided_answer.strip().lower()
                stored = secure_data.get(field, '').strip().lower()
                
                if provided != stored:
                    return {
                        'valid': False,
                        'reason': f'Security answer mismatch for: {field}'
                    }
                
                # If we get here, the answer is correct
                return {'valid': True, 'reason': f'Security answer validated successfully for: {field}'}
            
            return {'valid': True, 'reason': 'Security answer validated successfully'}
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            return {
                'valid': False,
                'reason': f'Security validation error: {str(e)}'
            }
    
    def _cleanup(self):
        del self.connector_manager
        del self.rule_engine
        logger.debug("Engine cleanup completed - all data cleared from memory")
