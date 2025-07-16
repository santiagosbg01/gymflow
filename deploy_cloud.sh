#!/bin/bash

# Cloud Deployment Script for Gym Reservation System
# This script helps test and deploy the cloud version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment variables
validate_env() {
    print_status "Validating environment variables..."
    
    local missing_vars=()
    
    if [ -z "$CONDOMISOFT_USERNAME" ]; then
        missing_vars+=("CONDOMISOFT_USERNAME")
    fi
    
    if [ -z "$CONDOMISOFT_PASSWORD" ]; then
        missing_vars+=("CONDOMISOFT_PASSWORD")
    fi
    
    if [ -z "$EMAIL_USER" ]; then
        missing_vars+=("EMAIL_USER")
    fi
    
    if [ -z "$EMAIL_PASSWORD" ]; then
        missing_vars+=("EMAIL_PASSWORD")
    fi
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required environment variables are set"
        return 0
    else
        print_error "Missing required environment variables: ${missing_vars[*]}"
        echo "Please set these variables in your environment or config.env file"
        return 1
    fi
}

# Function to load environment variables from config.env
load_env() {
    if [ -f "config.env" ]; then
        print_status "Loading environment variables from config.env..."
        source config.env
        print_success "Environment variables loaded"
    else
        print_warning "config.env file not found. Using system environment variables."
    fi
}

# Function to test core logic
test_core_logic() {
    print_status "Testing core logic without drivers..."
    
    if python3 test_simple_cloud.py; then
        print_success "Core logic tests passed"
        return 0
    else
        print_error "Core logic tests failed"
        return 1
    fi
}

# Function to test local cloud version
test_local_cloud() {
    print_status "Testing cloud version locally..."
    
    # Create a simple test that doesn't require full driver setup
    python3 -c "
import sys
sys.path.append('.')
from gym_reservation_cloud import GymReservationCloud

try:
    # Test initialization
    reservation = GymReservationCloud()
    print('✅ Cloud version initialization successful')
    
    # Test timezone
    import pytz
    from datetime import datetime
    mexico_tz = pytz.timezone('America/Mexico_City')
    now = datetime.now(mexico_tz)
    print(f'✅ Mexico City timezone: {now}')
    
    print('✅ Local cloud version tests passed')
except Exception as e:
    print(f'❌ Local cloud version test failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Local cloud version tests passed"
        return 0
    else
        print_error "Local cloud version tests failed"
        return 1
    fi
}

# Function to build Docker image
build_docker() {
    print_status "Building Docker image..."
    
    if command_exists docker; then
        if docker build -t gym-reservation-cloud .; then
            print_success "Docker image built successfully"
            return 0
        else
            print_error "Docker build failed"
            return 1
        fi
    else
        print_warning "Docker not available, skipping Docker build"
        return 0
    fi
}

# Function to test Docker container
test_docker() {
    print_status "Testing Docker container..."
    
    if command_exists docker; then
        if docker run --rm \
            -e CONDOMISOFT_USERNAME="$CONDOMISOFT_USERNAME" \
            -e CONDOMISOFT_PASSWORD="$CONDOMISOFT_PASSWORD" \
            -e EMAIL_USER="$EMAIL_USER" \
            -e EMAIL_PASSWORD="$EMAIL_PASSWORD" \
            gym-reservation-cloud \
            python3 test_simple_cloud.py; then
            print_success "Docker container tests passed"
            return 0
        else
            print_error "Docker container tests failed"
            return 1
        fi
    else
        print_warning "Docker not available, skipping Docker tests"
        return 0
    fi
}

# Function to show deployment options
show_deployment_options() {
    print_status "Cloud Deployment Options:"
    echo ""
    echo "1. Railway (railway.json configured)"
    echo "   - Connect GitHub repository"
    echo "   - Set environment variables"
    echo "   - Deploy automatically"
    echo ""
    echo "2. Render (render.yaml configured)"
    echo "   - Connect GitHub repository"
    echo "   - Set environment variables"
    echo "   - Deploy automatically"
    echo ""
    echo "3. DigitalOcean App Platform"
    echo "   - Use docker-compose.cloud.yml"
    echo "   - Set environment variables"
    echo "   - Deploy container"
    echo ""
    echo "4. Heroku"
    echo "   - Use Dockerfile"
    echo "   - Set environment variables"
    echo "   - Deploy container"
    echo ""
    echo "5. AWS ECS/Fargate"
    echo "   - Use Dockerfile"
    echo "   - Configure task definition"
    echo "   - Set environment variables"
    echo ""
    echo "See CLOUD_DEPLOYMENT.md for detailed instructions"
}

# Main execution
main() {
    echo "=========================================="
    echo "  Gym Reservation Cloud Deployment"
    echo "=========================================="
    echo ""
    
    # Load environment variables
    load_env
    
    # Validate environment
    if ! validate_env; then
        exit 1
    fi
    
    # Test core logic
    if ! test_core_logic; then
        exit 1
    fi
    
    # Test local cloud version
    if ! test_local_cloud; then
        exit 1
    fi
    
    # Build and test Docker (if available)
    if build_docker; then
        test_docker
    fi
    
    # Show deployment options
    show_deployment_options
    
    print_success "Cloud deployment preparation complete!"
    print_status "Choose a deployment platform from the options above"
}

# Run main function
main "$@" 