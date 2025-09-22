"""
Unit tests for spintax processing.
"""

import pytest
from app.core.spintax import SpintaxProcessor


class TestSpintaxProcessor:
    """Test spintax processor functionality."""
    
    def test_simple_spintax(self):
        """Test simple spintax processing."""
        processor = SpintaxProcessor()
        text = "Hello {John|Jane|User}"
        result = processor.process(text)
        
        assert result.text in ["Hello John", "Hello Jane", "Hello User"]
        assert result.variants_count == 3
        assert len(result.variables_used) == 3
    
    def test_multiple_spintax(self):
        """Test multiple spintax patterns."""
        processor = SpintaxProcessor()
        text = "Hello {John|Jane}, welcome to {our|the} service!"
        result = processor.process(text)
        
        assert "Hello" in result.text
        assert "welcome to" in result.text
        assert "service!" in result.text
        assert result.variants_count == 4  # 2 * 2
    
    def test_nested_spintax_warning(self):
        """Test nested spintax validation."""
        processor = SpintaxProcessor()
        text = "Hello {John|{Jane|User}}"
        
        validation = processor.validate_spintax(text)
        assert not validation["valid"]
        assert len(validation["warnings"]) > 0
    
    def test_empty_variants(self):
        """Test empty variants handling."""
        processor = SpintaxProcessor()
        text = "Hello {|Jane|User}"
        
        validation = processor.validate_spintax(text)
        assert not validation["valid"]
        assert len(validation["errors"]) > 0
    
    def test_no_spintax(self):
        """Test text without spintax."""
        processor = SpintaxProcessor()
        text = "Hello World"
        result = processor.process(text)
        
        assert result.text == "Hello World"
        assert result.variants_count == 1
        assert len(result.variables_used) == 0
    
    def test_preview_samples(self):
        """Test preview samples generation."""
        processor = SpintaxProcessor()
        text = "Hello {John|Jane|User}"
        samples = processor.get_preview_samples(text, 5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.startswith("Hello ")
            assert sample.split()[1] in ["John", "Jane", "User"]
    
    def test_seed_reproducibility(self):
        """Test that seed produces reproducible results."""
        processor1 = SpintaxProcessor(seed=42)
        processor2 = SpintaxProcessor(seed=42)
        
        text = "Hello {John|Jane|User}"
        result1 = processor1.process(text)
        result2 = processor2.process(text)
        
        assert result1.text == result2.text
