#!/usr/bin/env python3
"""
Test script to verify template spintax is working correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database, get_session
from app.models import MessageTemplate
from app.core.spintax import SpintaxProcessor
from sqlmodel import select


def test_template_spintax():
    """Test spintax functionality with actual templates."""
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    
    try:
        # Get all templates
        templates = session.exec(select(MessageTemplate)).all()
        
        processor = SpintaxProcessor()
        
        print("Testing Template Spintax Functionality")
        print("=" * 60)
        
        for i, template in enumerate(templates, 1):
            print(f"\n{i}. {template.name}")
            print(f"   Description: {template.description}")
            print(f"   Use Spintax: {template.use_spintax}")
            
            if template.use_spintax and template.body:
                print(f"   Message Text: {template.body[:80]}...")
                
                # Test validation
                validation = processor.validate_spintax(template.body)
                print(f"   Valid: {validation['valid']}")
                print(f"   Patterns: {validation['patterns_count']}")
                print(f"   Variants: {validation['variants_count']}")
                
                if validation['errors']:
                    print(f"   Errors: {validation['errors']}")
                if validation['warnings']:
                    print(f"   Warnings: {validation['warnings']}")
                
                # Test processing
                result = processor.process(template.body)
                print(f"   Processed: {result.text[:80]}...")
                
                # Test preview samples
                samples = processor.get_preview_samples(template.body, count=3)
                print(f"   Preview samples:")
                for j, sample in enumerate(samples, 1):
                    print(f"     {j}. {sample[:60]}...")
                
                if validation['patterns_count'] > 0:
                    print(f"   ✅ Spintax working correctly")
                else:
                    print(f"   ❌ No spintax patterns found")
            else:
                print(f"   ⚠️  Spintax not enabled or no message text")
        
        print("\n" + "=" * 60)
        print("Template spintax test completed!")
        
    except Exception as e:
        print(f"Error testing templates: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    test_template_spintax()
