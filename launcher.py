#!/usr/bin/env python3

import os
import sys
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import importlib.abc
import importlib.machinery
import importlib.util

class EncryptedModuleFinder(importlib.abc.MetaPathFinder):
    """Custom finder for encrypted Python modules"""
    
    def __init__(self, fernet):
        self.fernet = fernet
    
    def find_spec(self, fullname, path, target=None):
        """Find module specification for encrypted modules"""
        try:
            # Convert module name to file path
            if path is None:
                # Top-level module
                module_path = self._get_module_path(fullname)
            else:
                # Submodule
                module_path = self._get_module_path(fullname, path[0])
            
            if module_path and os.path.exists(module_path):
                # Check if encrypted version exists
                encrypted_path = module_path + '.encrypted'
                if os.path.exists(encrypted_path):
                    return importlib.util.spec_from_file_location(
                        fullname, 
                        encrypted_path,
                        loader=EncryptedModuleLoader(self.fernet, fullname)
                    )
                elif os.path.exists(module_path):
                    # Fallback to regular file
                    return importlib.util.spec_from_file_location(
                        fullname,
                        module_path,
                        loader=EncryptedModuleLoader(self.fernet, fullname)
                    )
            
            return None
            
        except Exception as e:
            print(f"Error finding module {fullname}: {e}")
            return None
    
    def _get_module_path(self, fullname: str, base_path=None):
        """Convert module name to file path"""
        try:
            if base_path:
                # Submodule
                module_name = fullname.split('.')[-1]
                return os.path.join(base_path, f"{module_name}.py")
            else:
                # Top-level module - search in current directory and src
                module_name = fullname.split('.')[-1]
                
                # Check current directory
                current_path = os.path.join(os.getcwd(), f"{module_name}.py")
                if os.path.exists(current_path):
                    return current_path
                
                # Check src directory
                src_path = os.path.join(os.getcwd(), "src", f"{module_name}.py")
                if os.path.exists(src_path):
                    return src_path
                
                # Check if it's a submodule in src
                parts = fullname.split('.')
                if len(parts) > 1:
                    # Handle nested modules like src.core.security
                    if parts[0] == 'src' and len(parts) > 1:
                        # Remove 'src' from parts and build path
                        module_parts = parts[1:]
                        src_module_path = os.path.join(os.getcwd(), "src", *module_parts[:-1], f"{module_parts[-1]}.py")
                        if os.path.exists(src_module_path):
                            return src_module_path
                    
                    # Also try without 'src' prefix
                    src_module_path = os.path.join(os.getcwd(), "src", *parts[:-1], f"{parts[-1]}.py")
                    if os.path.exists(src_module_path):
                        return src_module_path
                
                return None
                
        except Exception as e:
            print(f"Error getting module path for {fullname}: {e}")
            return None

class EncryptedModuleLoader(importlib.abc.Loader):
    """Custom loader for encrypted Python modules"""
    
    def __init__(self, fernet, fullname: str):
        self.fernet = fernet
        self.fullname = fullname
    
    def exec_module(self, module):
        """Execute the module with decrypted content"""
        try:
            # Get the module file path
            module_path = module.__file__
            
            # Load and decrypt the module content
            if module_path.endswith('.encrypted'):
                # Load encrypted content
                with open(module_path, 'rb') as f:
                    encrypted_content = f.read()
                
                decrypted_bytes = self.fernet.decrypt(encrypted_content)
                content = decrypted_bytes.decode('utf-8')
            else:
                # Load regular content
                with open(module_path, 'r') as f:
                    content = f.read()
            
            # Execute the module content
            exec(content, module.__dict__)
            
        except Exception as e:
            print(f"Error executing module {self.fullname}: {e}")
            raise

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

def install_encrypted_importer():
    """Install the encrypted module importer"""
    try:
        # Load master key
        master_key = load_master_key()
        if not master_key:
            print("Failed to load master key. Make sure .master_key file exists.")
            return False
        
        # Create Fernet cipher
        fernet = create_fernet(master_key)
        
        # Remove any existing encrypted importers
        sys.meta_path = [finder for finder in sys.meta_path 
                        if not isinstance(finder, EncryptedModuleFinder)]
        
        # Add our encrypted finder
        encrypted_finder = EncryptedModuleFinder(fernet)
        sys.meta_path.insert(0, encrypted_finder)
        
        print("Encrypted module importer installed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to install encrypted importer: {e}")
        return False

def main():
    """Main launcher function"""
    try:
        print("Starting Affixio Engine with encrypted source files...")
        
        # Add src directory to Python path
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        sys.path.insert(0, src_path)
        
        # Install encrypted importer
        if not install_encrypted_importer():
            print("Failed to install encrypted importer. Exiting.")
            sys.exit(1)
        
        # Import and run the main application
        import uvicorn
        from main import app
        from core.config import get_settings
        
        settings = get_settings()
        print(f"Starting server on {settings.host}:{settings.port}")
        
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=False  # Disable reload for encrypted files
        )
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
