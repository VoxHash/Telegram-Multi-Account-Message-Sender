#!/usr/bin/env python3
"""
Script to update existing message templates with enhanced spintax examples.
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database, get_session
from app.models import MessageTemplate
from sqlmodel import select


def update_templates_spintax():
    """Update existing templates with enhanced spintax examples."""
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    
    try:
        # Enhanced spintax examples for existing templates
        template_updates = {
            "Welcome Message": {
                "use_spintax": True,
                "spintax_text": "Hello {name|friend|valued customer}! Welcome to {company|our platform|our service}. We're {excited|thrilled|delighted} to have you on board. If you have any questions, feel free to reach out to us at {email}."
            },
            "Marketing Campaign": {
                "use_spintax": True,
                "spintax_text": "Hi {name|friend|customer}! Don't miss out on our {special|amazing|exclusive} offer. Get {20%|25%|30%} off your first order with code {WELCOME20|SAVE20|DISCOUNT20}. Visit our {website|store|platform} to learn more!"
            },
            "Appointment Reminder": {
                "use_spintax": True,
                "spintax_text": "Hello {name|friend|valued client}, this is a {friendly|gentle|important} reminder that you have an appointment scheduled for {date} at {time}. Please let us know if you need to {reschedule|change|modify} your appointment."
            },
            "Newsletter": {
                "use_spintax": True,
                "spintax_text": "Hi {name|friend|valued subscriber}! Here's your {weekly|monthly|quarterly} update from {company|our team|us}. We have some {exciting|amazing|fantastic} news and updates to share with you. Check out our {latest|newest|recent} blog post and don't forget to follow us on social media!"
            },
            "Thank You Message": {
                "use_spintax": True,
                "spintax_text": "Thank you {name|valued customer|friend} for choosing {company|our service|us}! We {appreciate|value|are grateful for} your business and look forward to {serving|helping|assisting} you again. If you have any {feedback|suggestions|comments}, please don't hesitate to contact us."
            },
            "Event Invitation": {
                "use_spintax": True,
                "spintax_text": "Hello {name|friend|colleague}! You're invited to our {upcoming|special|exclusive} event on {date}. Join us for an evening of {networking|learning|fun|celebration}. RSVP by {rsvp_date} to {secure|reserve|book} your spot!"
            },
            "Password Reset": {
                "use_spintax": True,
                "spintax_text": "Hi {name|valued user|account holder}, we received a {request|notification} to reset your password. Click the {link|button|link below} to reset your password: {reset_link}. If you didn't request this, please {ignore|disregard|delete} this message."
            },
            "Order Confirmation": {
                "use_spintax": True,
                "spintax_text": "Thank you {name|valued customer|friend} for your order! Your order #{order_number} has been {confirmed|processed|received} and will be {processed|shipped|sent} within {1-2|2-3|3-5} business days. You'll receive {tracking information|shipping details|delivery updates} once it ships."
            }
        }
        
        # Update templates
        updated_count = 0
        for template_name, updates in template_updates.items():
            # Find existing template
            template = session.exec(
                select(MessageTemplate).where(MessageTemplate.name == template_name)
            ).first()
            
            if template:
                # Update spintax settings
                template.use_spintax = updates["use_spintax"]
                template.spintax_text = updates["spintax_text"]
                
                # Update the template in the database
                session.add(template)
                updated_count += 1
                print(f"Updated template: {template_name}")
            else:
                print(f"Template not found: {template_name}")
        
        # Commit changes
        session.commit()
        print(f"\nSuccessfully updated {updated_count} templates with enhanced spintax examples!")
        
    except Exception as e:
        print(f"Error updating templates: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    update_templates_spintax()
