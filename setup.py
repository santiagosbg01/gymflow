#!/usr/bin/env python3
"""
Setup script for the gym reservation automation
"""
import os
import sys
import subprocess
import shutil

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def setup_config():
    """Setup configuration file"""
    print("Setting up configuration...")
    
    if not os.path.exists(".env"):
        if os.path.exists("config.env"):
            shutil.copy("config.env", ".env")
            print("✅ Created .env file from config.env")
        else:
            # Create .env file with template
            with open(".env", "w") as f:
                f.write("CONDOMISOFT_USERNAME=your_username_here\n")
                f.write("CONDOMISOFT_PASSWORD=your_password_here\n")
            print("✅ Created .env file template")
    else:
        print("✅ .env file already exists")
    
    # Check if credentials are set
    with open(".env", "r") as f:
        content = f.read()
        if "your_username_here" in content or "your_password_here" in content:
            print("⚠️  Please edit .env file and set your actual credentials")
            return False
    
    return True

def check_chrome():
    """Check if Chrome is installed"""
    print("Checking for Chrome browser...")
    
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Linux (Chromium)
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Windows
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    print("⚠️  Chrome browser not found. Please install Google Chrome.")
    return False

def main():
    """Main setup function"""
    print("🏋️  Gym Reservation Automation Setup")
    print("=" * 40)
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Setup configuration
    if not setup_config():
        success = False
    
    # Check Chrome
    if not check_chrome():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your actual credentials")
        print("2. Test the script: python gym_reservation.py")
        print("3. Run daily automation: python gym_reservation.py")
    else:
        print("❌ Setup completed with warnings. Please address the issues above.")
    
    return success

if __name__ == "__main__":
    main() 