#!/usr/bin/env python3
"""
Test script for cloud WebDriver functionality
Tests both Chrome and Firefox drivers
"""

import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chrome_driver():
    """Test Chrome driver initialization"""
    logger.info("Testing Chrome driver...")
    
    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Try different ChromeDriver paths
        driver_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/app/chromedriver'
        ]
        
        driver = None
        for path in driver_paths:
            if os.path.exists(path):
                try:
                    service = ChromeService(path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info(f"✅ Chrome driver works with: {path}")
                    break
                except Exception as e:
                    logger.warning(f"❌ Chrome driver failed at {path}: {e}")
                    continue
        
        if not driver:
            try:
                chrome_driver_path = ChromeDriverManager().install()
                service = ChromeService(chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"✅ Chrome driver works with WebDriverManager: {chrome_driver_path}")
            except Exception as e:
                logger.error(f"❌ WebDriverManager Chrome failed: {e}")
                return False
        
        # Test basic functionality
        driver.get("https://www.google.com")
        title = driver.title
        logger.info(f"✅ Chrome driver successfully loaded Google with title: {title}")
        driver.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Chrome driver test failed: {e}")
        return False

def test_firefox_driver():
    """Test Firefox driver initialization"""
    logger.info("Testing Firefox driver...")
    
    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        
        # Try different GeckoDriver paths
        driver_paths = [
            '/usr/local/bin/geckodriver',
            '/usr/bin/geckodriver',
            '/app/geckodriver'
        ]
        
        driver = None
        for path in driver_paths:
            if os.path.exists(path):
                try:
                    service = FirefoxService(path)
                    driver = webdriver.Firefox(service=service, options=firefox_options)
                    logger.info(f"✅ Firefox driver works with: {path}")
                    break
                except Exception as e:
                    logger.warning(f"❌ Firefox driver failed at {path}: {e}")
                    continue
        
        if not driver:
            try:
                gecko_driver_path = GeckoDriverManager().install()
                service = FirefoxService(gecko_driver_path)
                driver = webdriver.Firefox(service=service, options=firefox_options)
                logger.info(f"✅ Firefox driver works with WebDriverManager: {gecko_driver_path}")
            except Exception as e:
                logger.error(f"❌ WebDriverManager Firefox failed: {e}")
                return False
        
        # Test basic functionality
        driver.get("https://www.google.com")
        title = driver.title
        logger.info(f"✅ Firefox driver successfully loaded Google with title: {title}")
        driver.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Firefox driver test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting WebDriver tests...")
    
    chrome_works = test_chrome_driver()
    firefox_works = test_firefox_driver()
    
    logger.info("\n📊 Test Results:")
    logger.info(f"Chrome Driver: {'✅ WORKS' if chrome_works else '❌ FAILED'}")
    logger.info(f"Firefox Driver: {'✅ WORKS' if firefox_works else '❌ FAILED'}")
    
    if chrome_works or firefox_works:
        logger.info("🎉 At least one driver works - cloud version should be functional!")
        return 0
    else:
        logger.error("💥 All drivers failed - cloud version needs fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 