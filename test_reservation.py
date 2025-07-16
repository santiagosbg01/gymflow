#!/usr/bin/env python3
"""
Test script to run the gym reservation process once
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gym_reservation import GymReservation, run_weekly_reservation

def main():
    """Test the reservation process"""
    try:
        print("🏋️  Testing Gym Reservation Script")
        print("=" * 40)
        
        run_weekly_reservation()
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 