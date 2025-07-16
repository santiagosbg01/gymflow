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
        
        # Reservation status tracking for multiple time slots
        self.reservation_results = {
            "07:30-08:00": {"success": False, "message": "Not attempted"},
            "08:00-08:30": {"success": False, "message": "Not attempted"}
        }
        
        if not self.username or not self.password:
            logger.error("Username and password must be set in environment variables")
            raise ValueError("Missing credentials")
    
    def setup_chrome_driver(self):
        """Set up Chrome WebDriver with cloud-optimized options"""
        try:
            chrome_options = ChromeOptions()
            
            # Essential options for cloud deployment
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            # Removed --disable-javascript as it may break the website
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
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
            
            # Try WebDriverManager as fallback
            try:
                chrome_driver_path = ChromeDriverManager().install()
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
            
            # Wait for username field
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "user")))
            logger.info("Found username field")
            
            password_field = self.driver.find_element(By.NAME, "pass")
            logger.info("Found password field")
            
            # Enter credentials
            logger.info("Entering credentials...")
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Find and click login button
            login_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Entrar']")
            login_button.click()
            
            logger.info("Login form submitted")
            
            # Wait for successful login
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login.php" in current_url:
                logger.error("Login failed - still on login page")
                raise Exception("Login failed")
            
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

    def select_apartment(self):
        """Select the G-502 apartment"""
        try:
            logger.info("Selecting apartment G-502")
            
            # Look for G-502 button
            g502_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'G-502')]")))
            g502_button.click()
            
            logger.info("Successfully clicked G-502 apartment button")
            
            # Wait for apartment selection to process
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Failed to select apartment: {str(e)}")
            raise

    def navigate_to_reservation(self):
        """Navigate to the reservation page"""
        try:
            logger.info("Navigating to reservation page")
            self.driver.get(self.reservation_url)
            
            # Wait for page to load
            time.sleep(2)
            
            logger.info("Reservation page loaded")
            
        except Exception as e:
            logger.error(f"Failed to navigate to reservation page: {str(e)}")
            raise

    def get_target_date(self):
        """Calculate the next occurrence of the same day of the week"""
        # Use Mexico City timezone
        mexico_tz = pytz.timezone('America/Mexico_City')
        now = datetime.now(mexico_tz)
        current_weekday = now.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        
        # Map weekdays to names for logging
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Calculate days until next occurrence of the same weekday
        days_ahead = 7  # Always go to next week
        target_date = now + timedelta(days=days_ahead)
        
        logger.info(f"Current day (Mexico City): {weekday_names[current_weekday]}")
        logger.info(f"Current time (Mexico City): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Target date: {target_date.strftime('%Y-%m-%d (%A)')}")
        
        return target_date

    def select_calendar_day(self):
        """Select the next occurrence of the same day of the week from the calendar"""
        try:
            target_date = self.get_target_date()
            target_day = target_date.day
            
            logger.info(f"Looking for day {target_day} in calendar")
            
            # Wait for calendar to load
            time.sleep(2)
            
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
                logger.info(f"Found {len(available_days)} available days")
                for i, day in enumerate(available_days[:10]):  # Show first 10 days
                    logger.info(f"  Day {i}: {day.text}")
                
                # Look for the specific target day
                target_day_element = None
                for day_element in available_days:
                    if day_element.text.strip() == str(target_day):
                        target_day_element = day_element
                        break
                
                if target_day_element:
                    target_day_element.click()
                    logger.info(f"Selected calendar day: {target_day}")
                    
                    # Wait for the day selection to process
                    time.sleep(3)
                    
                    # Check if we got the "7 days in advance" error
                    if self.check_and_handle_advance_error():
                        return True
                    
                    return True
                else:
                    logger.warning(f"Target day {target_day} not found in available days")
                    # Fall back to selecting the first available day
                    available_days[0].click()
                    logger.info(f"Selected fallback day: {available_days[0].text}")
                    time.sleep(3)
                    
                    # Check if we got the "7 days in advance" error
                    if self.check_and_handle_advance_error():
                        return True
                    
                    return True
            else:
                logger.warning("No available days found in calendar")
                return False
            
        except Exception as e:
            logger.error(f"Failed to select calendar day: {str(e)}")
            return False

    def check_and_handle_advance_error(self):
        """Check for the '7 days in advance' error message and handle it"""
        try:
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
        """Select calendar day with more precise date calculation to avoid 7-day limit"""
        try:
            # Calculate target date more precisely - exactly 7 days from now or less
            now = datetime.now()
            current_weekday = now.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
            
            # Calculate days until next occurrence of the same weekday, but cap at 7 days
            days_ahead = 7
            if current_weekday == 0:  # Monday
                days_ahead = 7  # Next Monday
            elif current_weekday == 2:  # Wednesday  
                days_ahead = 7  # Next Wednesday
            elif current_weekday == 4:  # Friday
                days_ahead = 7  # Next Friday
            else:
                # For other days, find the next occurrence of Mon/Wed/Fri
                if current_weekday == 6:  # Sunday (6) -> Monday (0)
                    days_ahead = 1
                elif current_weekday == 1:  # Tuesday -> Wednesday
                    days_ahead = 1
                elif current_weekday == 3:  # Thursday -> Friday
                    days_ahead = 1
                elif current_weekday == 5:  # Saturday -> Monday
                    days_ahead = 2
                else:  # Default to 7 days
                    days_ahead = 7
            
            target_date = now + timedelta(days=days_ahead)
            target_day = target_date.day
            
            logger.info(f"Retry: Looking for day {target_day} in calendar (calculated with {days_ahead} days ahead)")
            
            # Wait for calendar to load
            time.sleep(2)
            
            # Look for available days
            available_days = self.driver.find_elements(By.XPATH, "//td[contains(@style, 'background-color: #90EE90') or contains(@style, 'background-color: green') or contains(@class, 'available')]")
            
            if not available_days:
                available_days = self.driver.find_elements(By.XPATH, "//td[@onclick and text() and string-length(text()) <= 2 and text() != ' ']")
            
            if not available_days:
                available_days = self.driver.find_elements(By.XPATH, "//td[text() and @onclick and not(contains(@class, 'disabled'))]")
            
            if available_days:
                # Look for the specific target day
                target_day_element = None
                for day_element in available_days:
                    if day_element.text.strip() == str(target_day):
                        target_day_element = day_element
                        break
                
                if target_day_element:
                    target_day_element.click()
                    logger.info(f"Retry: Selected calendar day: {target_day}")
                    time.sleep(3)
                    return True
                else:
                    logger.warning(f"Retry: Target day {target_day} not found, selecting first available day")
                    available_days[0].click()
                    logger.info(f"Retry: Selected fallback day: {available_days[0].text}")
                    time.sleep(3)
                    return True
            else:
                logger.warning("Retry: No available days found in calendar")
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
                time.sleep(1)
                time_buttons[0].click()
                
                # Wait for confirmation or next step
                time.sleep(3)
                
                # Check if we got the "7 days in advance" error after clicking
                if not self.check_and_handle_advance_error():
                    return False
                
                # Look for confirmation button
                confirm_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirmar') or contains(text(), 'Reservar') or contains(text(), 'Aceptar')]")
                if confirm_buttons:
                    confirm_buttons[0].click()
                    logger.info(f"Clicked confirmation button for {time_slot} slot")
                    time.sleep(3)
                    
                    # Check if we got the "7 days in advance" error after confirmation
                    if not self.check_and_handle_advance_error():
                        return False
                else:
                    logger.info(f"Reservation for {time_slot} initiated (no confirmation button found)")
                    time.sleep(2)
                    
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
            time.sleep(3)
            
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
            
            # Define both time slots to reserve
            time_slots = ["07:30-08:00", "08:00-08:30"]
            
            # Attempt to reserve both time slots
            for time_slot in time_slots:
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
                time.sleep(2)
            
            logger.info("Reservation process completed for both time slots")
            
            # Check if at least one reservation was successful
            any_success = any(result["success"] for result in self.reservation_results.values())
            if not any_success:
                raise Exception("Both reservations failed")
            
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
            failed_slots = [slot for slot, result in reservation_results.items() if not result["success"]]
            all_success = len(successful_slots) == 2
            partial_success = len(successful_slots) == 1
            no_success = len(successful_slots) == 0
        else:
            successful_slots = []
            failed_slots = ["07:30-08:00", "08:00-08:30"] 
            all_success = False
            partial_success = False
            no_success = True
        
        if all_success:
            subject = "✅ Gym Reservation - Both Slots Reserved! (Cloud)"
            
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
                
                <p><strong>Overall Status:</strong> <span style="color: green;">✅ Both slots reserved successfully!</span></p>
                
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
                
                <p><strong>Overall Status:</strong> <span style="color: orange;">⚠️ One slot reserved, one failed</span></p>
                
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
            subject = "❌ Gym Reservation Failed - Both Slots (Cloud)"
            
            # Use reservation_results if available, otherwise use exception message
            failure_reason = error_message if error_message else "Both time slots failed"
            
            body = f"""
            <html>
            <body>
                <h2>🏋️ Gym Reservation Failed - Both Slots (Cloud Deployment)</h2>
                
                <p><strong>Attempted Reservation:</strong></p>
                <ul>
                    <li><strong>Target Date:</strong> {target_date if target_date else 'Unable to determine'}</li>
                    <li><strong>Time Slots:</strong> 07:30-08:00 and 08:00-08:30</li>
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
                        <th style="padding: 8px; text-align: left;">Failure Reason</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">07:30 - 08:00</td>
                        <td style="padding: 8px;"><span style="color: red;">❌ FAILED</span></td>
                        <td style="padding: 8px;">{reservation_results["07:30-08:00"]["message"] if reservation_results else "Unknown error"}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">08:00 - 08:30</td>
                        <td style="padding: 8px;"><span style="color: red;">❌ FAILED</span></td>
                        <td style="padding: 8px;">{reservation_results["08:00-08:30"]["message"] if reservation_results else "Unknown error"}</td>
                    </tr>
                </table>
                
                <p><strong>Overall Failure Reason:</strong></p>
                <p style="background-color: #ffebee; padding: 10px; border-radius: 5px; color: #c62828;">{failure_reason}</p>
                
                <p><strong>Possible causes:</strong></p>
                <ul>
                    <li>Time slots were already reserved by another user</li>
                    <li>System did not confirm the reservations properly</li>
                    <li>Network or website issues during reservation</li>
                    <li>Time slots show "Disponible" instead of "Confirmado para G-502"</li>
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

def main():
    """Main function to set up cloud scheduling"""
    # Schedule the script to run on Monday, Wednesday, and Friday at 00:01 AM Mexico City time
    schedule.every().monday.at("00:01").do(run_cloud_reservation)
    schedule.every().wednesday.at("00:01").do(run_cloud_reservation)
    schedule.every().friday.at("00:01").do(run_cloud_reservation)
    
    # Log current Mexico City time for reference
    mexico_tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(mexico_tz)
    
    logger.info("Cloud scheduler started. Will run on Monday, Wednesday, and Friday at 00:01 AM Mexico City time")
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