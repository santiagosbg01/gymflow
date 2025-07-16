#!/usr/bin/env python3
"""
Email setup helper script
"""

def setup_email():
    """Guide user through email setup"""
    print("📧 Email Notification Setup")
    print("=" * 40)
    
    print("\n📝 To receive email notifications, you need to:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password for this script")
    print("3. Update the .env file with your email credentials")
    
    print("\n🔧 Step-by-step instructions:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification if not already enabled")
    print("3. Go to https://myaccount.google.com/apppasswords")
    print("4. Generate a new App Password for 'Gym Reservation Script'")
    print("5. Copy the 16-character password (no spaces)")
    
    print("\n✏️  Edit your .env file:")
    print("   EMAIL_USER=your_email@gmail.com")
    print("   EMAIL_PASSWORD=your_16_character_app_password")
    
    print("\n⚠️  Important:")
    print("   - Use your Gmail address for EMAIL_USER")
    print("   - Use the App Password (not your regular password)")
    print("   - Keep your App Password secure")
    
    print("\n🧪 Test your email setup:")
    print("   python3 test_email.py")
    
    print("\n✅ Email notifications will be sent to: santiago.sbg@gmail.com")

if __name__ == "__main__":
    setup_email() 