"""SQLAlchemy custom types for MLID support.

This module provides SQLAlchemy column types and utilities for storing
and querying MLIDs in the database with proper validation and indexing.
"""

from typing import Any, Optional

from sqlalchemy import String, TypeDecorator
from sqlalchemy.engine import Dialect

from .mlid import MLID_TOTAL_LENGTH, is_valid_mlid, validate_mlid


class MLID(TypeDecorator):
    """SQLAlchemy column type for storing MLIDs with validation.
    
    Custom SQLAlchemy type that stores MLIDs as variable-length strings
    with automatic validation and proper database indexing. MLIDs are
    stored as VARCHAR(17) in the database for optimal performance.
    
    Features:
        - Automatic MLID validation on insert/update
        - Efficient VARCHAR storage with fixed length
        - Proper indexing support for fast queries
        - Type safety with Python MLID validation
        
    Usage:
        class User(BaseModel):
            id: Mapped[str] = mapped_column(MLID, primary_key=True)
            
    Database Schema:
        - Column type: VARCHAR(17)
        - Indexed: Yes (when used as primary key)
        - Nullable: Based on column definition
    """
    
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect: Dialect) -> Any:
        """Load the appropriate dialect implementation.
        
        Configures the underlying string type with the exact MLID length
        for optimal database storage and indexing performance.
        """
        return dialect.type_descriptor(String(MLID_TOTAL_LENGTH))
    
    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Process value before storing in database.
        
        Validates the MLID format before storing to ensure data integrity
        and consistent format in the database.
        
        Args:
            value: The MLID value to store
            dialect: The database dialect being used
            
        Returns:
            The validated MLID string or None
            
        Raises:
            ValueError: If the MLID format is invalid
        """
        if value is None:
            return None
            
        if not isinstance(value, str):
            raise ValueError(f"MLID must be a string, got {type(value).__name__}")
            
        # Validate MLID format before storing
        return validate_mlid(value)
    
    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[str]:
        """Process value retrieved from database.
        
        Validates MLIDs retrieved from the database to ensure they
        maintain proper format (useful for data migration scenarios).
        
        Args:
            value: The MLID value from database
            dialect: The database dialect being used
            
        Returns:
            The validated MLID string or None
        """
        if value is None:
            return None
            
        # Validate MLIDs from database (useful for migrations)
        if not is_valid_mlid(value):
            raise ValueError(f"Invalid MLID retrieved from database: {value}")
            
        return value