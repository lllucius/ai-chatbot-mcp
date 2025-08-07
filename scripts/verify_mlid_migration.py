#!/usr/bin/env python3
"""
MLID Migration Verification Script

This script verifies that the UUID to MLID migration has been completed
successfully across the entire codebase.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_uuid_references(directory: str) -> List[Tuple[str, int, str]]:
    """Find remaining UUID references in Python files."""
    uuid_pattern = re.compile(r'\b(uuid|UUID)\b')
    allowed_files = {
        'app/core/logging.py',  # Uses UUID for correlation IDs
        'app/utils/mlid.py',    # Documentation mentions UUIDs  
        'docs/MLID_SYSTEM.md',  # Documentation about migration
    }
    
    references = []
    
    for root, dirs, files in os.walk(directory):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules'}]
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            
            # Skip allowed files
            if relative_path in allowed_files:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if uuid_pattern.search(line):
                            references.append((relative_path, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue
    
    return references


def verify_mlid_imports() -> bool:
    """Verify that MLID utilities can be imported correctly."""
    try:
        from app.utils.mlid import generate_mlid, is_valid_mlid, validate_mlid
        from app.utils.mlid_types import MLID
        
        # Test basic functionality
        mlid = generate_mlid()
        if not is_valid_mlid(mlid):
            print(f"❌ Generated MLID {mlid} is not valid")
            return False
            
        # Test validation
        try:
            validate_mlid(mlid)
        except ValueError:
            print(f"❌ MLID validation failed for {mlid}")
            return False
            
        print(f"✅ MLID system working: Generated {mlid}")
        return True
        
    except ImportError as e:
        print(f"❌ MLID import failed: {e}")
        return False


def verify_model_imports() -> bool:
    """Verify that database models can be imported with MLID system."""
    try:
        from app.models.base import BaseModelDB, MLIDMixin
        from app.models.user import User
        from app.models.conversation import Conversation
        from app.models.document import Document
        
        print("✅ All database models imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Model import failed: {e}")
        return False


def verify_schema_imports() -> bool:
    """Verify that Pydantic schemas work with MLID system."""
    try:
        from shared.schemas.base import MLIDMixin, BaseModelSchema
        from shared.schemas.user import UserResponse
        from shared.schemas.conversation import ConversationResponse
        from shared.schemas.document import DocumentResponse
        
        # Test MLID validation in schema
        from app.utils.mlid import generate_mlid
        mlid = generate_mlid()
        
        schema = MLIDMixin(id=mlid)
        if schema.id != mlid:
            print(f"❌ Schema MLID validation failed")
            return False
            
        print("✅ All schemas imported and working with MLID")
        return True
        
    except (ImportError, ValueError) as e:
        print(f"❌ Schema import/validation failed: {e}")
        return False


def main():
    """Run the MLID migration verification."""
    print("🔍 Verifying UUID to MLID migration...")
    print("=" * 50)
    
    # Change to the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    success = True
    
    # Check for remaining UUID references
    print("\n1. Checking for remaining UUID references...")
    uuid_refs = find_uuid_references(".")
    
    if uuid_refs:
        print(f"❌ Found {len(uuid_refs)} UUID references that may need attention:")
        for file_path, line_num, line in uuid_refs[:10]:  # Show first 10
            print(f"   {file_path}:{line_num}: {line[:80]}...")
        if len(uuid_refs) > 10:
            print(f"   ... and {len(uuid_refs) - 10} more")
        success = False
    else:
        print("✅ No problematic UUID references found")
    
    # Verify MLID system
    print("\n2. Verifying MLID system...")
    if not verify_mlid_imports():
        success = False
    
    # Verify model imports
    print("\n3. Verifying database models...")
    if not verify_model_imports():
        success = False
    
    # Verify schema imports
    print("\n4. Verifying Pydantic schemas...")
    if not verify_schema_imports():
        success = False
    
    # Final result
    print("\n" + "=" * 50)
    if success:
        print("🎉 UUID to MLID migration verification PASSED!")
        print("\nThe migration appears to be complete and working correctly.")
        sys.exit(0)
    else:
        print("❌ UUID to MLID migration verification FAILED!")
        print("\nPlease review the issues above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()