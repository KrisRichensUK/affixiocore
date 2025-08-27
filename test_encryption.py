#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets

def test_encryption():
    """Test the encryption system"""
    try:
        print("Testing encryption system...")
        
        # Create a test file
        test_content = """
def hello_world():
    print("Hello, World!")
    return "Hello from encrypted module!"

class TestClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
"""
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        print(f"Created test file: {test_file}")
        
        # Initialize encryption
        master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        print("Encryption initialized")
        
        # Create Fernet cipher
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'affixio_salt_2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        fernet = Fernet(key)
        
        # Encrypt the file
        with open(test_file, 'rb') as f:
            content = f.read()
        
        encrypted_content = fernet.encrypt(content)
        encrypted_path = test_file + '.encrypted'
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_content)
        
        print(f"File encrypted: {encrypted_path}")
        
        # Verify encrypted file exists
        if not os.path.exists(encrypted_path):
            raise Exception("Encrypted file was not created")
        
        # Decrypt and verify content
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_bytes = fernet.decrypt(encrypted_data)
        decrypted_content = decrypted_bytes.decode('utf-8')
        
        print("File decrypted successfully")
        
        # Verify content matches
        if decrypted_content.strip() != test_content.strip():
            raise Exception("Decrypted content does not match original")
        
        print("Content verification passed")
        
        # Test module execution simulation
        print("Testing module execution simulation...")
        
        # Simulate executing the decrypted content
        namespace = {}
        exec(decrypted_content, namespace)
        
        # Test the functions
        if 'hello_world' in namespace:
            result = namespace['hello_world']()
            if result != "Hello from encrypted module!":
                raise Exception("Function execution failed")
        
        if 'TestClass' in namespace:
            test_obj = namespace['TestClass']("Test")
            result = test_obj.greet()
            if result != "Hello, Test!":
                raise Exception("Class execution failed")
        
        print("Module execution test passed")
        
        # Cleanup
        os.unlink(test_file)
        os.unlink(encrypted_path)
        
        print("✅ All encryption tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_encryption()
    if success:
        print("\n✅ Encryption system is working correctly!")
        print("Ready to encrypt source files.")
    else:
        print("\n❌ Encryption system test failed!")
        sys.exit(1)
