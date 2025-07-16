#!/bin/bash

# Gym Reservation System - Cloud Deployment Script

echo "🏋️ Gym Reservation System - Cloud Deployment Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is installed"
        return 0
    else
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi
}

# Check if environment variables are set
check_env_vars() {
    if [ -f ".env" ]; then
        print_status "Environment file (.env) found"
        return 0
    else
        print_warning "Environment file (.env) not found"
        print_info "Please copy env.template to .env and fill in your credentials"
        return 1
    fi
}

# Build Docker image
build_image() {
    print_info "Building Docker image..."
    if docker build -t gym-reservation:latest .; then
        print_status "Docker image built successfully"
        return 0
    else
        print_error "Failed to build Docker image"
        return 1
    fi
}

# Test Docker image locally
test_image() {
    print_info "Testing Docker image locally..."
    if [ -f ".env" ]; then
        if docker run --rm --env-file .env gym-reservation:latest python -c "print('✅ Docker image test successful')"; then
            print_status "Docker image test passed"
            return 0
        else
            print_error "Docker image test failed"
            return 1
        fi
    else
        print_warning "Cannot test without .env file"
        return 1
    fi
}

# Deploy to Railway
deploy_railway() {
    print_info "Railway deployment instructions:"
    echo "1. Go to https://railway.app"
    echo "2. Connect your GitHub account"
    echo "3. Create new project from GitHub repo"
    echo "4. Set environment variables in Railway dashboard"
    echo "5. Deploy!"
    echo ""
    print_info "Environment variables needed:"
    echo "- CONDOMISOFT_USERNAME"
    echo "- CONDOMISOFT_PASSWORD"
    echo "- EMAIL_HOST"
    echo "- EMAIL_PORT"
    echo "- EMAIL_USER"
    echo "- EMAIL_PASSWORD"
    echo "- EMAIL_TO"
    echo "- TZ"
}

# Deploy to Render
deploy_render() {
    print_info "Render deployment instructions:"
    echo "1. Go to https://render.com"
    echo "2. Connect your GitHub account"
    echo "3. Create new Web Service"
    echo "4. Select your repository"
    echo "5. Set build command: pip install -r requirements.txt"
    echo "6. Set start command: python gym_reservation_cloud.py"
    echo "7. Set environment variables"
    echo "8. Deploy!"
}

# Main menu
main_menu() {
    echo "Choose an option:"
    echo "1. Check prerequisites"
    echo "2. Build Docker image"
    echo "3. Test locally"
    echo "4. Railway deployment guide"
    echo "5. Render deployment guide"
    echo "6. Exit"
    echo ""
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            echo ""
            print_info "Checking prerequisites..."
            check_docker
            check_env_vars
            echo ""
            ;;
        2)
            echo ""
            build_image
            echo ""
            ;;
        3)
            echo ""
            test_image
            echo ""
            ;;
        4)
            echo ""
            deploy_railway
            echo ""
            ;;
        5)
            echo ""
            deploy_render
            echo ""
            ;;
        6)
            echo ""
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please try again."
            echo ""
            ;;
    esac
}

# Initial setup check
echo "Checking your setup..."
echo ""

# Check if we're in the right directory
if [ ! -f "gym_reservation_cloud.py" ]; then
    print_error "gym_reservation_cloud.py not found. Please run this script from the project directory."
    exit 1
fi

print_status "Project files found"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    print_info "Creating .env file from template..."
    
    if [ -f "env.template" ]; then
        cp env.template .env
        print_info "Please edit .env file and add your credentials"
        print_warning "Remember to never commit .env file to version control!"
    else
        print_error "env.template not found"
    fi
fi

echo ""

# Main loop
while true; do
    main_menu
    read -p "Press Enter to continue..."
    echo ""
done 