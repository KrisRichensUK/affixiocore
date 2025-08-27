#!/usr/bin/env python3

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = Field(default="0.0.0.0", env="AFFIXIO_HOST")
    port: int = Field(default=8000, env="AFFIXIO_PORT")
    debug: bool = Field(default=False, env="AFFIXIO_DEBUG")
    
    jwt_secret: str = Field(default="your-super-secret-jwt-key-that-is-at-least-32-characters-long", env="AFFIXIO_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="AFFIXIO_JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, env="AFFIXIO_JWT_EXPIRY_HOURS")
    
    config_dir: str = Field(default="config", env="AFFIXIO_CONFIG_DIR")
    
    rules: Dict[str, Any] = {}
    endpoints: Dict[str, Any] = {}
    
    class Config:
        env_file = ".env"
        case_sensitive = False

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _load_config_files(_settings)
    return _settings

def _load_config_files(settings: Settings) -> None:
    config_path = Path(settings.config_dir)
    
    rules_file = config_path / "rules.json"
    if rules_file.exists():
        with open(rules_file, 'r') as f:
            settings.rules = json.load(f)
    
    endpoints_file = config_path / "endpoints.json"
    if endpoints_file.exists():
        with open(endpoints_file, 'r') as f:
            settings.endpoints = json.load(f)

def reload_config() -> None:
    global _settings
    _settings = None
    get_settings()
