# Gym Reservation Automation Script

This script automatically reserves gym time slots (7:30 AM - 8:00 AM) at the condomisoft.com system. It runs on Monday, Wednesday, and Friday at 12:01 AM and reserves the next occurrence of the same day (next week).

## Setup

### Quick Setup (Recommended)
```bash
./run.sh setup
```
This will automatically install dependencies, create the `.env` file, and check for Chrome.

### Manual Setup

1. **Install Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure Credentials**
   - Copy `config.env` to `.env`
   - Edit `.env` and replace the placeholder values with your actual credentials:
     ```
     CONDOMISOFT_USERNAME=your_actual_username
     CONDOMISOFT_PASSWORD=your_actual_password
     ```

3. **Setup Email Notifications (Optional)**
   - Run the email setup guide:
     ```bash
     ./run.sh email-setup
     ```
   - Follow the instructions to set up Gmail App Password
   - Test email functionality:
     ```bash
     ./run.sh test-email
     ```

4. **Install Chrome Browser**
   - Make sure you have Google Chrome installed on your system
   - The script will automatically download and manage ChromeDriver

## Usage

### Quick Start (Using Shell Script)
```bash
# Setup dependencies and configuration
./run.sh setup

# Setup email notifications (optional)
./run.sh email-setup

# Test email notifications
./run.sh test-email

# Test the script once
./run.sh test

# Run weekly automation (interactive)
./run.sh daily

# Run weekly automation in background
./run.sh background
```

### Manual Usage

#### Test the Script
To test the script immediately (without scheduling):
```bash
python3 test_reservation.py
```

#### Run Weekly Automation
To run the script with weekly scheduling (runs at 12:01 AM on Monday, Wednesday, and Friday):
```bash
python3 gym_reservation.py
```

#### Run as Background Service (macOS/Linux)
To run the script continuously in the background:
```bash
nohup python3 gym_reservation.py &
```

## Configuration

- **Schedule Time**: The script is set to run at 12:01 AM on Monday, Wednesday, and Friday. You can change this in the `main()` function.
- **Time Slot**: Currently reserves 7:30 AM - 8:00 AM. You can modify this in the `make_reservations()` method.
- **Calendar Logic**: The script automatically selects the next occurrence of the same day (next week). For example, if it runs on Friday at 12:01 AM, it will select the next Friday.
- **Email Notifications**: The script sends email notifications to `santiago.sbg@gmail.com` after each reservation attempt.
- **Headless Mode**: The script runs in headless mode (no browser window). To see the browser, remove the `--headless` argument in `setup_driver()`.

## Email Notifications

The script automatically sends email notifications after each reservation attempt:

### **Successful Reservation Email:**
- ✅ **Subject**: "Gym Reservation Successful"
- **Content**: Reservation details, date, time slot, confirmation status
- **Recipient**: santiago.sbg@gmail.com

### **Failed Reservation Email:**
- ❌ **Subject**: "Gym Reservation Failed"  
- **Content**: Error details, attempted reservation info, troubleshooting guidance
- **Recipient**: santiago.sbg@gmail.com

### **Email Setup Requirements:**
1. Gmail account with 2-factor authentication enabled
2. App Password generated for this script
3. EMAIL_USER and EMAIL_PASSWORD configured in `.env` file

## Logging

The script creates a log file (`gym_reservation.log`) that records all activities and errors. Check this file if you encounter issues.

## Troubleshooting

1. **Login Issues**: Verify your credentials in the `.env` file
2. **Element Not Found**: The website structure might have changed. You may need to update the element selectors in the script
3. **Chrome Driver Issues**: Make sure Chrome is installed and up to date

## Notes

- The script uses multiple fallback methods to find time slot buttons on the page
- It waits between actions to avoid overwhelming the server
- All errors are logged with timestamps for debugging

## Running on macOS (using launchd)

To run this script automatically on macOS startup, you can create a launchd service:

1. Create a plist file in `~/Library/LaunchAgents/`
2. Load it with `launchctl load ~/Library/LaunchAgents/your_plist_file.plist`

Example plist configuration is provided in the next section if needed. 