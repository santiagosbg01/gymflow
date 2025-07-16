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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import schedule

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gym_reservation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GymReservation:
    def __init__(self):
        self.driver = None
        self.wait = None
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
    
    def setup_driver(self):
        """Set up Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to get the ChromeDriver
            driver_path = ChromeDriverManager().install()
            
            # Fix the path if it's pointing to the wrong file
            if 'THIRD_PARTY_NOTICES' in driver_path:
                import os
                driver_dir = os.path.dirname(driver_path)
                # Look for the actual chromedriver file
                for file in os.listdir(driver_dir):
                    if file.startswith('chromedriver') and not file.endswith('.txt'):
                        driver_path = os.path.join(driver_dir, file)
                        break
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Add stealth settings
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            # Try without webdriver-manager as fallback
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)
                logger.info("Driver initialized successfully using system ChromeDriver")
            except Exception as e2:
                logger.error(f"Failed to initialize driver with system ChromeDriver: {e2}")
                raise
    
    def login(self):
        """Login to the condomisoft system"""
        try:
            logger.info("Navigating to login page")
            self.driver.get(self.login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're already logged in by looking for logout link or user info
            if self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Salir') or contains(text(), 'Logout')]"):
                logger.info("Already logged in")
                return
            
            # Look for login form fields
            username_field = None
            password_field = None
            
            # Try to find username field
            username_elements = self.driver.find_elements(By.NAME, "usuario")
            if not username_elements:
                username_elements = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email']")
            
            if username_elements:
                username_field = username_elements[0]
                logger.info("Found username field")
            else:
                logger.error("No username field found")
                raise Exception("Username field not found")
            
            # Try to find password field
            password_elements = self.driver.find_elements(By.NAME, "clave")
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
            
            # Submit login form
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
                
                # After successful login, click on the G-502 condominium button
                self.select_condominium()
                
            else:
                logger.warning("Login may have failed - checking for error messages")
                # Check for error messages
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'incorrecto') or contains(text(), 'invalid')]")
                if error_elements:
                    logger.error(f"Login error: {error_elements[0].text}")
                    raise Exception(f"Login failed: {error_elements[0].text}")
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def select_condominium(self):
        """Select the G-502 apartment from the dashboard"""
        try:
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
        """Navigate to the gym reservation page"""
        try:
            logger.info("Navigating to reservation page")
            self.driver.get(self.reservation_url)
            
            # Wait for the reservation page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("Reservation page loaded")
            
        except Exception as e:
            logger.error(f"Failed to navigate to reservation page: {str(e)}")
            raise
    
    def get_target_date(self):
        """Calculate the next occurrence of the same day of the week"""
        now = datetime.now()
        current_weekday = now.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        
        # Map weekdays to names for logging
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Calculate days until next occurrence of the same weekday
        days_ahead = 7  # Always go to next week
        target_date = now + timedelta(days=days_ahead)
        
        logger.info(f"Current day: {weekday_names[current_weekday]}")
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

def run_weekly_reservation():
    """Function to run the weekly reservation"""
    start_time = datetime.now()
    success = False
    error_message = ""
    target_date = ""
    reservation_message = ""
    reservation = None
    
    try:
        logger.info("Starting weekly reservation process")
        reservation = GymReservation()
        
        # Get target date info for email
        target_date_obj = reservation.get_target_date()
        target_date = target_date_obj.strftime('%A, %B %d, %Y')
        
        reservation.make_reservations()
        
        # Check the actual reservation status from validation
        success = any(result["success"] for result in reservation.reservation_results.values())
        reservation_results = reservation.reservation_results
        
        if success:
            logger.info("Weekly reservation completed successfully (at least one slot reserved)")
        else:
            logger.error("Weekly reservation failed: Both time slots failed")
            
    except Exception as e:
        success = False
        error_message = str(e)
        logger.error(f"Weekly reservation failed: {error_message}")
    
    finally:
        # Send email notification
        end_time = datetime.now()
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
            subject = "✅ Gym Reservation - Both Slots Reserved!"
            
            body = f"""
            <html>
            <body>
                <h2>🏋️ Gym Reservation Results</h2>
                
                <p><strong>Reservation Summary:</strong></p>
                <ul>
                    <li><strong>Date:</strong> {target_date}</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Reservation Made:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
                    <li><strong>Successful Slots:</strong> {len(successful_slots)}/2</li>
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
                <p><small>This is an automated message from your Gym Reservation System.</small></p>
            </body>
            </html>
            """
        elif partial_success:
            subject = "⚠️ Gym Reservation - Partial Success"
            
            body = f"""
            <html>
            <body>
                <h2>⚠️ Gym Reservation - Partial Success</h2>
                
                <p><strong>Reservation Summary:</strong></p>
                <ul>
                    <li><strong>Date:</strong> {target_date}</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Reservation Made:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
                    <li><strong>Successful Slots:</strong> {len(successful_slots)}/2</li>
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
                <p><small>This is an automated message from your Gym Reservation System.</small></p>
            </body>
            </html>
            """
        else:
            subject = "❌ Gym Reservation Failed - Both Slots"
            
            # Use reservation_results if available, otherwise use exception message
            failure_reason = error_message if error_message else "Both time slots failed"
            
            body = f"""
            <html>
            <body>
                <h2>🏋️ Gym Reservation Failed - Both Slots</h2>
                
                <p><strong>Attempted Reservation:</strong></p>
                <ul>
                    <li><strong>Target Date:</strong> {target_date if target_date else 'Unable to determine'}</li>
                    <li><strong>Time Slots:</strong> 07:30-08:00 and 08:00-08:30</li>
                    <li><strong>Location:</strong> Gym - G-502</li>
                    <li><strong>Attempt Time:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Duration:</strong> {duration.total_seconds():.1f} seconds</li>
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
                
                <p>Please check the logs for more details or try running the script manually.</p>
                
                <hr>
                <p><small>This is an automated message from your Gym Reservation System.</small></p>
            </body>
            </html>
            """
        
        send_email_notification(subject, body, success=not no_success)

def main():
    """Main function to set up weekly scheduling"""
    # Schedule the script to run on Monday, Wednesday, and Friday at 00:01 AM
    schedule.every().monday.at("00:01").do(run_weekly_reservation)
    schedule.every().wednesday.at("00:01").do(run_weekly_reservation)
    schedule.every().friday.at("00:01").do(run_weekly_reservation)
    
    logger.info("Scheduler started. Will run on Monday, Wednesday, and Friday at 00:01 AM")
    logger.info("Next scheduled runs:")
    
    # Show next scheduled times
    jobs = schedule.get_jobs()
    for job in jobs:
        logger.info(f"  - {job}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # For immediate testing, uncomment the line below
    # run_weekly_reservation()
    
    # For weekly scheduling, run main()
    main() 