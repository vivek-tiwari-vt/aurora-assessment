#!/bin/bash

# Aurora Q&A System - Complete Deployment Script
# This script builds Docker, starts all services, and pushes to GitHub

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="aurora-qa-system"
DOCKER_IMAGE="vivek-tiwari-vt/aurora-qa-system:latest"
DOCKER_COMPOSE_FILE="docker/docker-compose.yml"
GIT_REPO="https://github.com/vivek-tiwari-vt/aurora-assessment.git"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing=0
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        missing=1
    else
        print_success "Docker is installed"
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        missing=1
    else
        print_success "Docker Compose is installed"
    fi
    
    if ! command_exists git; then
        print_error "Git is not installed"
        missing=1
    else
        print_success "Git is installed"
    fi
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Make sure to create it with OPENROUTER_API_KEY"
    else
        print_success ".env file exists"
    fi
    
    if [ $missing -eq 1 ]; then
        print_error "Please install missing prerequisites"
        exit 1
    fi
    
    echo ""
}

# Build Docker image
build_docker() {
    print_header "Building Docker Image"
    
    print_info "Building Docker image: $DOCKER_IMAGE"
    docker build -f docker/Dockerfile -t $DOCKER_IMAGE .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
        docker images | grep aurora-qa-system
    else
        print_error "Docker build failed"
        exit 1
    fi
    
    echo ""
}

# Stop existing services
stop_services() {
    print_header "Stopping Existing Services"
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        print_info "Stopping Docker Compose services..."
        cd docker
        docker-compose down 2>/dev/null || true
        cd ..
        print_success "Services stopped"
    else
        print_warning "Docker Compose file not found, skipping..."
    fi
    
    # Stop any running containers
    print_info "Stopping any running containers..."
    docker stop $PROJECT_NAME 2>/dev/null || true
    docker rm $PROJECT_NAME 2>/dev/null || true
    
    echo ""
}

# Start services with Docker Compose
start_services() {
    print_header "Starting All Services"
    
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    print_info "Starting services with Docker Compose..."
    cd docker
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
    
    cd ..
    
    # Wait for service to be ready
    print_info "Waiting for service to be ready..."
    sleep 5
    
    # Check if service is running
    if docker ps | grep -q $PROJECT_NAME; then
        print_success "Service is running"
        print_info "Backend API: http://localhost:8000"
        print_info "Frontend: http://localhost:8000"
        print_info "API Health: http://localhost:8000/api"
    else
        print_warning "Service container not found in running containers"
    fi
    
    echo ""
}

# Show service status
show_status() {
    print_header "Service Status"
    
    echo -e "\n${BLUE}Running Containers:${NC}"
    docker ps --filter "name=$PROJECT_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${BLUE}Service Logs (last 20 lines):${NC}"
    cd docker
    docker-compose logs --tail=20
    cd ..
    
    echo -e "\n${BLUE}Testing Health Endpoint:${NC}"
    sleep 2
    if curl -s http://localhost:8000/api > /dev/null; then
        print_success "Service is responding"
        curl -s http://localhost:8000/api | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api
    else
        print_warning "Service not responding yet (may still be starting)"
    fi
    
    echo ""
}

# Push to GitHub
push_to_github() {
    print_header "Pushing to GitHub"
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_error "Not a git repository"
        return 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "You have uncommitted changes"
        read -p "Do you want to commit and push? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Staging all changes..."
            git add .
            
            read -p "Enter commit message (or press Enter for default): " commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="Deploy: Update services and Docker configuration"
            fi
            
            print_info "Committing changes..."
            git commit -m "$commit_msg"
        else
            print_warning "Skipping commit"
        fi
    else
        print_info "No uncommitted changes"
    fi
    
    # Get current branch
    current_branch=$(git branch --show-current)
    print_info "Current branch: $current_branch"
    
    # Push to GitHub
    print_info "Pushing to GitHub..."
    if git push origin $current_branch; then
        print_success "Successfully pushed to GitHub"
        print_info "Repository: $GIT_REPO"
        print_info "Branch: $current_branch"
    else
        print_error "Failed to push to GitHub"
        print_warning "You may need to set up remote or authentication"
        return 1
    fi
    
    echo ""
}

# Main execution
main() {
    print_header "Aurora Q&A System - Complete Deployment"
    
    # Parse command line arguments
    SKIP_BUILD=false
    SKIP_START=false
    SKIP_PUSH=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-start)
                SKIP_START=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-build    Skip Docker build step"
                echo "  --skip-start    Skip starting services"
                echo "  --skip-push     Skip pushing to GitHub"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run steps
    check_prerequisites
    
    if [ "$SKIP_BUILD" = false ]; then
        build_docker
    else
        print_warning "Skipping Docker build"
    fi
    
    if [ "$SKIP_START" = false ]; then
        stop_services
        start_services
        show_status
    else
        print_warning "Skipping service start"
    fi
    
    if [ "$SKIP_PUSH" = false ]; then
        read -p "Do you want to push to GitHub? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            push_to_github
        else
            print_info "Skipping GitHub push"
        fi
    else
        print_warning "Skipping GitHub push"
    fi
    
    print_header "Deployment Complete!"
    print_success "All services are running"
    print_info "Access your application at:"
    echo -e "  ${GREEN}Frontend:${NC} http://localhost:8000"
    echo -e "  ${GREEN}API:${NC} http://localhost:8000/api"
    echo -e "  ${GREEN}Health:${NC} http://localhost:8000/api/health"
    echo ""
    print_info "To view logs: cd docker && docker-compose logs -f"
    print_info "To stop services: cd docker && docker-compose down"
    echo ""
}

# Run main function
main "$@"

