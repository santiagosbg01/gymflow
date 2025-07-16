#!/usr/bin/env python3
"""
Test email functionality
"""
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gym_reservation import send_email_notification

def test_email():
    """Test email notification functionality"""
    print("📧 Testing Email Notification")
    print("=" * 40)
    
    # Test successful reservation email
    print("Sending test email...")
    
    subject = "🧪 Test Email - Gym Reservation System"
    body = f"""
    <html>
    <body>
        <h2>🧪 Email Test Successful!</h2>
        
        <p>This is a test email from your Gym Reservation System.</p>
        
        <p><strong>Test Details:</strong></p>
        <ul>
            <li><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li><strong>Recipient:</strong> santiago.sbg@gmail.com</li>
            <li><strong>Status:</strong> <span style="color: green;">✅ EMAIL WORKING</span></li>
        </ul>
        
        <p>If you received this email, your email notifications are configured correctly!</p>
        
        <hr>
        <p><small>This is a test message from your Gym Reservation System.</small></p>
    </body>
    </html>
    """
    
    try:
        send_email_notification(subject, body, True)
        print("✅ Test email sent successfully!")
        print("📬 Check your inbox at santiago.sbg@gmail.com")
        
    except Exception as e:
        print(f"❌ Test email failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file has correct EMAIL_USER and EMAIL_PASSWORD")
        print("2. Make sure you're using an App Password (not your regular password)")
        print("3. Verify 2-factor authentication is enabled on your Gmail account")
        print("4. Run 'python3 setup_email.py' for detailed setup instructions")
        
        return False
    
    return True

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1) 