#!/usr/bin/env python3
"""
Script to fix template spintax by updating the message text with spintax patterns.
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database, get_session
from app.models import MessageTemplate
from sqlmodel import select


def fix_template_spintax():
    """Fix template spintax by updating message text with spintax patterns."""
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    
    try:
        # Updated templates with spintax in message text
        template_updates = {
            "Welcome Message": {
                "body": "Hello {name|friend|valued customer}! Welcome to {company|our platform|our service}. We're {excited|thrilled|delighted} to have you on board. If you have any questions, feel free to reach out to us at {email}.",
                "spintax_text": "Hello {name|buddy|pal}! Welcome to {company|our team|us}. We're {happy|glad|pleased} to have you here. Contact us at {email} if you need help."
            },
            "Marketing Campaign": {
                "body": "Hi {name|friend|customer}! Don't miss out on our {special|amazing|exclusive} offer. Get {20%|25%|30%} off your first order with code {WELCOME20|SAVE20|DISCOUNT20}. Visit our {website|store|platform} to learn more!",
                "spintax_text": "Hey {name|buddy|valued client}! Check out our {limited|flash|hot} deal. Save {15%|20%|25%} with code {PROMO|DEAL|SAVE}. Shop now at {our site|our store|our website}!"
            },
            "Appointment Reminder": {
                "body": "Hello {name|friend|valued client}, this is a {friendly|gentle|important} reminder that you have an appointment scheduled for {date} at {time}. Please let us know if you need to {reschedule|change|modify} your appointment.",
                "spintax_text": "Hi {name|buddy|client}, just a quick reminder about your {upcoming|scheduled} appointment on {date} at {time}. Contact us to {reschedule|change|update} if needed."
            },
            "Newsletter": {
                "body": "Hi {name|friend|valued subscriber}! Here's your {weekly|monthly|quarterly} update from {company|our team|us}. We have some {exciting|amazing|fantastic} news and updates to share with you. Check out our {latest|newest|recent} blog post and don't forget to follow us on social media!",
                "spintax_text": "Hello {name|buddy|subscriber}! Your {weekly|monthly} newsletter from {company|us} is here. We've got {great|wonderful|awesome} updates to share. Read our {new|latest|fresh} blog post and follow us online!"
            },
            "Thank You Message": {
                "body": "Thank you {name|valued customer|friend} for choosing {company|our service|us}! We {appreciate|value|are grateful for} your business and look forward to {serving|helping|assisting} you again. If you have any {feedback|suggestions|comments}, please don't hesitate to contact us.",
                "spintax_text": "Thanks {name|buddy|customer} for choosing {company|our business|us}! We {love|appreciate|value} having you as a customer. Feel free to {reach out|contact us|get in touch} with any {questions|feedback|thoughts}."
            },
            "Event Invitation": {
                "body": "Hello {name|friend|colleague}! You're invited to our {upcoming|special|exclusive} event on {date}. Join us for an evening of {networking|learning|fun|celebration}. RSVP by {rsvp_date} to {secure|reserve|book} your spot!",
                "spintax_text": "Hi {name|buddy|friend}! Don't miss our {special|amazing|exciting} event on {date}. It's going to be a {great|wonderful|fantastic} time! RSVP by {rsvp_date} to {join|attend|participate}."
            },
            "Password Reset": {
                "body": "Hi {name|valued user|account holder}, we received a {request|notification} to reset your password. Click the {link|button|link below} to reset your password: {reset_link}. If you didn't request this, please {ignore|disregard|delete} this message.",
                "spintax_text": "Hello {name|user|account owner}, someone requested to reset your password. Use this {link|button} to reset: {reset_link}. If this wasn't you, please {ignore|delete|disregard} this message."
            },
            "Order Confirmation": {
                "body": "Thank you {name|valued customer|friend} for your order! Your order #{order_number} has been {confirmed|processed|received} and will be {processed|shipped|sent} within {1-2|2-3|3-5} business days. You'll receive {tracking information|shipping details|delivery updates} once it ships.",
                "spintax_text": "Thanks {name|buddy|customer} for ordering! Order #{order_number} is {confirmed|ready|processed} and will {ship|be sent|go out} in {1-2|2-3} days. We'll send {tracking|shipping|delivery} info when it ships."
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
                # Update message text with spintax patterns
                template.body = updates["body"]
                template.spintax_text = updates["spintax_text"]
                template.use_spintax = True
                
                # Update the template in the database
                session.add(template)
                updated_count += 1
                print(f"Updated template: {template_name}")
                print(f"  Message: {updates['body'][:50]}...")
                print(f"  Spintax: {updates['spintax_text'][:50]}...")
            else:
                print(f"Template not found: {template_name}")
        
        # Commit changes
        session.commit()
        print(f"\nSuccessfully updated {updated_count} templates with spintax in message text!")
        
    except Exception as e:
        print(f"Error updating templates: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    fix_template_spintax()
