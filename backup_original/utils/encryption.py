#!/usr/bin/env python3

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileEncryption:
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption with master key or generate one"""
        if master_key:
            self.master_key = master_key
        else:
            # Use environment variable or generate from system
            self.master_key = os.environ.get('AFFIXIO_MASTER_KEY', self._generate_master_key())
        
        self.fernet = self._create_fernet()
    
    def _generate_master_key(self) -> str:
        """Generate a master key from system entropy"""
        import secrets
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from master key"""
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'affixio_salt_2024',  # Fixed salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def encrypt_file(self, file_path: str) -> str:
        """Encrypt a Python file and return encrypted content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Encrypt the content
            encrypted_content = self.fernet.encrypt(content)
            
            # Create encrypted file path
            encrypted_path = file_path + '.encrypted'
            
            # Save encrypted content
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_content)
            
            print(f"Encrypted: {file_path} -> {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            print(f"Failed to encrypt {file_path}: {e}")
            raise
    
    def decrypt_content(self, encrypted_content: bytes) -> str:
        """Decrypt content and return as string"""
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_content)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Failed to decrypt content: {e}")
            raise
    
    def decrypt_file(self, file_path: str) -> str:
        """Decrypt a file and return its content"""
        try:
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()
            
            return self.decrypt_content(encrypted_content)
            
        except Exception as e:
            print(f"Failed to decrypt {file_path}: {e}")
            raise

class EncryptedModuleLoader:
    """Custom module loader for encrypted Python files"""
    
    def __init__(self, encryption: FileEncryption):
        self.encryption = encryption
        self.cache: Dict[str, str] = {}
    
    def load_encrypted_module(self, module_path: str) -> str:
        """Load and decrypt a module, caching the result"""
        if module_path in self.cache:
            return self.cache[module_path]
        
        try:
            # Try to load encrypted version first
            encrypted_path = module_path + '.encrypted'
            if os.path.exists(encrypted_path):
                content = self.encryption.decrypt_file(encrypted_path)
                self.cache[module_path] = content
                return content
            else:
                # Fallback to original file if not encrypted
                with open(module_path, 'r') as f:
                    content = f.read()
                self.cache[module_path] = content
                return content
                
        except Exception as e:
            print(f"Failed to load encrypted module {module_path}: {e}")
            raise

def encrypt_all_python_files(source_dir: str, encryption: FileEncryption) -> Dict[str, str]:
    """Encrypt all Python files in a directory tree"""
    encrypted_files = {}
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py') and not file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    encrypted_path = encryption.encrypt_file(file_path)
                    encrypted_files[file_path] = encrypted_path
                except Exception as e:
                    print(f"Failed to encrypt {file_path}: {e}")
    
    return encrypted_files

def create_encrypted_loader():
    """Create and return an encrypted module loader"""
    encryption = FileEncryption()
    return EncryptedModuleLoader(encryption)
