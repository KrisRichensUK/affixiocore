#!/usr/bin/env python3

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class VerificationRequest(BaseModel):
    secure_code: str = Field(..., description="Secure verification code")
    jurisdiction: str = Field(default="UK", description="Jurisdiction for verification")
    client_id: Optional[str] = Field(None, description="Client identifier")
    security_answers: Optional[Dict[str, str]] = Field(None, description="HMRC-style security question answers")
    
    @validator('secure_code')
    def validate_secure_code(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Secure code must be at least 3 characters')
        return v.upper()
    
    @validator('jurisdiction')
    def validate_jurisdiction(cls, v):
        valid_jurisdictions = ['UK', 'US', 'EU', 'CA', 'AU']
        if v not in valid_jurisdictions:
            raise ValueError(f'Jurisdiction must be one of: {valid_jurisdictions}')
        return v.upper()

class VerificationResponse(BaseModel):
    verdict: str = Field(..., description="Verification result: YES or NO")
    jwt_token: str = Field(..., description="Signed JWT token containing verification details")
    qr_code: str = Field(..., description="Base64 encoded QR code")

class SecureData(BaseModel):
    secure_code: str
    eligibility_score: int
    risk_ratio: float
    stability_years: int
    jurisdiction_verified: bool
    verification_tier: str
    car_registration: str
    first_movie_seen: str
    first_pet_name: str
    mothers_maiden_name: str
    first_school_name: str
    favorite_color: str
    birth_town: str
    
    @validator('eligibility_score')
    def validate_eligibility_score(cls, v):
        if v < 0 or v > 1000:
            raise ValueError('Eligibility score must be between 0 and 1000')
        return v
    
    @validator('risk_ratio')
    def validate_risk_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Risk ratio must be between 0 and 1')
        return v
    
    @validator('stability_years')
    def validate_stability_years(cls, v):
        if v < 0:
            raise ValueError('Stability years cannot be negative')
        return v

class RuleCondition(BaseModel):
    fact: str
    operator: str
    value: Any
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = [
            'EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'LESS_THAN',
            'GREATER_THAN_EQUAL', 'LESS_THAN_EQUAL',
            'IN', 'NOT_IN', 'CONTAINS', 'NOT_CONTAINS'
        ]
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v

class Rule(BaseModel):
    name: str
    conditions: Dict[str, Any]
    action: str
    reason_pass: Optional[str] = None
    reason_fail: Optional[str] = None
    jurisdiction: Optional[str] = None
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['GRANT_YES', 'GRANT_NO', 'NO_DECISION']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v

class EndpointConfig(BaseModel):
    url: str
    method: str = "GET"
    auth_type: str = "none"
    auth_token: Optional[str] = None
    timeout: int = 30
    retries: int = 3
    
    @validator('method')
    def validate_method(cls, v):
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE']
        if v not in valid_methods:
            raise ValueError(f'Method must be one of: {valid_methods}')
        return v.upper()
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        valid_auth_types = ['none', 'api_key', 'oauth', 'bearer']
        if v not in valid_auth_types:
            raise ValueError(f'Auth type must be one of: {valid_auth_types}')
        return v
