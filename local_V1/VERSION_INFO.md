# Gym Reservation System - Local Version 1 (V1)

## Version Information
- **Created**: July 16, 2025
- **Version**: Local_V1
- **Status**: Fully Operational

## System Description
This is a complete backup of the gym reservation automation system that automatically reserves gym slots at condomisoft.com for apartment G-502.

## Key Features
- **Dual Slot Reservation**: Reserves both 07:30-08:00 and 08:00-08:30 time slots
- **Smart Scheduling**: Runs on Monday, Wednesday, and Friday at 00:01 AM
- **Date Selection**: Automatically selects next week's same day of the week
- **Error Handling**: Handles "7 days in advance" error with automatic retry
- **Email Notifications**: Sends detailed HTML emails with reservation results
- **Validation**: Confirms reservations by checking for "Confirmado para G-502"
- **Robust Recovery**: Automatic error detection and recovery mechanisms

## Files Included
- `gym_reservation.py` - Main automation script (923 lines)
- `requirements.txt` - Python dependencies
- `config.env` - Environment variables template
- `setup.py` - Installation and configuration helper
- `run.sh` - Shell script interface with multiple commands
- `README.md` - Complete documentation
- `test_email.py` - Email testing utilities
- `setup_email.py` - Email configuration helper
- `test_reservation.py` - Reservation testing utilities
- `debug_login.py` - Debug and testing utilities
- `simple_test.py` - Simple test utilities
- `com.user.gymreservation.plist` - LaunchDaemon configuration

## Last Test Results
- **Date**: July 16, 2025
- **Target**: Wednesday, July 23, 2025
- **Results**: 
  - 07:30-08:00: ❌ Failed (slot already booked)
  - 08:00-08:30: ✅ Success (Confirmed for G-502)
- **Status**: System fully operational

## Configuration
- **Username**: santiago.sbg@gmail.com
- **Target Apartment**: G-502
- **Website**: https://www.condomisoft.com
- **Email Notifications**: Enabled (santiago.sbg@gmail.com)
- **Schedule**: Mon/Wed/Fri at 00:01 AM

## Technical Details
- **Language**: Python 3.9+
- **Framework**: Selenium WebDriver
- **Browser**: Chrome (headless)
- **Email**: SMTP (Gmail)
- **Scheduling**: Python `schedule` library
- **Error Handling**: Comprehensive with automatic recovery

## Notes
- All validation failsafes implemented
- Email notifications with detailed results
- Automatic handling of "7 days in advance" error
- Smart calendar selection logic
- Robust error recovery mechanisms
- Ready for production use 