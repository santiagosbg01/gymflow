#!/usr/bin/env python3
"""
Debug script to inspect the login page structure
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def debug_login_page():
    """Debug the login page structure"""
    print("🔍 Debugging login page...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome driver initialized")
        
        # Navigate to the main page
        driver.get("https://www.condomisoft.com")
        print("✅ Navigated to condomisoft.com")
        time.sleep(3)
        
        # Look for login link
        login_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Entrar') or contains(text(), 'Login') or contains(text(), 'Ingresar')]")
        print(f"Found {len(login_links)} login links")
        
        if login_links:
            print("Clicking login link...")
            login_links[0].click()
            time.sleep(3)
        
        # Check current URL
        print(f"Current URL: {driver.current_url}")
        
        # Look for all input fields
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(all_inputs)} input fields:")
        
        for i, inp in enumerate(all_inputs):
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or "no-name"
            input_id = inp.get_attribute("id") or "no-id"
            input_placeholder = inp.get_attribute("placeholder") or "no-placeholder"
            input_value = inp.get_attribute("value") or "no-value"
            
            print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}, Placeholder: {input_placeholder}, Value: {input_value}")
        
        # Look for all forms
        all_forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"\nFound {len(all_forms)} forms:")
        
        for i, form in enumerate(all_forms):
            form_action = form.get_attribute("action") or "no-action"
            form_method = form.get_attribute("method") or "GET"
            print(f"  {i+1}. Action: {form_action}, Method: {form_method}")
            
            # Look for inputs within this form
            form_inputs = form.find_elements(By.TAG_NAME, "input")
            print(f"    Inputs in form {i+1}: {len(form_inputs)}")
            for j, inp in enumerate(form_inputs):
                input_type = inp.get_attribute("type") or "text"
                input_name = inp.get_attribute("name") or "no-name"
                print(f"      {j+1}. Type: {input_type}, Name: {input_name}")
        
        # Check page source for password-related elements
        page_source = driver.page_source.lower()
        password_keywords = ["password", "clave", "contraseña", "pass"]
        
        print(f"\nPassword-related keywords found in page source:")
        for keyword in password_keywords:
            count = page_source.count(keyword)
            if count > 0:
                print(f"  '{keyword}': {count} occurrences")
        
        # Look for specific elements we expect
        usuario_fields = driver.find_elements(By.NAME, "usuario")
        clave_fields = driver.find_elements(By.NAME, "clave")
        password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        
        print(f"\nSpecific field searches:")
        print(f"  Fields with name='usuario': {len(usuario_fields)}")
        print(f"  Fields with name='clave': {len(clave_fields)}")
        print(f"  Fields with type='password': {len(password_fields)}")
        
        # Wait for user to inspect the page
        print("\n⏳ Waiting 10 seconds for manual inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            print("Driver closed")
    
    return True

if __name__ == "__main__":
    debug_login_page() 