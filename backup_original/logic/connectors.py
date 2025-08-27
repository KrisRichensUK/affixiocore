#!/usr/bin/env python3

import asyncio
import httpx
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from .models import EndpointConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True

class DataConnector:
    def __init__(self, config: EndpointConfig):
        self.config = config
        self.circuit_breaker = CircuitBreaker()
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.config.timeout,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self.client
    
    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")
        
        client = await self._get_client()
        
        headers = {}
        if self.config.auth_type == "api_key" and self.config.auth_token:
            headers["X-API-Key"] = self.config.auth_token
        elif self.config.auth_type == "bearer" and self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        headers.update(kwargs.get("headers", {}))
        
        for attempt in range(self.config.retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **{k: v for k, v in kwargs.items() if k != "headers"}
                )
                
                response.raise_for_status()
                self.circuit_breaker.record_success()
                
                return response.json()
                
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                self.circuit_breaker.record_failure()
                
                if attempt == self.config.retries - 1:
                    raise Exception(f"All {self.config.retries} attempts failed: {str(e)}")
                
                await asyncio.sleep(2 ** attempt)
    
    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

class DataConnectorManager:
    def __init__(self, endpoints_config: Dict[str, Any]):
        self.endpoints_config = endpoints_config
        self.connectors: Dict[str, DataConnector] = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        for name, config_data in self.endpoints_config.items():
            try:
                config = EndpointConfig(**config_data)
                self.connectors[name] = DataConnector(config)
                logger.info(f"Initialized connector: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize connector {name}: {str(e)}")
    
    async def fetch_secure_data(self, secure_code: str) -> Dict[str, Any]:
        secure_data = {}
        
        for name, connector in self.connectors.items():
            try:
                # Format the URL with the secure code parameter
                url = connector.config.url.format(secure_code=secure_code)
                data = await connector._make_request(url, method=connector.config.method)
                secure_data.update(data)
                logger.info(f"Successfully fetched secure data from {name}")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch secure data from {name}: {str(e)}")
                continue
        
        return secure_data
    
    async def close_all(self):
        for connector in self.connectors.values():
            await connector.close()
    
    def __del__(self):
        if hasattr(self, 'connectors'):
            for connector in self.connectors.values():
                if connector.client:
                    asyncio.create_task(connector.close())
