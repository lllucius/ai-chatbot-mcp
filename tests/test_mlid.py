"""Tests for MLID utilities and functionality.

Comprehensive test suite for Machine Learning ID generation, validation,
and usage across the application.
"""

import pytest
import re
from unittest.mock import patch

from app.utils.mlid import (
    generate_mlid,
    is_valid_mlid,
    validate_mlid,
    mlid_from_any,
    get_mlid_info,
    MLID_PREFIX,
    MLID_TOTAL_LENGTH,
    MLID_PATTERN,
    MLID_ALPHABET,
    MLID_ID_LENGTH,
)


class TestMLIDGeneration:
    """Test MLID generation functionality."""

    def test_generate_mlid_format(self):
        """Test that generated MLIDs have correct format."""
        mlid = generate_mlid()
        
        assert isinstance(mlid, str)
        assert len(mlid) == MLID_TOTAL_LENGTH
        assert mlid.startswith(MLID_PREFIX)
        assert MLID_PATTERN.match(mlid)

    def test_generate_mlid_uniqueness(self):
        """Test that generated MLIDs are unique."""
        mlids = {generate_mlid() for _ in range(1000)}
        
        # All MLIDs should be unique
        assert len(mlids) == 1000

    def test_generate_mlid_alphabet(self):
        """Test that generated MLIDs only use allowed characters."""
        mlid = generate_mlid()
        identifier = mlid[len(MLID_PREFIX):]
        
        for char in identifier:
            assert char in MLID_ALPHABET

    def test_generate_mlid_no_confusing_chars(self):
        """Test that generated MLIDs don't contain confusing characters."""
        # Generate many MLIDs to increase probability of hitting all chars
        for _ in range(100):
            mlid = generate_mlid()
            identifier = mlid[len(MLID_PREFIX):]
            
            # Should not contain confusing characters: 0, O, 1, l
            assert '0' not in identifier
            assert 'O' not in identifier
            assert '1' not in identifier
            assert 'l' not in identifier


class TestMLIDValidation:
    """Test MLID validation functionality."""

    def test_is_valid_mlid_valid_cases(self):
        """Test validation of valid MLIDs."""
        valid_mlids = [
            generate_mlid(),
            "ml_a2b3c4d5e6f7g8",
            "ml_23456789abcdef",
            "ml_zyxwvutsrqpmnk",
        ]
        
        for mlid in valid_mlids:
            assert is_valid_mlid(mlid), f"Should be valid: {mlid}"

    def test_is_valid_mlid_invalid_cases(self):
        """Test validation of invalid MLIDs."""
        invalid_cases = [
            # Wrong prefix
            "ai_a2b3c4d5e6f7g8",
            "mla2b3c4d5e6f7g8",
            
            # Wrong length
            "ml_a2b3c4d5e6f7g",  # too short
            "ml_a2b3c4d5e6f7g89",  # too long
            "ml_",  # no identifier
            
            # Invalid characters
            "ml_a2b3c4d5e6f7g0",  # contains 0
            "ml_a2b3c4d5e6f7gO",  # contains O
            "ml_a2b3c4d5e6f7g1",  # contains 1
            "ml_a2b3c4d5e6f7gl",  # contains l
            "ml_a2b3c4d5e6f7g!",  # contains special char
            
            # Not strings
            None,
            123,
            [],
            {},
            True,
        ]
        
        for invalid in invalid_cases:
            assert not is_valid_mlid(invalid), f"Should be invalid: {invalid}"

    def test_validate_mlid_success(self):
        """Test successful MLID validation."""
        valid_mlid = generate_mlid()
        result = validate_mlid(valid_mlid)
        assert result == valid_mlid

    def test_validate_mlid_failure(self):
        """Test MLID validation failures."""
        invalid_mlids = [
            "invalid",
            "ml_invalid",
            "ai_a2b3c4d5e6f7g8",
        ]
        
        for invalid in invalid_mlids:
            with pytest.raises(ValueError, match="Invalid MLID format"):
                validate_mlid(invalid)

    def test_mlid_from_any_success(self):
        """Test successful conversion from various types."""
        valid_mlid = generate_mlid()
        
        result = mlid_from_any(valid_mlid)
        assert result == valid_mlid

    def test_mlid_from_any_failure(self):
        """Test conversion failures."""
        invalid_cases = [
            None,
            123,
            "invalid",
            [],
            {},
        ]
        
        for invalid in invalid_cases:
            with pytest.raises(ValueError):
                mlid_from_any(invalid)


