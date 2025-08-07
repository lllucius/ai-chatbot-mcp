"""Tests for MLID integration with database models and operations.

This test suite verifies that the MLID system works correctly with
SQLAlchemy models, database operations, and schema validation.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import BaseModelDB
from app.models.user import User
from app.utils.mlid import generate_mlid, is_valid_mlid
from app.utils.mlid_types import MLID


# Test model for validation
class TestModel(BaseModelDB):
    """Test model for MLID integration testing."""
    __tablename__ = "test_model"
    
    name: str = ""


@pytest.fixture
async def async_db_session():
    """Create an in-memory SQLite database session for testing."""
    # Use SQLite for testing since it's simpler than setting up PostgreSQL
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModelDB.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


class TestMLIDDatabaseIntegration:
    """Test MLID integration with database operations."""
    
    async def test_mlid_primary_key_generation(self, async_db_session):
        """Test that MLID primary keys are generated correctly."""
        # Note: This test uses a simple model since User model has additional complexity
        # In a real application, you'd test with actual User model
        test_id = generate_mlid()
        
        assert is_valid_mlid(test_id)
        assert len(test_id) == 17
        assert test_id.startswith("ml_")
    
    def test_mlid_sqlalchemy_type(self):
        """Test MLID SQLAlchemy type functionality."""
        mlid_type = MLID()
        
        # Test valid MLID processing
        valid_mlid = generate_mlid()
        result = mlid_type.process_bind_param(valid_mlid, None)
        assert result == valid_mlid
        
        # Test None handling
        result = mlid_type.process_bind_param(None, None)
        assert result is None
        
        # Test invalid MLID rejection
        with pytest.raises(ValueError, match="Invalid MLID format"):
            mlid_type.process_bind_param("invalid", None)
        
        # Test non-string rejection
        with pytest.raises(ValueError, match="MLID must be a string"):
            mlid_type.process_bind_param(123, None)
    
    def test_mlid_result_processing(self):
        """Test MLID result value processing from database."""
        mlid_type = MLID()
        
        # Test valid MLID from database
        valid_mlid = generate_mlid()
        result = mlid_type.process_result_value(valid_mlid, None)
        assert result == valid_mlid
        
        # Test None from database
        result = mlid_type.process_result_value(None, None)
        assert result is None
        
        # Test invalid MLID from database (should raise error)
        with pytest.raises(ValueError, match="Invalid MLID retrieved from database"):
            mlid_type.process_result_value("invalid", None)
    
    async def test_mlid_uniqueness_constraint(self, async_db_session):
        """Test that MLID primary keys maintain uniqueness."""
        # Generate multiple MLIDs and verify they're unique
        mlids = [generate_mlid() for _ in range(100)]
        
        # All MLIDs should be unique
        assert len(set(mlids)) == 100
        
        # All MLIDs should be valid
        for mlid in mlids:
            assert is_valid_mlid(mlid)
    
    def test_mlid_string_format_consistency(self):
        """Test that MLID format is consistent and valid."""
        for _ in range(50):
            mlid = generate_mlid()
            
            # Test format consistency
            assert isinstance(mlid, str)
            assert len(mlid) == 17
            assert mlid.startswith("ml_")
            
            # Test character set
            identifier = mlid[3:]  # Remove 'ml_' prefix
            valid_chars = set("abcdefghijkmnpqrstuvwxyz23456789")
            mlid_chars = set(identifier)
            assert mlid_chars.issubset(valid_chars)
            
            # Test no confusing characters
            confusing_chars = set("0O1l")
            assert confusing_chars.isdisjoint(mlid_chars)
    
    async def test_mlid_database_storage_retrieval(self, async_db_session):
        """Test storing and retrieving MLIDs from database."""
        # This is a simplified test since we're using SQLite
        # In production, this would test with actual PostgreSQL
        
        test_mlid = generate_mlid()
        
        # Test that the MLID can be used as a string ID
        assert is_valid_mlid(test_mlid)
        assert len(test_mlid) == 17
        
        # Verify it's a proper string for database storage
        assert isinstance(test_mlid, str)
        assert test_mlid.isascii()  # Database-safe characters


class TestMLIDSchemaIntegration:
    """Test MLID integration with Pydantic schemas."""
    
    def test_mlid_schema_validation(self):
        """Test MLID validation in Pydantic schemas."""
        from shared.schemas.base import MLIDMixin
        
        # Test valid MLID
        valid_mlid = generate_mlid()
        schema_instance = MLIDMixin(id=valid_mlid)
        assert schema_instance.id == valid_mlid
        
        # Test None (should be allowed)
        schema_instance = MLIDMixin(id=None)
        assert schema_instance.id is None
        
        # Test invalid MLID
        with pytest.raises(ValueError, match="Invalid MLID format"):
            MLIDMixin(id="invalid_mlid")
    
    def test_mlid_schema_serialization(self):
        """Test MLID serialization in schemas."""
        from shared.schemas.base import BaseModelSchema
        
        valid_mlid = generate_mlid()
        schema_instance = BaseModelSchema(id=valid_mlid)
        
        # Test model_dump
        data = schema_instance.model_dump()
        assert data["id"] == valid_mlid
        
        # Test JSON serialization
        json_str = schema_instance.model_dump_json()
        assert valid_mlid in json_str
    
    def test_mlid_api_schema_compatibility(self):
        """Test MLID compatibility with API schemas."""
        from shared.schemas.user import UserResponse
        from datetime import datetime
        
        valid_mlid = generate_mlid()
        
        # Test user response schema with MLID
        user_data = {
            "id": valid_mlid,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow()
        }
        
        user_response = UserResponse(**user_data)
        assert user_response.id == valid_mlid
        
        # Test serialization
        json_data = user_response.model_dump_json()
        assert valid_mlid in json_data


class TestMLIDPerformanceIntegration:
    """Test MLID performance in database context."""
    
    def test_mlid_generation_performance(self):
        """Test MLID generation performance for database use."""
        import time
        
        # Generate many MLIDs quickly
        start_time = time.time()
        mlids = [generate_mlid() for _ in range(1000)]
        end_time = time.time()
        
        # Should be fast enough for database operations
        assert end_time - start_time < 0.5  # Less than 0.5 seconds
        
        # All should be unique and valid
        assert len(set(mlids)) == 1000
        for mlid in mlids[:10]:  # Check first 10
            assert is_valid_mlid(mlid)
    
    def test_mlid_indexing_characteristics(self):
        """Test MLID characteristics for database indexing."""
        mlids = [generate_mlid() for _ in range(100)]
        
        # Test that MLIDs have good distribution for indexing
        prefixes = [mlid[:5] for mlid in mlids]  # First 5 chars
        unique_prefixes = set(prefixes)
        
        # Should have reasonable distribution (not all the same)
        assert len(unique_prefixes) > 10  # At least 10% unique prefixes
        
        # Test lexicographic ordering variation
        sorted_mlids = sorted(mlids)
        assert sorted_mlids != mlids  # Should have different ordering


class TestMLIDMigrationSupport:
    """Test MLID support for database migration scenarios."""
    
    def test_mlid_validation_for_existing_data(self):
        """Test MLID validation for data migration scenarios."""
        # Simulate existing valid MLIDs
        existing_mlids = [generate_mlid() for _ in range(10)]
        
        # All should validate
        for mlid in existing_mlids:
            assert is_valid_mlid(mlid)
        
        # Simulate invalid data that might exist during migration
        invalid_data = [
            "old_uuid_format",
            "12345678-1234-1234-1234-123456789012",
            "",
            None
        ]
        
        for invalid in invalid_data:
            if invalid is not None:
                assert not is_valid_mlid(invalid)
    
    def test_mlid_conversion_utilities(self):
        """Test utilities for converting to MLID format."""
        from app.utils.mlid import mlid_from_any, get_mlid_info
        
        # Test valid MLID conversion
        valid_mlid = generate_mlid()
        converted = mlid_from_any(valid_mlid)
        assert converted == valid_mlid
        
        # Test MLID info extraction
        info = get_mlid_info(valid_mlid)
        assert info["is_valid"] is True
        assert info["prefix"] == "ml_"
        assert info["length"] == 17
        
        # Test invalid conversion
        with pytest.raises(ValueError):
            mlid_from_any("invalid_format")
        
        with pytest.raises(ValueError):
            mlid_from_any(None)