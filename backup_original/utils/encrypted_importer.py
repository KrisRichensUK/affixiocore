#!/usr/bin/env python3

import sys
import os
import importlib.abc
import importlib.machinery
import importlib.util
from typing import Optional

from .encryption import create_encrypted_loader

class EncryptedModuleFinder(importlib.abc.MetaPathFinder):
    """Custom finder for encrypted Python modules"""
    
    def __init__(self):
        self.loader = create_encrypted_loader()
    
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
                    print(f"Found encrypted module: {fullname} -> {encrypted_path}")
                    return importlib.util.spec_from_file_location(
                        fullname, 
                        encrypted_path,
                        loader=EncryptedModuleLoader(self.loader, fullname)
                    )
                elif os.path.exists(module_path):
                    # Fallback to regular file
                    print(f"Found regular module: {fullname} -> {module_path}")
                    return importlib.util.spec_from_file_location(
                        fullname,
                        module_path,
                        loader=EncryptedModuleLoader(self.loader, fullname)
                    )
            
            return None
            
        except Exception as e:
            print(f"Error finding module {fullname}: {e}")
            return None
    
    def _get_module_path(self, fullname: str, base_path: Optional[str] = None) -> Optional[str]:
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
                    src_module_path = os.path.join(os.getcwd(), "src", *parts[:-1], f"{parts[-1]}.py")
                    if os.path.exists(src_module_path):
                        return src_module_path
                
                return None
                
        except Exception as e:
            print(f"Error getting module path for {fullname}: {e}")
            return None

class EncryptedModuleLoader(importlib.abc.Loader):
    """Custom loader for encrypted Python modules"""
    
    def __init__(self, encrypted_loader, fullname: str):
        self.encrypted_loader = encrypted_loader
        self.fullname = fullname
    
    def exec_module(self, module):
        """Execute the module with decrypted content"""
        try:
            # Get the module file path
            module_path = module.__file__
            
            # Load and decrypt the module content
            if module_path.endswith('.encrypted'):
                # Load encrypted content
                content = self.encrypted_loader.load_encrypted_module(module_path)
            else:
                # Load regular content
                with open(module_path, 'r') as f:
                    content = f.read()
            
            # Execute the module content
            exec(content, module.__dict__)
            
        except Exception as e:
            print(f"Error executing module {self.fullname}: {e}")
            raise

def install_encrypted_importer():
    """Install the encrypted module importer"""
    try:
        # Remove any existing encrypted importers
        sys.meta_path = [finder for finder in sys.meta_path 
                        if not isinstance(finder, EncryptedModuleFinder)]
        
        # Add our encrypted finder
        encrypted_finder = EncryptedModuleFinder()
        sys.meta_path.insert(0, encrypted_finder)
        
        print("Encrypted module importer installed successfully")
        return encrypted_finder
        
    except Exception as e:
        print(f"Failed to install encrypted importer: {e}")
        raise

def uninstall_encrypted_importer():
    """Remove the encrypted module importer"""
    try:
        sys.meta_path = [finder for finder in sys.meta_path 
                        if not isinstance(finder, EncryptedModuleFinder)]
        print("Encrypted module importer uninstalled")
    except Exception as e:
        print(f"Failed to uninstall encrypted importer: {e}")
        raise
