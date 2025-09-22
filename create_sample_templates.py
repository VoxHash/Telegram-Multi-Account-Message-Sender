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
        # Sample templates with enhanced spintax examples
        templates = [
            {
                "name": "Welcome Message",
                "description": "Welcome new users to our service",
                "message_text": "Hello {name}! Welcome to {company}. We're excited to have you on board. If you have any questions, feel free to reach out to us at {email}.",
                "use_spintax": True,
                "spintax_example": "Hello {name|friend|valued customer}! Welcome to {company|our platform|our service}. We're {excited|thrilled|delighted} to have you on board. If you have any questions, feel free to reach out to us at {email}.",
                "tags": ["welcome", "onboarding", "greeting"]
            },
            {
                "name": "Marketing Campaign",
                "description": "Promotional message for marketing campaigns",
                "message_text": "Hi {name}! Don't miss out on our special offer. Get 20% off your first order with code WELCOME20. Visit our website to learn more!",
                "use_spintax": True,
                "spintax_example": "Hi {name|friend|customer}! Don't miss out on our {special|amazing|exclusive} offer. Get {20%|25%|30%} off your first order with code {WELCOME20|SAVE20|DISCOUNT20}. Visit our {website|store|platform} to learn more!",
                "tags": ["marketing", "promotion", "discount"]
            },
            {
                "name": "Appointment Reminder",
                "description": "Remind users about upcoming appointments",
                "message_text": "Hello {name}, this is a reminder that you have an appointment scheduled for {date} at {time}. Please let us know if you need to reschedule.",
                "use_spintax": True,
                "spintax_example": "Hello {name|friend|valued client}, this is a {friendly|gentle|important} reminder that you have an appointment scheduled for {date} at {time}. Please let us know if you need to {reschedule|change|modify} your appointment.",
                "tags": ["reminder", "appointment", "scheduling"]
            },
            {
                "name": "Newsletter",
                "description": "Weekly newsletter template",
                "message_text": "Hi {name}! Here's your weekly update from {company}. We have some exciting news and updates to share with you. Check out our latest blog post and don't forget to follow us on social media!",
                "use_spintax": True,
                "spintax_example": "Hi {name|friend|valued subscriber}! Here's your {weekly|monthly|quarterly} update from {company|our team|us}. We have some {exciting|amazing|fantastic} news and updates to share with you. Check out our {latest|newest|recent} blog post and don't forget to follow us on social media!",
                "tags": ["newsletter", "update", "communication"]
            },
            {
                "name": "Thank You Message",
                "description": "Thank users for their business",
                "message_text": "Thank you {name} for choosing {company}! We appreciate your business and look forward to serving you again. If you have any feedback, please don't hesitate to contact us.",
                "use_spintax": True,
                "spintax_example": "Thank you {name|valued customer|friend} for choosing {company|our service|us}! We {appreciate|value|are grateful for} your business and look forward to {serving|helping|assisting} you again. If you have any {feedback|suggestions|comments}, please don't hesitate to contact us.",
                "tags": ["thank you", "gratitude", "follow-up"]
            },
            {
                "name": "Event Invitation",
                "description": "Invite users to events",
                "message_text": "Hello {name}! You're invited to our upcoming event on {date}. Join us for an evening of networking and fun. RSVP by {rsvp_date} to secure your spot!",
                "use_spintax": True,
                "spintax_example": "Hello {name|friend|colleague}! You're invited to our {upcoming|special|exclusive} event on {date}. Join us for an evening of {networking|learning|fun|celebration}. RSVP by {rsvp_date} to {secure|reserve|book} your spot!",
                "tags": ["event", "invitation", "networking"]
            },
            {
                "name": "Password Reset",
                "description": "Password reset instructions",
                "message_text": "Hi {name}, we received a request to reset your password. Click the link below to reset your password: {reset_link}. If you didn't request this, please ignore this message.",
                "use_spintax": True,
                "spintax_example": "Hi {name|valued user|account holder}, we received a {request|notification} to reset your password. Click the {link|button|link below} to reset your password: {reset_link}. If you didn't request this, please {ignore|disregard|delete} this message.",
                "tags": ["security", "password", "reset"]
            },
            {
                "name": "Order Confirmation",
                "description": "Confirm order placement",
                "message_text": "Thank you {name} for your order! Your order #{order_number} has been confirmed and will be processed within 1-2 business days. You'll receive tracking information once it ships.",
                "use_spintax": True,
                "spintax_example": "Thank you {name|valued customer|friend} for your order! Your order #{order_number} has been {confirmed|processed|received} and will be {processed|shipped|sent} within {1-2|2-3|3-5} business days. You'll receive {tracking information|shipping details|delivery updates} once it ships.",
                "tags": ["order", "confirmation", "shipping"]
            },
            {
                "name": "Follow-up Message",
                "description": "Follow up with customers after purchase",
                "message_text": "Hi {name}, we hope you're enjoying your recent purchase from {company}. We'd love to hear your feedback and see how we can improve our service.",
                "use_spintax": True,
                "spintax_example": "Hi {name|friend|valued customer}, we hope you're {enjoying|loving|pleased with} your recent purchase from {company|our store|us}. We'd {love|appreciate|value} to hear your {feedback|thoughts|opinions} and see how we can {improve|enhance|better} our service.",
                "tags": ["follow-up", "feedback", "customer service"]
            },
            {
                "name": "Holiday Greeting",
                "description": "Holiday season greetings",
                "message_text": "Happy Holidays {name}! Wishing you and your family a wonderful holiday season. Thank you for being a valued customer of {company}.",
                "use_spintax": True,
                "spintax_example": "Happy {Holidays|Christmas|New Year} {name|friend|valued customer}! Wishing you and your {family|loved ones|friends} a {wonderful|joyful|magical} holiday season. Thank you for being a {valued|loyal|cherished} customer of {company|our business|us}.",
                "tags": ["holiday", "greeting", "seasonal"]
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