class TestMLIDInfo:
    """Test MLID information functionality."""

    def test_get_mlid_info_valid(self):
        """Test getting info for valid MLID."""
        mlid = generate_mlid()
        info = get_mlid_info(mlid)
        
        assert info["is_valid"] is True
        assert info["prefix"] == MLID_PREFIX
        assert info["identifier"] == mlid[len(MLID_PREFIX):]
        assert info["length"] == MLID_TOTAL_LENGTH
        assert info["alphabet_used"] == MLID_ALPHABET
        assert info["expected_length"] == MLID_TOTAL_LENGTH

    def test_get_mlid_info_invalid(self):
        """Test getting info for invalid MLID."""
        invalid_mlid = "invalid"
        info = get_mlid_info(invalid_mlid)
        
        assert info["is_valid"] is False
        assert info["length"] == len(invalid_mlid)
        assert info["expected_length"] == MLID_TOTAL_LENGTH


class TestMLIDConstants:
    """Test MLID constants and configuration."""

    def test_mlid_constants(self):
        """Test that MLID constants are correctly defined."""
        assert MLID_PREFIX == "ml_"
        assert MLID_ID_LENGTH == 14
        assert MLID_TOTAL_LENGTH == 17
        assert len(MLID_ALPHABET) == 32

    def test_mlid_alphabet_safety(self):
        """Test that MLID alphabet excludes confusing characters."""
        confusing_chars = {'0', 'O', '1', 'l'}
        alphabet_set = set(MLID_ALPHABET)
        
        assert confusing_chars.isdisjoint(alphabet_set)

    def test_mlid_pattern(self):
        """Test that MLID regex pattern works correctly."""
        valid_mlid = generate_mlid()
        assert MLID_PATTERN.match(valid_mlid)
        
        invalid_cases = [
            "ai_a2b3c4d5e6f7g8",  # wrong prefix
            "ml_a2b3c4d5e6f7g",   # too short
            "ml_a2b3c4d5e6f7g89", # too long
        ]
        
        for invalid in invalid_cases:
            assert not MLID_PATTERN.match(invalid)


class TestMLIDSecurity:
    """Test MLID security properties."""

    def test_mlid_entropy(self):
        """Test that MLIDs have sufficient entropy."""
        # Generate many MLIDs and check distribution
        mlids = [generate_mlid() for _ in range(1000)]
        
        # All should be unique (high entropy)
        assert len(set(mlids)) == 1000
        
        # Character distribution should be roughly even
        char_counts = {}
        for mlid in mlids:
            identifier = mlid[len(MLID_PREFIX):]
            for char in identifier:
                char_counts[char] = char_counts.get(char, 0) + 1
        
        # Should have used most characters in the alphabet
        assert len(char_counts) > len(MLID_ALPHABET) * 0.8

    def test_mlid_non_sequential(self):
        """Test that MLIDs are not sequential."""
        mlids = [generate_mlid() for _ in range(10)]
        
        # MLIDs should not follow any obvious pattern
        for i in range(1, len(mlids)):
            # Simple check: consecutive MLIDs should differ significantly
            prev_id = mlids[i-1][len(MLID_PREFIX):]
            curr_id = mlids[i][len(MLID_PREFIX):]
            
            # Count differing positions
            diff_count = sum(a != b for a, b in zip(prev_id, curr_id))
            
            # Should differ in most positions (not sequential)
            assert diff_count > MLID_ID_LENGTH // 2

    @patch('app.utils.mlid.secrets.choice')
    def test_mlid_uses_secure_random(self, mock_choice):
        """Test that MLID generation uses cryptographically secure randomness."""
        mock_choice.side_effect = list("a2b3c4d5e6f7g8")
        
        mlid = generate_mlid()
        
        # Should have called secrets.choice for each character
        assert mock_choice.call_count == MLID_ID_LENGTH
        assert mlid == "ml_a2b3c4d5e6f7g8"


class TestMLIDPerformance:
    """Test MLID performance characteristics."""

    def test_generation_performance(self):
        """Test that MLID generation is fast."""
        import time
        
        start_time = time.time()
        mlids = [generate_mlid() for _ in range(1000)]
        end_time = time.time()
        
        # Should generate 1000 MLIDs in reasonable time
        assert end_time - start_time < 1.0  # Less than 1 second
        assert len(set(mlids)) == 1000  # All unique

    def test_validation_performance(self):
        """Test that MLID validation is fast."""
        import time
        
        mlids = [generate_mlid() for _ in range(1000)]
        
        start_time = time.time()
        results = [is_valid_mlid(mlid) for mlid in mlids]
        end_time = time.time()
        
        # Should validate 1000 MLIDs in reasonable time
        assert end_time - start_time < 0.1  # Less than 0.1 seconds
        assert all(results)  # All should be valid