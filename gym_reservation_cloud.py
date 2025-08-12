import os
import time
import logging
from datetime import datetime, timedelta
import calendar
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from dotenv import load_dotenv
import schedule
import pytz
from typing import Optional, Union

# Load environment variables
load_dotenv()

# Set up logging with cloud-friendly format
import os
log_dir = '/app/logs' if os.path.exists('/app') else './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'gym_reservation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GymReservationCloud:
    def __init__(self):
        self.driver: Optional[Union[webdriver.Chrome, webdriver.Firefox]] = None
        self.wait: Optional[WebDriverWait] = None
        self.driver_type: Optional[str] = None
        self.username = os.getenv('CONDOMISOFT_USERNAME')
        self.password = os.getenv('CONDOMISOFT_PASSWORD')
        self.base_url = "https://www.condomisoft.com"
        self.login_url = "https://www.condomisoft.com/system/login.php?sin_apps=true&plataforma="
        self.reservation_url = "https://www.condomisoft.com/system/detalle_recursos.php?id_recurso=1780&nombre_recurso=GIMNASIO%20CUARTO%20PILATES%20Y%20%20SAL%C3%93N%20AEROBI"
        
        # Time slots to try - both main early morning slots
        self.time_slots = ["07:30-08:00", "08:00-08:30"]
        
        # Results tracking
        self.reservation_results = {
            "07:30-08:00": {"success": False, "message": ""},
            "08:00-08:30": {"success": False, "message": ""}
        }
        
        if not self.username or not self.password:
            logger.error("Username and password must be set in environment variables")
            raise ValueError("Missing credentials")
    
    def setup_chrome_driver(self):
        """Set up Chrome WebDriver with cloud-optimized options"""
        try:
            chrome_options = ChromeOptions()
            
            # Essential options for cloud deployment
            # Only use headless mode in cloud/CI environments
            if os.getenv('GITHUB_ACTIONS') == 'true' or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER'):
                chrome_options.add_argument("--headless")
            else:
                logger.info("Running in local mode - browser window will be visible for debugging")
            # Core stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Cloud-specific optimizations (only in production)
            if os.getenv('GITHUB_ACTIONS') == 'true' or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER'):
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
            
            # Anti-detection options
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set Chrome binary path for macOS
            if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            # Additional stability options
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Try different ChromeDriver paths
            driver_paths = [
                '/usr/local/bin/chromedriver',
                '/usr/bin/chromedriver',
                '/app/chromedriver'
            ]
            
            for path in driver_paths:
                if os.path.exists(path):
                    try:
                        service = ChromeService(path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.info(f"Chrome driver initialized successfully using: {path}")
                        self.driver_type = "chrome"
                        return True
                    except Exception as e:
                        logger.warning(f"Chrome driver failed at {path}: {e}")
                        continue
            
            # Try WebDriverManager as fallback with error handling
            try:
                chrome_driver_path = ChromeDriverManager().install()
                # Fix the path if WebDriverManager returns wrong file
                if 'THIRD_PARTY_NOTICES' in chrome_driver_path:
                    import glob
                    # Find the actual chromedriver binary in the same directory
                    driver_dir = os.path.dirname(chrome_driver_path)
                    possible_drivers = glob.glob(os.path.join(driver_dir, '**/chromedriver*'), recursive=True)
                    actual_driver = None
                    for driver_path in possible_drivers:
                        if os.path.isfile(driver_path) and 'chromedriver' in os.path.basename(driver_path) and 'THIRD_PARTY' not in driver_path:
                            actual_driver = driver_path
                            break
                    if actual_driver and os.path.exists(actual_driver):
                        chrome_driver_path = actual_driver
                        logger.info(f"Fixed WebDriverManager path to: {chrome_driver_path}")
                        # Fix permissions if needed
                        import stat
                        if not os.access(chrome_driver_path, os.X_OK):
                            os.chmod(chrome_driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                            logger.info("Fixed chromedriver permissions")
                
                service = ChromeService(chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"Chrome driver initialized using WebDriverManager: {chrome_driver_path}")
                self.driver_type = "chrome"
                return True
            except Exception as e:
                logger.warning(f"WebDriverManager Chrome failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            return False
    
    def setup_firefox_driver(self):
        """Set up Firefox WebDriver as fallback"""
        try:
            firefox_options = FirefoxOptions()
            
            # Essential options for cloud deployment
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            firefox_options.add_argument("--disable-gpu")
            firefox_options.add_argument("--window-size=1920,1080")
            
            # Set preferences
            firefox_options.set_preference("general.useragent.override", 
                                         "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0")
            firefox_options.set_preference("dom.webdriver.enabled", False)
            firefox_options.set_preference("useAutomationExtension", False)
            
            # Try different GeckoDriver paths
            driver_paths = [
                '/usr/local/bin/geckodriver',
                '/usr/bin/geckodriver',
                '/app/geckodriver'
            ]
            
            for path in driver_paths:
                if os.path.exists(path):
                    try:
                        service = FirefoxService(path)
                        self.driver = webdriver.Firefox(service=service, options=firefox_options)
                        logger.info(f"Firefox driver initialized successfully using: {path}")
                        self.driver_type = "firefox"
                        return True
                    except Exception as e:
                        logger.warning(f"Firefox driver failed at {path}: {e}")
                        continue
            
            # Try WebDriverManager as fallback
            try:
                gecko_driver_path = GeckoDriverManager().install()
                service = FirefoxService(gecko_driver_path)
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
                logger.info(f"Firefox driver initialized using WebDriverManager: {gecko_driver_path}")
                self.driver_type = "firefox"
                return True
            except Exception as e:
                logger.warning(f"WebDriverManager Firefox failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Firefox driver: {str(e)}")
            return False
    
    def setup_driver(self):
        """Set up WebDriver with fallback options"""
        logger.info("Initializing WebDriver...")
        
        # Try Chrome first
        if self.setup_chrome_driver():
            logger.info("Successfully initialized Chrome driver")
        # Try Firefox as fallback
        elif self.setup_firefox_driver():
            logger.info("Successfully initialized Firefox driver as fallback")
        else:
            logger.error("Failed to initialize any WebDriver")
            raise Exception("Could not initialize WebDriver with Chrome or Firefox")
        
        # Ensure driver is initialized before setting timeouts
        if self.driver is None:
            raise Exception("Driver is None after initialization")
        
        # Set timeouts
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)
        
        logger.info(f"WebDriver initialized successfully using {self.driver_type}")

    def login(self):
        """Login to the condomisoft system"""
        try:
            assert self.driver is not None, "Driver must be initialized before login"
            assert self.wait is not None, "Wait must be initialized before login"
            
            logger.info("Navigating to login page")
            self.driver.get(self.login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're already logged in by looking for logout link or user info
            if self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Salir') or contains(text(), 'Logout')]"):
                logger.info("Already logged in")
                return
            
            # Look for login form fields with fallback logic
            username_field = None
            password_field = None
            
            # Try to find username field - first try correct name, then fallback
            username_elements = self.driver.find_elements(By.NAME, "usuario")
            if not username_elements:
                username_elements = self.driver.find_elements(By.NAME, "user")
            if not username_elements:
                username_elements = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email']")
            
            if username_elements:
                username_field = username_elements[0]
                logger.info("Found username field")
            else:
                logger.error("No username field found")
                raise Exception("Username field not found")
            
            # Try to find password field - first try correct name, then fallback
            password_elements = self.driver.find_elements(By.NAME, "clave")
            if not password_elements:
                password_elements = self.driver.find_elements(By.NAME, "pass")
            if not password_elements:
                password_elements = self.driver.find_elements(By.XPATH, "//input[@type='password']")
            
            if password_elements:
                password_field = password_elements[0]
                logger.info("Found password field")
            else:
                logger.error("No password field found")
                raise Exception("Password field not found")
            
            # Enter credentials
            logger.info("Entering credentials...")
            username_field.clear()
            username_field.send_keys(self.username)
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit login form with multiple fallback options
            submit_buttons = self.driver.find_elements(By.XPATH, "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Entrar')]")
            if submit_buttons:
                submit_buttons[0].click()
                logger.info("Login form submitted")
            else:
                # Try pressing Enter on password field
                password_field.send_keys("\n")
                logger.info("Submitted login by pressing Enter")
            
            # Wait for login to process
            time.sleep(5)
            
            # Check for successful login (redirect or presence of logout link)
            current_url = self.driver.current_url
            if current_url != self.login_url or self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Salir') or contains(text(), 'Logout')]"):
                logger.info("Login successful")
            else:
                logger.warning("Login may have failed - checking for error messages")
                # Check for error messages
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'incorrecto') or contains(text(), 'invalid')]")
                if error_elements:
                    logger.error(f"Login error: {error_elements[0].text}")
                    raise Exception(f"Login failed: {error_elements[0].text}")
                else:
                    logger.warning("No clear error message found, but login may have failed")
                    raise Exception("Login failed - unknown error")
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            # Let's take a screenshot for debugging
            try:
                self.driver.save_screenshot('/tmp/selenium_login_error.png')
                logger.info("Screenshot saved to /tmp/selenium_login_error.png")
            except:
                pass
            raise

    def select_apartment(self):
        """Select the G-502 apartment from the dashboard"""
        try:
            assert self.driver is not None, "Driver must be initialized"
            
            logger.info("Selecting apartment G-502")
            
            # Wait for the condominium list to load
            time.sleep(3)
            
            # Look for the G-502 button (it should be in the "Vivienda" column)
            # The button text might have spaces like "G - 502"
            g502_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'G') and contains(text(), '502')] | //a[contains(text(), 'G') and contains(text(), '502')]")
            
            if not g502_buttons:
                # Try looking in the FLOW building row for G-502
                g502_buttons = self.driver.find_elements(By.XPATH, "//tr[contains(., 'FLOW')]//button[contains(text(), 'G') and contains(text(), '502')] | //tr[contains(., 'FLOW')]//a[contains(text(), 'G') and contains(text(), '502')]")
            
            if not g502_buttons:
                # Try looking for any element containing G and 502
                g502_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'G') and contains(text(), '502')]")
            
            if g502_buttons:
                # Make sure it's clickable
                clickable_element = g502_buttons[0]
                if clickable_element.tag_name not in ['button', 'a']:
                    # Look for clickable parent or child
                    parent_clickable = clickable_element.find_elements(By.XPATH, ".//button | .//a | ./ancestor::button | ./ancestor::a")
                    if parent_clickable:
                        clickable_element = parent_clickable[0]
                
                clickable_element.click()
                logger.info("Successfully clicked G-502 apartment button")
                
                # Wait for the apartment selection to process
                time.sleep(3)
                
            else:
                logger.warning("G-502 button not found - checking available options")
                # Log all table rows for debugging
                rows = self.driver.find_elements(By.XPATH, "//tr")
                logger.info(f"Found {len(rows)} table rows")
                
                for i, row in enumerate(rows[:10]):  # Show first 10 rows
                    row_text = row.text.replace('\n', ' | ')
                    logger.info(f"  Row {i}: {row_text}")
                
                # Look for any buttons in the table
                all_buttons = self.driver.find_elements(By.XPATH, "//button | //a[contains(@class, 'btn')]")
                logger.info(f"Found {len(all_buttons)} buttons:")
                for i, btn in enumerate(all_buttons[:5]):
                    logger.info(f"  Button {i}: {btn.text}")
                
                raise Exception("G-502 apartment button not found")
                
        except Exception as e:
            logger.error(f"Failed to select apartment: {str(e)}")
            raise

    def navigate_to_reservation(self):
        """Navigate to gym reservation page"""
        try:
            # Navigate to the gym reservation page
            reservation_url = "https://www.condomisoft.com/system/detalle_recursos.php?id_recurso=1780&nombre_recurso=GIMNASIO%20CUARTO%20PILATES%20Y%20%20SAL%C3%93N%20AEROBI"
            
            logger.info(f"Navigating to reservation page: {reservation_url}")
            self.driver.get(reservation_url)
            
            # Wait for page to load with explicit wait instead of sleep
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Successfully navigated to reservation page")
            
        except Exception as e:
            logger.error(f"Failed to navigate to reservation page: {str(e)}")
            raise

    def get_target_date(self):
        """Calculate the target reservation date for the FOLLOWING week's gym day.

        Requirements:
        - When running Sunday/Tuesday/Thursday at ~23:30, target is the next day (Mon/Wed/Fri) PLUS 7 days.
        - When running at 00:00–06:00 on Mon/Wed/Fri (post-midnight), target is the SAME weekday plus 7 days.
        - For ad-hoc daytime runs, target is next week's same weekday.
        """
        mexico_tz = pytz.timezone('America/Mexico_City')
        now = datetime.now(mexico_tz)

        current_weekday = now.weekday()  # Monday=0, ... Sunday=6
        current_hour = now.hour

        # Determine the base day we want to reserve FOR (this week or next) before adding +7
        if current_hour >= 23:
            # Night before: base is tomorrow (e.g., Sun->Mon, Tue->Wed, Thu->Fri)
            base_day = now + timedelta(days=1)
        elif 0 <= current_hour < 6:
            # Early morning of gym day: base is today (e.g., Mon/Wed/Fri)
            base_day = now
        else:
            # Daytime/manual run: base is today (we'll roll to next gym day if needed)
            base_day = now

        # Find the next gym day relative to base_day (including today if it is a gym day)
        gym_days = [0, 2, 4]  # Mon, Wed, Fri
        days_until_next_gym = min(((d - base_day.weekday()) % 7) for d in gym_days)
        next_gym_day = base_day + timedelta(days=days_until_next_gym)

        # Target is the same weekday in the FOLLOWING week
        target_date = next_gym_day + timedelta(days=7)

        logger.info(f"Current time (Mexico City): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Computed base day: {base_day.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Next gym day (this week): {next_gym_day.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Target reservation date (following week): {target_date.strftime('%Y-%m-%d (%A)')}")

        return target_date

    def select_calendar_day(self):
        """Select the next occurrence of the same day of the week from the calendar"""
        try:
            assert self.driver is not None, "Driver must be initialized"
            
            target_date = self.get_target_date()
            target_day = target_date.day
            target_month = target_date.month
            target_year = target_date.year
            
            # Get current month/year from system
            current_date = datetime.now(pytz.timezone('America/Mexico_City'))
            current_month = current_date.month
            current_year = current_date.year
            
            logger.info(f"Looking for day {target_day} in {target_date.strftime('%B %Y')} (target: {target_month}/{target_year}, current: {current_month}/{current_year})")
            
            # Wait for calendar to load
            time.sleep(1)  # Reduced from 2
            
            # Navigate to the correct month if needed
            months_to_advance = 0
            if target_year > current_year:
                months_to_advance = (target_year - current_year) * 12 + (target_month - current_month)
            elif target_year == current_year and target_month > current_month:
                months_to_advance = target_month - current_month
            
            # Click the >> button to advance months if necessary
            for i in range(months_to_advance):
                try:
                    next_month_button = self.driver.find_element(By.XPATH, "//a[contains(text(), '>>') or contains(@onclick, 'next') or contains(@title, 'next')]")
                    next_month_button.click()
                    logger.info(f"Advanced calendar to next month (step {i+1}/{months_to_advance})")
                    time.sleep(0.5)  # Reduced from 1
                except Exception as e:
                    logger.warning(f"Could not advance to next month (step {i+1}): {str(e)}")
                    # Try alternative selectors for next month button
                    try:
                        # Try looking for >> symbol or similar navigation
                        next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), '>') or contains(text(), 'siguiente') or contains(text(), 'next')]")
                        if next_buttons:
                            next_buttons[-1].click()  # Usually the >> button is the last one
                            logger.info(f"Advanced calendar using alternative selector (step {i+1}/{months_to_advance})")
                            time.sleep(0.5)  # Reduced from 1
                        else:
                            logger.error(f"No next month button found for step {i+1}")
                            break
                    except Exception as e2:
                        logger.error(f"Failed to find any next month button: {str(e2)}")
                        break
            
            # Wait for calendar to update after navigation
            if months_to_advance > 0:
                time.sleep(1)  # Reduced from 2
            
            # Look for available days (green highlighted days in the calendar)
            available_days = self.driver.find_elements(By.XPATH, "//td[contains(@style, 'background-color: #90EE90') or contains(@style, 'background-color: green') or contains(@class, 'available')]")
            
            if not available_days:
                # Try looking for clickable calendar cells that contain numbers
                available_days = self.driver.find_elements(By.XPATH, "//td[@onclick and text() and string-length(text()) <= 2 and text() != ' ']")
            
            if not available_days:
                # Try looking for any clickable day numbers in the calendar
                available_days = self.driver.find_elements(By.XPATH, "//td[text() and @onclick and not(contains(@class, 'disabled'))]")
            
            if available_days:
                # Log available days for debugging
                logger.info(f"Found {len(available_days)} available days in the correct month")
                for i, day in enumerate(available_days[:10]):  # Show first 10 days
                    logger.info(f"  Day {i}: {day.text}")
                
                # Look for the specific target day (try both single digit and zero-padded)
                target_day_element = None
                target_day_str = str(target_day)
                target_day_padded = f"{target_day:02d}"  # Zero-padded (e.g., "08")
                
                for day_element in available_days:
                    day_text = day_element.text.strip()
                    if day_text == target_day_str or day_text == target_day_padded:
                        target_day_element = day_element
                        logger.info(f"Found target day: '{day_text}' matches target {target_day}")
                        break
                
                if target_day_element:
                    target_day_element.click()
                    logger.info(f"Selected calendar day: {target_day} in {target_date.strftime('%B %Y')}")
                    
                    # Wait for the day selection to process
                    time.sleep(1)  # Reduced from 3
                    
                    # Check if we got the "7 days in advance" error
                    if self.check_and_handle_advance_error():
                        return True
                    
                    return True
                else:
                    logger.warning(f"Target day {target_day} not found in available days for {target_date.strftime('%B %Y')}")
                    # Fall back to selecting the first available day
                    available_days[0].click()
                    logger.info(f"Selected fallback day: {available_days[0].text} in {target_date.strftime('%B %Y')}")
                    time.sleep(1)  # Reduced from 3
                    
                    # Check if we got the "7 days in advance" error
                    if self.check_and_handle_advance_error():
                        return True
                    
                    return True
            else:
                logger.warning(f"No available days found in calendar for {target_date.strftime('%B %Y')}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to select calendar day: {str(e)}")
            return False

    def check_and_handle_advance_error(self):
        """Check for the '7 days in advance' error message and handle it"""
        try:
            assert self.driver is not None, "Driver must be initialized"
            
            # Check if we're on the apology page with the error message
            current_url = self.driver.current_url
            if "apology.php" in current_url and "m%C3%A1s%20de%207%20d%C3%ADas" in current_url:
                logger.warning("Detected '7 days in advance' error - trying to return and select correct date")
                
                # Click the "Regresar" button
                regresar_button = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Regresar')] | //button[contains(text(), 'Regresar')]")
                if regresar_button:
                    regresar_button[0].click()
                    logger.info("Clicked 'Regresar' button")
                    time.sleep(2)
                    
                    # Return to reservation page and try again with correct date
                    self.navigate_to_reservation()
                    return self.select_calendar_day_with_retry()
                else:
                    logger.error("Could not find 'Regresar' button")
                    return False
            
            # Check for the error message in the page content
            error_message_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'No se acepta reservaciones con más de 7 días')] | //p[contains(text(), 'No se acepta reservaciones con más de 7 días')] | //*[contains(text(), 'No se acepta reservaciones con más de 7 días')]")
            
            if error_message_elements:
                logger.warning("Found '7 days in advance' error message on page")
                
                # Look for and click "Regresar" button
                regresar_button = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Regresar')] | //button[contains(text(), 'Regresar')]")
                if regresar_button:
                    regresar_button[0].click()
                    logger.info("Clicked 'Regresar' button")
                    time.sleep(2)
                    
                    # Return to reservation page and try again with correct date
                    self.navigate_to_reservation()
                    return self.select_calendar_day_with_retry()
                else:
                    logger.error("Could not find 'Regresar' button")
                    return False
            
            return True  # No error found, continue normally
            
        except Exception as e:
            logger.error(f"Error checking for advance error: {str(e)}")
            return False

    def select_calendar_day_with_retry(self):
        """Retry selecting the calendar day using the same target date logic."""
        try:
            target_date = self.get_target_date()
            target_day = target_date.day
            target_month = target_date.month
            target_year = target_date.year

            # Current month/year (Mexico City)
            now = datetime.now(pytz.timezone('America/Mexico_City'))
            current_month = now.month
            current_year = now.year

            logger.info(f"Retry: Looking for day {target_day} in {target_date.strftime('%B %Y')} (following week's {target_date.strftime('%A')})")
            
            # Wait for calendar to load
            time.sleep(1)  # Reduced from 2
            
            # Navigate to the correct month if needed
            months_to_advance = 0
            if target_year > current_year:
                months_to_advance = (target_year - current_year) * 12 + (target_month - current_month)
            elif target_year == current_year and target_month > current_month:
                months_to_advance = target_month - current_month
            
            # Click the >> button to advance months if necessary
            for i in range(months_to_advance):
                try:
                    next_month_button = self.driver.find_element(By.XPATH, "//a[contains(text(), '>>') or contains(@onclick, 'next') or contains(@title, 'next')]")
                    next_month_button.click()
                    logger.info(f"Retry: Advanced calendar to next month (step {i+1}/{months_to_advance})")
                    time.sleep(0.5)  # Reduced from 1
                except Exception as e:
                    logger.warning(f"Retry: Could not advance to next month (step {i+1}): {str(e)}")
                    # Try alternative selectors for next month button
                    try:
                        next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), '>') or contains(text(), 'siguiente') or contains(text(), 'next')]")
                        if next_buttons:
                            next_buttons[-1].click()  # Usually the >> button is the last one
                            logger.info(f"Retry: Advanced calendar using alternative selector (step {i+1}/{months_to_advance})")
                            time.sleep(0.5)  # Reduced from 1
                        else:
                            logger.error(f"Retry: No next month button found for step {i+1}")
                            break
                    except Exception as e2:
                        logger.error(f"Retry: Failed to find any next month button: {str(e2)}")
                        break
            
            # Wait for calendar to update after navigation
            if months_to_advance > 0:
                time.sleep(1)  # Reduced from 2
            
            # Look for available days
            available_days = self.driver.find_elements(By.XPATH, "//td[contains(@style, 'background-color: #90EE90') or contains(@style, 'background-color: green') or contains(@class, 'available')]")
            
            if not available_days:
                available_days = self.driver.find_elements(By.XPATH, "//td[@onclick and text() and string-length(text()) <= 2 and text() != ' ']")
            
            if not available_days:
                available_days = self.driver.find_elements(By.XPATH, "//td[text() and @onclick and not(contains(@class, 'disabled'))]")
            
            if available_days:
                # Log available days for debugging
                logger.info(f"Retry: Found {len(available_days)} available days in the correct month")
                for i, day in enumerate(available_days[:10]):  # Show first 10 days
                    logger.info(f"  Retry Day {i}: {day.text}")
                
                # Look for the specific target day (try both single digit and zero-padded)
                target_day_element = None
                target_day_str = str(target_day)
                target_day_padded = f"{target_day:02d}"  # Zero-padded (e.g., "08")
                
                for day_element in available_days:
                    day_text = day_element.text.strip()
                    if day_text == target_day_str or day_text == target_day_padded:
                        target_day_element = day_element
                        logger.info(f"Retry: Found target day: '{day_text}' matches target {target_day}")
                        break
                
                if target_day_element:
                    target_day_element.click()
                    logger.info(f"Retry: Selected calendar day: {target_day} in {target_date.strftime('%B %Y')}")
                    time.sleep(1)  # Reduced from 3
                    return True
                else:
                    logger.warning(f"Retry: Target day {target_day} not found in {target_date.strftime('%B %Y')}, selecting first available day")
                    available_days[0].click()
                    logger.info(f"Retry: Selected fallback day: {available_days[0].text} in {target_date.strftime('%B %Y')}")
                    time.sleep(1)  # Reduced from 3
                    return True
            else:
                logger.warning(f"Retry: No available days found in calendar for {target_date.strftime('%B %Y')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to select calendar day with retry: {str(e)}")
            return False

    def reserve_time_slot(self, time_slot):
        """Reserve a specific time slot"""
        try:
            logger.info(f"Attempting to reserve {time_slot} slot")
            
            # Look for the specific time slot in the table
            # First try to find by exact text match
            time_buttons = self.driver.find_elements(By.XPATH, f"//td[contains(text(), '{time_slot}')]//following-sibling::td//button[contains(text(), 'Disponible')]")
            
            if not time_buttons:
                # Try finding the "Disponible" button in the same row as the time
                time_buttons = self.driver.find_elements(By.XPATH, f"//td[text()='{time_slot}']//following-sibling::td//button | //td[text()='{time_slot}']//following-sibling::td//a")
            
            if not time_buttons:
                # Try finding any clickable element with "Disponible" text
                time_buttons = self.driver.find_elements(By.XPATH, f"//tr[contains(., '{time_slot}')]//button[contains(text(), 'Disponible')] | //tr[contains(., '{time_slot}')]//a[contains(text(), 'Disponible')]")
            
            if not time_buttons:
                # Fallback: look for any clickable element containing the time
                time_buttons = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{time_slot}') and (@onclick or @href)]")
            
            if time_buttons:
                # Click the first available button
                self.driver.execute_script("arguments[0].scrollIntoView(true);", time_buttons[0])
                time.sleep(0.5)  # Reduced from 1
                time_buttons[0].click()
                
                # Wait for confirmation or next step
                time.sleep(1)  # Reduced from 3
                
                # Check if we got the "7 days in advance" error after clicking
                if not self.check_and_handle_advance_error():
                    return False
                
                # Look for confirmation button
                confirm_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirmar') or contains(text(), 'Reservar') or contains(text(), 'Aceptar')]")
                if confirm_buttons:
                    confirm_buttons[0].click()
                    logger.info(f"Clicked confirmation button for {time_slot} slot")
                    time.sleep(1)  # Reduced from 3
                    
                    # Check if we got the "7 days in advance" error after confirmation
                    if not self.check_and_handle_advance_error():
                        return False
                else:
                    logger.info(f"Reservation for {time_slot} initiated (no confirmation button found)")
                    time.sleep(1)  # Reduced from 2
                    
                    # Check if we got the "7 days in advance" error
                    if not self.check_and_handle_advance_error():
                        return False
                    
            else:
                logger.warning(f"No available slot found for {time_slot}")
                return False
                
            return True
                
        except Exception as e:
            logger.error(f"Failed to reserve {time_slot} slot: {str(e)}")
            raise

    def validate_reservation(self, time_slot):
        """Validate that the reservation was successful by checking the time slot status"""
        try:
            logger.info(f"Validating reservation for {time_slot}")
            
            # Refresh the page to get the latest status
            self.driver.refresh()
            time.sleep(1)  # Reduced from 3
            
            # Check if the time slot shows "Confirmado para G-502"
            confirmed_elements = self.driver.find_elements(By.XPATH, f"//tr[contains(., '{time_slot}')]//td[contains(text(), 'Confirmado para G-502')]")
            
            if confirmed_elements:
                logger.info(f"✅ Reservation confirmed! {time_slot} shows 'Confirmado para G-502'")
                return True, "Confirmed successfully"
            
            # Check if there's still a "Disponible" button (means reservation failed)
            available_buttons = self.driver.find_elements(By.XPATH, f"//tr[contains(., '{time_slot}')]//button[contains(text(), 'Disponible')] | //tr[contains(., '{time_slot}')]//a[contains(text(), 'Disponible')]")
            
            if available_buttons:
                logger.warning(f"❌ Reservation failed! {time_slot} still shows 'Disponible' button")
                return False, "Time slot still available - reservation not successful"
            
            # Check for any other status in the time slot
            time_slot_row = self.driver.find_elements(By.XPATH, f"//tr[contains(., '{time_slot}')]")
            if time_slot_row:
                row_text = time_slot_row[0].text
                logger.info(f"Time slot row content: {row_text}")
                
                # Check if it shows any other confirmation status
                if "Confirmado" in row_text:
                    if "G-502" not in row_text:
                        logger.warning(f"❌ Time slot confirmed for different apartment: {row_text}")
                        return False, f"Time slot confirmed for different apartment"
                    else:
                        logger.info(f"✅ Reservation confirmed for G-502")
                        return True, "Confirmed successfully"
                
                # Check for other statuses
                if "Ocupado" in row_text or "Reservado" in row_text:
                    logger.warning(f"❌ Time slot occupied by another user: {row_text}")
                    return False, "Time slot occupied by another user"
                
                logger.warning(f"❌ Unexpected status for time slot: {row_text}")
                return False, f"Unexpected status: {row_text}"
            
            logger.warning(f"❌ Could not find time slot {time_slot} in the table")
            return False, "Time slot not found in table"
            
        except Exception as e:
            logger.error(f"Failed to validate reservation: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def make_reservations(self):
        """Main function to make both reservations"""
        try:
            self.setup_driver()
            if not self.driver:
                raise Exception("Failed to initialize driver")
                
            self.login()
            self.select_apartment()
            self.navigate_to_reservation()
            
            # Select the next occurrence of the same day of the week
            if not self.select_calendar_day():
                logger.warning("Failed to select target day from calendar")
                return
            
            # Try each time slot until we get one successful reservation
            for time_slot in self.time_slots:
                logger.info(f"Attempting to reserve {time_slot}")
                
                try:
                    reservation_attempted = self.reserve_time_slot(time_slot)
                    
                    if reservation_attempted:
                        # Validate the reservation was successful
                        validation_success, validation_message = self.validate_reservation(time_slot)
                        
                        if validation_success:
                            logger.info(f"✅ {time_slot} reservation validated successfully: {validation_message}")
                            self.reservation_results[time_slot]["success"] = True
                            self.reservation_results[time_slot]["message"] = validation_message
                        else:
                            logger.error(f"❌ {time_slot} reservation validation failed: {validation_message}")
                            self.reservation_results[time_slot]["success"] = False
                            self.reservation_results[time_slot]["message"] = validation_message
                    else:
                        logger.error(f"❌ Failed to attempt {time_slot} reservation")
                        self.reservation_results[time_slot]["success"] = False
                        self.reservation_results[time_slot]["message"] = "Failed to find available time slot"
                        
                except Exception as e:
                    logger.error(f"❌ Exception during {time_slot} reservation: {str(e)}")
                    self.reservation_results[time_slot]["success"] = False
                    self.reservation_results[time_slot]["message"] = f"Exception: {str(e)}"
                
                # Brief pause between reservations
                time.sleep(1)  # Reduced from 2
            
            logger.info(f"Reservation process completed for both early morning time slots")
            
            # Log results for both slots
            successful_slots = [slot for slot, result in self.reservation_results.items() if result["success"]]
            failed_slots = [slot for slot, result in self.reservation_results.items() if not result["success"]]
            
            logger.info(f"✅ Successful reservations: {successful_slots if successful_slots else 'None'}")
            logger.info(f"❌ Failed reservations: {failed_slots if failed_slots else 'None'}")
            
            # Check if at least one reservation was successful
            any_success = any(result["success"] for result in self.reservation_results.values())
            if not any_success:
                raise Exception(f"Both early morning reservations failed - no available slots found")
            
        except Exception as e:
            logger.error(f"Reservation process failed: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed")

def send_email_notification(subject, body, success=True):
    """Send email notification with reservation results"""
    try:
        # Get email configuration from environment
        email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.getenv('EMAIL_PORT', '587'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        email_to = os.getenv('EMAIL_TO', 'santiago.sbg@gmail.com')
        
        if not email_user or not email_password:
            logger.warning("Email credentials not configured. Skipping email notification.")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'html'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()  # Enable security
        server.login(email_user, email_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(email_user, email_to, text)
        server.quit()
        
        logger.info(f"Email notification sent successfully to {email_to}")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")

def run_cloud_reservation():
    """Function to run the cloud reservation"""
    # Use Mexico City timezone
    mexico_tz = pytz.timezone('America/Mexico_City')
    start_time = datetime.now(mexico_tz)
    success = False
    error_message = ""
    target_date = ""
    reservation_results = {}
    reservation = None
    
    try:
        logger.info("Starting cloud reservation process")
        reservation = GymReservationCloud()
        
        # Get target date info for email
        target_date_obj = reservation.get_target_date()
        target_date = target_date_obj.strftime('%A, %B %d, %Y')
        
        reservation.make_reservations()
        
        # Check the actual reservation status from validation
        success = any(result["success"] for result in reservation.reservation_results.values())
        reservation_results = reservation.reservation_results
        
        if success:
            logger.info("Cloud reservation completed successfully (at least one slot reserved)")
        else:
            logger.error("Cloud reservation failed: Both time slots failed")
            
    except Exception as e:
        success = False
        error_message = str(e)
        logger.error(f"Cloud reservation failed: {error_message}")
    
    finally:
        # Send email notification
        end_time = datetime.now(mexico_tz)
        duration = end_time - start_time
        
        # Determine email type based on results
        if reservation_results:
            successful_slots = [slot for slot, result in reservation_results.items() if result["success"]]
            failed_slots = [slot for slot, result in reservation_results.items() if not result["success"] and result["message"] != "Not attempted - earlier slot succeeded"]
            attempted_slots = [slot for slot, result in reservation_results.items() if result["message"] not in ["", "Not attempted - earlier slot succeeded"]]
            all_success = len(successful_slots) == 2  # Success if we got both slots
            partial_success = len(successful_slots) == 1  # Partial success if we got one slot
            no_success = len(successful_slots) == 0
        else:
            successful_slots = []
            failed_slots = ["07:30-08:00", "08:00-08:30"]
            attempted_slots = failed_slots
            all_success = False
            partial_success = False
            no_success = True
        
        if all_success:
            subject = f"✅ Gym Reservation Success - Both Slots Reserved! (Cloud)"
            
            body = f"""
            <html>
            <body>
                <h2>🏋️ Gym Reservation Results (Cloud Deployment)</h2>
                
                <p><strong>Reservation Summary:</strong></p>
                <ul>
                    <li><strong>Date:</strong> {target_date}</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Reservation Made:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
                    <li><strong>Successful Slots:</strong> {len(successful_slots)}/2</li>
                    <li><strong>Deployment:</strong> Cloud ☁️</li>
                </ul>
                
                <h3>📋 Detailed Results:</h3>
                
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left;">Time Slot</th>
                        <th style="padding: 8px; text-align: left;">Status</th>
                        <th style="padding: 8px; text-align: left;">Message</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">07:30 - 08:00</td>
                        <td style="padding: 8px;">
                            {'<span style="color: green;">✅ SUCCESS</span>' if reservation_results["07:30-08:00"]["success"] else '<span style="color: red;">❌ FAILED</span>'}
                        </td>
                        <td style="padding: 8px;">{reservation_results["07:30-08:00"]["message"]}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">08:00 - 08:30</td>
                        <td style="padding: 8px;">
                            {'<span style="color: green;">✅ SUCCESS</span>' if reservation_results["08:00-08:30"]["success"] else '<span style="color: red;">❌ FAILED</span>'}
                        </td>
                        <td style="padding: 8px;">{reservation_results["08:00-08:30"]["message"]}</td>
                    </tr>
                </table>
                
                <p><strong>Overall Status:</strong> <span style="color: green;">✅ Both time slots reserved successfully!</span></p>
                
                <hr>
                <p><small>This is an automated message from your Cloud Gym Reservation System.</small></p>
            </body>
            </html>
            """
        elif partial_success:
            subject = "⚠️ Gym Reservation - Partial Success (Cloud)"
            
            body = f"""
            <html>
            <body>
                <h2>⚠️ Gym Reservation - Partial Success (Cloud Deployment)</h2>
                
                <p><strong>Reservation Summary:</strong></p>
                <ul>
                    <li><strong>Date:</strong> {target_date}</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Reservation Made:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
                    <li><strong>Successful Slots:</strong> {len(successful_slots)}/2</li>
                    <li><strong>Deployment:</strong> Cloud ☁️</li>
                </ul>
                
                <h3>📋 Detailed Results:</h3>
                
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left;">Time Slot</th>
                        <th style="padding: 8px; text-align: left;">Status</th>
                        <th style="padding: 8px; text-align: left;">Message</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">07:30 - 08:00</td>
                        <td style="padding: 8px;">
                            {'<span style="color: green;">✅ SUCCESS</span>' if reservation_results["07:30-08:00"]["success"] else '<span style="color: red;">❌ FAILED</span>'}
                        </td>
                        <td style="padding: 8px;">{reservation_results["07:30-08:00"]["message"]}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">08:00 - 08:30</td>
                        <td style="padding: 8px;">
                            {'<span style="color: green;">✅ SUCCESS</span>' if reservation_results["08:00-08:30"]["success"] else '<span style="color: red;">❌ FAILED</span>'}
                        </td>
                        <td style="padding: 8px;">{reservation_results["08:00-08:30"]["message"]}</td>
                    </tr>
                </table>
                
                <p><strong>Overall Status:</strong> <span style="color: orange;">⚠️ Partial success - {len(successful_slots)}/2 slots reserved</span></p>
                
                <p><strong>Manual Reservation Link:</strong></p>
                <p>You can try to manually reserve the failed slot by clicking the link below:</p>
                <p><a href="https://www.condomisoft.com/system/detalle_recursos.php?id_recurso=1780&nombre_recurso=GIMNASIO%20CUARTO%20PILATES%20Y%20%20SAL%C3%93N%20AEROBI" 
                   style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   🏋️ Reserve Manually on Condomisoft
                </a></p>
                
                <hr>
                <p><small>This is an automated message from your Cloud Gym Reservation System.</small></p>
            </body>
            </html>
            """
        else:
            subject = f"❌ Gym Reservation Failed - All {len(attempted_slots) if 'attempted_slots' in locals() else 'Available'} Early Morning Slots (Cloud)"
            
            # Use reservation_results if available, otherwise use exception message
            failure_reason = error_message if error_message else f"All {len(attempted_slots) if 'attempted_slots' in locals() else 'available'} early morning time slots failed - no slots available"
            
            body = f"""
            <html>
            <body>
                <h2>🏋️ Gym Reservation Failed - Both Slots (Cloud Deployment)</h2>
                
                <p><strong>Attempted Reservation:</strong></p>
                <ul>
                    <li><strong>Target Date:</strong> {target_date if target_date else 'Unable to determine'}</li>
                    <li><strong>Time Slots Attempted:</strong> {", ".join(attempted_slots)}</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Attempt Time:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
                    <li><strong>Deployment:</strong> Cloud ☁️</li>
                </ul>
                
                <p><strong>Status:</strong> <span style="color: red;">❌ FAILED - Not successful</span></p>
                
                <h3>📋 Detailed Failure Results:</h3>
                
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left;">Time Slot</th>
                        <th style="padding: 8px; text-align: left;">Status</th>
                        <th style="padding: 8px; text-align: left;">Result</th>
                    </tr>
                    {"".join([f'''
                    <tr>
                        <td style="padding: 8px;">{slot}</td>
                        <td style="padding: 8px;"><span style="color: red;">❌ FAILED</span></td>
                        <td style="padding: 8px;">{reservation_results[slot]["message"] if reservation_results and slot in reservation_results else "No available slots found"}</td>
                    </tr>''' for slot in attempted_slots])}
                </table>
                
                <p><strong>Overall Failure Reason:</strong></p>
                <p style="background-color: #ffebee; padding: 10px; border-radius: 5px; color: #c62828;">{failure_reason}</p>
                
                <p><strong>Possible causes:</strong></p>
                <ul>
                    <li><strong>Most likely:</strong> All attempted time slots were already reserved by other users</li>
                    <li>Gym availability calendar had no open slots for the target date</li>
                    <li>System couldn't find available buttons for any of the time slots</li>
                    <li>Network or website issues during reservation attempt</li>
                    <li>Booking window restrictions (some gyms limit advance booking days)</li>
                </ul>
                
                <p><strong>Manual Reservation Link:</strong></p>
                <p>You can try to make the reservation manually by clicking the link below:</p>
                <p><a href="https://www.condomisoft.com/system/detalle_recursos.php?id_recurso=1780&nombre_recurso=GIMNASIO%20CUARTO%20PILATES%20Y%20%20SAL%C3%93N%20AEROBI" 
                   style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   🏋️ Reserve Manually on Condomisoft
                </a></p>
                
                <p>Please check the cloud logs for more details.</p>
                
                <hr>
                <p><small>This is an automated message from your Cloud Gym Reservation System.</small></p>
            </body>
            </html>
            """
        
        send_email_notification(subject, body, success=not no_success)

def wait_for_exact_reservation_time(target_date, holdoff_seconds=None):
    """Wait until 7 days before target date, then hold until 00:01+ buffer.

    By default, waits until 00:01:05 Mexico City time to avoid race conditions
    at midnight. Override with RESERVATION_HOLDOFF_SECONDS env var.
    """
    mexico_tz = pytz.timezone('America/Mexico_City')

    # Resolve holdoff seconds (env override -> parameter default 65s)
    if holdoff_seconds is None:
        try:
            holdoff_seconds = int(os.getenv('RESERVATION_HOLDOFF_SECONDS', '65'))
        except Exception:
            holdoff_seconds = 65

    # Ensure target_date is timezone-aware
    if target_date.tzinfo is None:
        target_date = mexico_tz.localize(target_date)

    # Calculate the exact moment reservations become available (7 days before at midnight)
    reservation_opens = target_date - timedelta(days=7)
    reservation_opens = reservation_opens.replace(hour=0, minute=0, second=0, microsecond=0)
    desired_start = reservation_opens + timedelta(seconds=holdoff_seconds)

    logger.info(f"Target reservation date: {target_date.strftime('%A, %B %d, %Y')}")
    logger.info(f"Reservations open at: {reservation_opens.strftime('%A, %B %d, %Y at %H:%M:%S %Z')} (holding {holdoff_seconds}s -> start at {desired_start.strftime('%H:%M:%S')})")

    current_time = datetime.now(mexico_tz)

    # If we are before midnight opening, sleep until after holdoff
    if current_time < desired_start:
        wait_seconds = (desired_start - current_time).total_seconds()
        wait_minutes = wait_seconds / 60
        logger.info(f"⏰ Waiting {wait_minutes:.1f} minutes ({wait_seconds:.1f} seconds) until {desired_start.strftime('%Y-%m-%d %H:%M:%S %Z')}...")
        time.sleep(wait_seconds)
        final_time = datetime.now(mexico_tz)
        logger.info(f"🎯 Proceeding at: {final_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (after holdoff)")
    else:
        # We are already past desired start time – proceed immediately
        time_diff = (current_time - desired_start).total_seconds()
        logger.info(f"✅ Already {time_diff:.1f}s past desired start ({desired_start.strftime('%H:%M:%S')}). Proceeding now.")

def run_cloud_reservation_with_retry():
    """Function to run cloud reservation with precise timing and retry logic"""
    mexico_tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(mexico_tz)
    
    logger.info(f"GitHub Action started at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        # Determine the target date using the class logic (FOLLOWING week's gym day)
        temp_reservation = GymReservationCloud()
        target_date = temp_reservation.get_target_date()

        # Wait for the exact moment reservations become available, then hold past 00:01
        holdoff_seconds = None
        try:
            holdoff_seconds = int(os.getenv('RESERVATION_HOLDOFF_SECONDS', '65'))
        except Exception:
            holdoff_seconds = 65
        wait_for_exact_reservation_time(target_date, holdoff_seconds)
        
        # Now run the actual reservation
        run_cloud_reservation()
        logger.info("✅ Reservation completed successfully with precise timing")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check if error is related to "7 days in advance" or timing issues
        if "7 días" in error_msg or "7 days" in error_msg or "advance" in error_msg:
            logger.warning("⚠️ Still got 'too early' error even after waiting - scheduling additional retries")
            
            # Schedule retry attempts with small delays
            schedule.every().day.at("00:00:30").do(run_cloud_reservation_retry, attempt="30-seconds").tag('retry')
            schedule.every().day.at("00:01:00").do(run_cloud_reservation_retry, attempt="1-minute").tag('retry')
            schedule.every().day.at("00:02:00").do(run_cloud_reservation_retry, attempt="2-minute").tag('retry')
            
            logger.info("🔄 Scheduled additional retry attempts at 30s, 1min, and 2min past midnight")
            return False
        else:
            # Other error, just log and report
            logger.error(f"❌ Reservation failed with non-timing error: {e}")
            return False

def run_cloud_reservation_retry(attempt="unknown"):
    """Retry function that clears itself after successful run"""
    mexico_tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(mexico_tz)
    
    logger.info(f"🔄 Retry attempt '{attempt}' at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        run_cloud_reservation()
        logger.info(f"✅ Reservation completed successfully on retry attempt: {attempt}")
        
        # Clear all retry jobs after successful completion
        schedule.clear('retry')
        logger.info("🧹 Cleared all retry schedules after successful reservation")
        return True
        
    except Exception as e:
        logger.error(f"❌ Retry attempt '{attempt}' failed: {e}")
        return False

def main():
    """Main function to set up cloud scheduling with retry logic"""
    # Schedule the script to run the night before at 11:30 PM Mexico City time
    # Sunday night for Monday, Tuesday night for Wednesday, Thursday night for Friday
    schedule.every().sunday.at("23:30").do(run_cloud_reservation_with_retry)
    schedule.every().tuesday.at("23:30").do(run_cloud_reservation_with_retry)
    schedule.every().thursday.at("23:30").do(run_cloud_reservation_with_retry)
    
    # Log current Mexico City time for reference
    mexico_tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(mexico_tz)
    
    logger.info("Cloud scheduler started with retry logic")
    logger.info("Will run on Sunday/Tuesday/Thursday at 11:30 PM Mexico City time")
    logger.info("Automatic retries at 00:01 and 01:01 if needed")
    logger.info(f"Current time in Mexico City: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("Next scheduled runs:")
    
    # Show next scheduled times
    jobs = schedule.get_jobs()
    for job in jobs:
        logger.info(f"  - {job}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Check if we should run immediately (for GitHub Actions manual trigger)
    import os
    if os.getenv('GITHUB_ACTIONS') == 'true':
        logger.info("Running in GitHub Actions - executing immediately")
        run_cloud_reservation()
    else:
        # For immediate testing, uncomment the line below
        # run_cloud_reservation()
        
        # For cloud scheduling, run main()
        logger.info("Running in scheduler mode")
        main() 