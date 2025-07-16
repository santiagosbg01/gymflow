#!/bin/bash

# Gym Reservation Script Runner

case "$1" in
    "setup")
        echo "🏋️  Running setup..."
        python3 setup.py
        ;;
    "test")
        echo "🏋️  Running test reservation..."
        python3 test_reservation.py
        ;;
    "email-setup")
        echo "📧 Setting up email notifications..."
        python3 setup_email.py
        ;;
    "test-email")
        echo "📧 Testing email notifications..."
        python3 test_email.py
        ;;
    "daily")
        echo "🏋️  Starting weekly reservation service..."
        python3 gym_reservation.py
        ;;
    "background")
        echo "🏋️  Starting weekly reservation service in background..."
        nohup python3 gym_reservation.py > gym_reservation.log 2>&1 &
        echo "Service started in background. Check gym_reservation.log for output."
        ;;
    *)
        echo "Usage: $0 {setup|test|email-setup|test-email|daily|background}"
        echo ""
        echo "Commands:"
        echo "  setup      - Install dependencies and configure environment"
        echo "  test       - Run reservation process once for testing"
        echo "  email-setup - Guide through email notification setup"
        echo "  test-email - Test email notification functionality"
        echo "  daily      - Start weekly reservation service (runs Mon/Wed/Fri at 12:01 AM)"
        echo "  background - Start weekly service in background"
        echo ""
        echo "Examples:"
        echo "  ./run.sh setup"
        echo "  ./run.sh test"
        echo "  ./run.sh email-setup"
        echo "  ./run.sh test-email"
        echo "  ./run.sh daily"
        echo "  ./run.sh background"
        exit 1
        ;;
esac 