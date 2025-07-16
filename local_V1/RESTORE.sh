#!/bin/bash

# Gym Reservation System - Local V1 Restore Script
# This script restores the Local V1 version to the parent directory

echo "=== Gym Reservation System - Local V1 Restore ==="
echo "This will restore the Local V1 version to the parent directory"
echo ""

# Check if we're in the local_V1 directory
if [ ! -f "VERSION_INFO.md" ]; then
    echo "❌ Error: Please run this script from the local_V1 directory"
    exit 1
fi

# Create backup of current version if it exists
if [ -f "../gym_reservation.py" ]; then
    echo "📦 Creating backup of current version..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    mkdir -p "../backup_${timestamp}"
    cp ../gym_reservation.py "../backup_${timestamp}/"
    echo "✅ Current version backed up to backup_${timestamp}/"
fi

# Restore files
echo "🔄 Restoring Local V1 files..."
cp gym_reservation.py requirements.txt config.env setup.py run.sh README.md test_email.py setup_email.py test_reservation.py debug_login.py simple_test.py com.user.gymreservation.plist ../

echo "✅ Local V1 restoration complete!"
echo ""
echo "📋 Restored files:"
echo "  - gym_reservation.py (Main script)"
echo "  - requirements.txt (Dependencies)"
echo "  - config.env (Environment variables)"
echo "  - setup.py (Installation helper)"
echo "  - run.sh (Shell interface)"
echo "  - README.md (Documentation)"
echo "  - test_email.py (Email testing)"
echo "  - setup_email.py (Email setup)"
echo "  - test_reservation.py (Reservation testing)"
echo "  - debug_login.py (Debug utilities)"
echo "  - simple_test.py (Simple test)"
echo "  - com.user.gymreservation.plist (LaunchDaemon)"
echo ""
echo "🚀 You can now run the system from the parent directory!"
echo "   cd .. && python3 setup.py"
echo ""
echo "📖 For more information, see VERSION_INFO.md" 