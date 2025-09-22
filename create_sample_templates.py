#!/usr/bin/env python3
"""
Script to create sample message templates for the application.
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database, get_session
from app.models import MessageTemplate


def create_sample_templates():
    """Create sample message templates."""
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    
    try:
        # Sample templates
        templates = [
            {
                "name": "Welcome Message",
                "description": "Welcome new users to our service",
                "message_text": "Hello {name}! Welcome to {company}. We're excited to have you on board. If you have any questions, feel free to reach out to us at {email}.",
                "use_spintax": False,
                "spintax_example": None,
                "tags": ["welcome", "onboarding", "greeting"]
            },
            {
                "name": "Marketing Campaign",
                "description": "Promotional message for marketing campaigns",
                "message_text": "Hi {name}! Don't miss out on our special offer. Get 20% off your first order with code WELCOME20. Visit our website to learn more!",
                "use_spintax": True,
                "spintax_example": "Hi {name|friend|customer}! Don't miss out on our {special|amazing|exclusive} offer. Get {20%|25%|30%} off your first order!",
                "tags": ["marketing", "promotion", "discount"]
            },
            {
                "name": "Appointment Reminder",
                "description": "Remind users about upcoming appointments",
                "message_text": "Hello {name}, this is a reminder that you have an appointment scheduled for {date} at {time}. Please let us know if you need to reschedule.",
                "use_spintax": False,
                "spintax_example": None,
                "tags": ["reminder", "appointment", "scheduling"]
            },
            {
                "name": "Newsletter",
                "description": "Weekly newsletter template",
                "message_text": "Hi {name}! Here's your weekly update from {company}. We have some exciting news and updates to share with you. Check out our latest blog post and don't forget to follow us on social media!",
                "use_spintax": True,
                "spintax_example": "Hi {name|friend|valued customer}! Here's your {weekly|monthly|quarterly} update from {company|our team|us}. We have some {exciting|amazing|fantastic} news to share!",
                "tags": ["newsletter", "update", "communication"]
            },
            {
                "name": "Thank You Message",
                "description": "Thank users for their business",
                "message_text": "Thank you {name} for choosing {company}! We appreciate your business and look forward to serving you again. If you have any feedback, please don't hesitate to contact us.",
                "use_spintax": False,
                "spintax_example": None,
                "tags": ["thank you", "gratitude", "follow-up"]
            },
            {
                "name": "Event Invitation",
                "description": "Invite users to events",
                "message_text": "Hello {name}! You're invited to our upcoming event on {date}. Join us for an evening of networking and fun. RSVP by {rsvp_date} to secure your spot!",
                "use_spintax": True,
                "spintax_example": "Hello {name|friend|colleague}! You're invited to our {upcoming|special|exclusive} event on {date}. Join us for an evening of {networking|learning|fun}!",
                "tags": ["event", "invitation", "networking"]
            },
            {
                "name": "Password Reset",
                "description": "Password reset instructions",
                "message_text": "Hi {name}, we received a request to reset your password. Click the link below to reset your password: {reset_link}. If you didn't request this, please ignore this message.",
                "use_spintax": False,
                "spintax_example": None,
                "tags": ["security", "password", "reset"]
            },
            {
                "name": "Order Confirmation",
                "description": "Confirm order placement",
                "message_text": "Thank you {name} for your order! Your order #{order_number} has been confirmed and will be processed within 1-2 business days. You'll receive tracking information once it ships.",
                "use_spintax": False,
                "spintax_example": None,
                "tags": ["order", "confirmation", "shipping"]
            }
        ]
        
        # Create templates
        created_count = 0
        for template_data in templates:
            # Check if template already exists
            from sqlmodel import select
            existing = session.exec(
                select(MessageTemplate).where(MessageTemplate.name == template_data["name"])
            ).first()
            
            if not existing:
                template = MessageTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    body=template_data["message_text"],
                    use_spintax=template_data["use_spintax"],
                    spintax_text=template_data["spintax_example"]
                )
                
                # Set tags
                template.set_tags_list(template_data["tags"])
                
                session.add(template)
                created_count += 1
                print(f"Created template: {template_data['name']}")
            else:
                print(f"Template already exists: {template_data['name']}")
        
        # Commit changes
        session.commit()
        print(f"\nSuccessfully created {created_count} sample templates!")
        
    except Exception as e:
        print(f"Error creating sample templates: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    create_sample_templates()
