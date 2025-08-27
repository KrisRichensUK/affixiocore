#!/usr/bin/env python3

import os
import sys
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def load_master_key():
    """Load the master key from file"""
    try:
        master_key_file = os.path.join(os.path.dirname(__file__), '.master_key')
        with open(master_key_file, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Failed to load master key: {e}")
        return None

def create_fernet(master_key):
    """Create Fernet cipher from master key"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'affixio_salt_2024',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    return Fernet(key)

def test_encrypted_module():
    """Test loading an encrypted module"""
    try:
        print("Testing encrypted module loading...")
        
        # Load master key
        master_key = load_master_key()
        if not master_key:
            print("Failed to load master key.")
            return False
        
        # Create Fernet cipher
        fernet = create_fernet(master_key)
        
        # Test loading main.py.encrypted
        main_encrypted_path = os.path.join(os.getcwd(), "src", "main.py.encrypted")
        
        if not os.path.exists(main_encrypted_path):
            print(f"Encrypted file not found: {main_encrypted_path}")
            return False
        
        print(f"Found encrypted file: {main_encrypted_path}")
        
        # Load and decrypt
        with open(main_encrypted_path, 'rb') as f:
            encrypted_content = f.read()
        
        decrypted_bytes = fernet.decrypt(encrypted_content)
        decrypted_content = decrypted_bytes.decode('utf-8')
        
        print("Successfully decrypted main.py")
        print(f"Content length: {len(decrypted_content)} characters")
        print(f"First 100 characters: {decrypted_content[:100]}")
        
        # Test loading config.py.encrypted
        config_encrypted_path = os.path.join(os.getcwd(), "src", "core", "config.py.encrypted")
        
        if os.path.exists(config_encrypted_path):
            with open(config_encrypted_path, 'rb') as f:
                encrypted_content = f.read()
            
            decrypted_bytes = fernet.decrypt(encrypted_content)
            decrypted_content = decrypted_bytes.decode('utf-8')
            
            print("Successfully decrypted config.py")
            print(f"Content length: {len(decrypted_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_encrypted_module()
    if success:
        print("\n✅ Encrypted module test passed!")
    else:
        print("\n❌ Encrypted module test failed!")
        sys.exit(1)
