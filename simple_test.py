#!/usr/bin/env python3
"""
Simple test to debug Chrome driver issues
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_chrome_driver():
    """Test basic Chrome driver functionality"""
    print("Testing Chrome driver...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    
    try:
        # Try to initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome driver initialized successfully")
        
        # Test with a simple page first
        print("Testing with Google...")
        driver.get("https://www.google.com")
        print("✅ Successfully loaded Google")
        
        time.sleep(3)
        
        # Now test with the target site
        print("Testing with condomisoft...")
        driver.get("https://www.condomisoft.com")
        print("✅ Successfully loaded condomisoft")
        
        time.sleep(5)
        
        # Check page title
        print(f"Page title: {driver.title}")
        
        # Look for login elements
        login_elements = driver.find_elements(By.NAME, "usuario")
        if login_elements:
            print("✅ Found login form")
        else:
            print("⚠️  No login form found")
            
        # Check for any forms
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"Found {len(forms)} forms on the page")
        
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            print("Driver closed")
    
    return True

if __name__ == "__main__":
    success = test_chrome_driver()
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed") 