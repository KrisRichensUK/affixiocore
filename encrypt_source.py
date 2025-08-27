#!/usr/bin/env python3

import os
import sys
import shutil
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
from pathlib import Path

def create_encryption():
    """Create encryption instance"""
    master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'affixio_salt_2024',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    fernet = Fernet(key)
    
    return fernet, master_key

def backup_original_files(source_dir: str, backup_dir: str):
    """Create a backup of original files"""
    try:
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        
        shutil.copytree(source_dir, backup_dir)
        print(f"Backup created at: {backup_dir}")
        return True
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False

def encrypt_file(file_path: str, fernet: Fernet) -> str:
    """Encrypt a Python file"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        encrypted_content = fernet.encrypt(content)
        encrypted_path = file_path + '.encrypted'
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_content)
        
        print(f"Encrypted: {file_path} -> {encrypted_path}")
        return encrypted_path
        
    except Exception as e:
        print(f"Failed to encrypt {file_path}: {e}")
        raise

def encrypt_all_python_files(source_dir: str, fernet: Fernet) -> dict:
    """Encrypt all Python files in a directory tree"""
    encrypted_files = {}
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py') and not file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    encrypted_path = encrypt_file(file_path, fernet)
                    encrypted_files[file_path] = encrypted_path
                except Exception as e:
                    print(f"Failed to encrypt {file_path}: {e}")
    
    return encrypted_files

def remove_original_python_files(source_dir: str):
    """Remove original Python files after encryption"""
    removed_count = 0
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py') and not file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                encrypted_path = file_path + '.encrypted'
                
                # Only remove if encrypted version exists
                if os.path.exists(encrypted_path):
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        print(f"Removed original: {file_path}")
                    except Exception as e:
                        print(f"Failed to remove {file_path}: {e}")
    
    return removed_count

def encrypt_source_code():
    """Main function to encrypt all source code"""
    try:
        # Get project root
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(project_root, 'src')
        
        print("Starting source code encryption...")
        print(f"Project root: {project_root}")
        print(f"Source directory: {src_dir}")
        
        # Create backup
        backup_dir = os.path.join(project_root, 'backup_original')
        if not backup_original_files(src_dir, backup_dir):
            print("Failed to create backup. Aborting encryption.")
            return False
        
        # Initialize encryption
        fernet, master_key = create_encryption()
        print("Encryption initialized")
        
        # Encrypt all Python files
        print("Encrypting Python files...")
        encrypted_files = encrypt_all_python_files(src_dir, fernet)
        
        print(f"Encrypted {len(encrypted_files)} files")
        
        # Remove original files
        print("Removing original Python files...")
        removed_count = remove_original_python_files(src_dir)
        
        print(f"Removed {removed_count} original files")
        
        # Save master key (in production, this should be stored securely)
        master_key_file = os.path.join(project_root, '.master_key')
        with open(master_key_file, 'w') as f:
            f.write(master_key)
        
        print(f"Master key saved to: {master_key_file}")
        print("IMPORTANT: Store the master key securely! The application cannot run without it.")
        
        # Create a note about the backup
        backup_note = os.path.join(project_root, 'BACKUP_INFO.txt')
        with open(backup_note, 'w') as f:
            f.write(f"""BACKUP INFORMATION
==================

Original source files have been backed up to: {backup_dir}

To restore original files:
1. Stop the application
2. Copy files from {backup_dir} back to {src_dir}
3. Remove .encrypted files
4. Restart the application

Master key location: {master_key_file}

WARNING: Keep the master key secure! Without it, the encrypted files cannot be decrypted.
""")
        
        print("Encryption completed successfully!")
        print(f"Backup location: {backup_dir}")
        print(f"Master key location: {master_key_file}")
        
        return True
        
    except Exception as e:
        print(f"Encryption failed: {e}")
        return False

if __name__ == "__main__":
    success = encrypt_source_code()
    if success:
        print("\n✅ Source code encryption completed successfully!")
        print("📁 Original files backed up to 'backup_original/'")
        print("🔑 Master key saved to '.master_key'")
        print("⚠️  Keep the master key secure!")
        print("\nThe application will now run with encrypted source files.")
    else:
        print("\n❌ Source code encryption failed!")
        sys.exit(1)
