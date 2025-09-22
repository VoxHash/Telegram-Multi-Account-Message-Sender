#!/usr/bin/env python3
"""
Test script to verify spintax functionality is working correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.spintax import SpintaxProcessor


def test_spintax_functionality():
    """Test spintax functionality with various examples."""
    
    processor = SpintaxProcessor()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple spintax",
            "text": "Hello {friend|buddy|pal}!",
            "expected_variants": 3
        },
        {
            "name": "Multiple spintax patterns",
            "text": "Get {20%|25%|30%} off your {first|next} order with code {SAVE20|DISCOUNT20|WELCOME20}",
            "expected_variants": 3 * 2 * 3  # 18 variants
        },
        {
            "name": "Mixed variables and spintax",
            "text": "Hi {name}! Welcome to {company|our platform|our service}. We're {excited|thrilled|delighted} to have you on board.",
            "expected_variants": 3 * 3  # 9 variants
        },
        {
            "name": "No spintax patterns",
            "text": "Hello {name}! Welcome to {company}.",
            "expected_variants": 1
        },
        {
            "name": "Empty spintax pattern",
            "text": "Hello {|friend|buddy}!",
            "expected_variants": 3
        }
    ]
    
    print("Testing Spintax Functionality")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Text: {test_case['text']}")
        
        # Test validation
        validation = processor.validate_spintax(test_case['text'])
        print(f"   Valid: {validation['valid']}")
        print(f"   Patterns found: {validation['patterns_count']}")
        print(f"   Variants count: {validation['variants_count']}")
        
        if validation['errors']:
            print(f"   Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"   Warnings: {validation['warnings']}")
        
        # Test processing
        result = processor.process(test_case['text'])
        print(f"   Processed: {result.text}")
        print(f"   Variables used: {result.variables_used}")
        print(f"   Variants count: {result.variants_count}")
        
        # Test preview samples
        samples = processor.get_preview_samples(test_case['text'], count=5)
        print(f"   Preview samples:")
        for j, sample in enumerate(samples, 1):
            print(f"     {j}. {sample}")
        
        # Check if variants count matches expected
        if result.variants_count == test_case['expected_variants']:
            print(f"   ✅ Variants count correct: {result.variants_count}")
        else:
            print(f"   ❌ Variants count incorrect: expected {test_case['expected_variants']}, got {result.variants_count}")
    
    print("\n" + "=" * 50)
    print("Spintax functionality test completed!")


if __name__ == "__main__":
    test_spintax_functionality()
