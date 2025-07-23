#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Helper functions
log_info() { echo -e "${GREEN}✨ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    

    # Check if .env file exists
    if [ ! -f .env ]; then
        log_error ".env file not found. Please create one from .env.example"
        exit 1
    

    # Check if required directories exist
    for dir in "frontend" "backend" "nginx/conf.d" "certbot"; do
        if [ ! -d "$dir" ]; then
            log_error "Directory '$dir' not found"
            exit 1
        fi
    done
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create required directories
    mkdir -p uploads media static
    
    # Generate package-lock.json if needed
    if [ ! -f frontend/package-lock.json ]; then
        (cd frontend && npm install --package-lock-only)
    fi
}

# Stop running containers
stop_containers() {
    log_info "Stopping existing containers..."
    docker compose down
    
    read -p "🗑️  Remove old Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose down --rmi all
        docker system prune -f
    fi
}

# Start containers
start_containers() {
    log_info "Building and starting containers..."
    docker compose up -d --build

    # Wait for containers to start
    log_info "Waiting for services to start..."
    sleep 15
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Check database
    if ! docker compose exec db pg_isready -U goatuser -d goatmeasure &> /dev/null; then
        log_error "Database is not ready"
        return 1
    

    # Check Redis
    if ! docker compose exec redis redis-cli ping &> /dev/null; then
        log_error "Redis is not ready"
        return 1
    

    # Check backend API
    if ! curl -f http://localhost:8000/health/ &> /dev/null; then
        log_error "Backend API is not responding"
        return 1
    

    # Check frontend
    if ! curl -f http://localhost &> /dev/null; then
        log_error "Frontend is not responding"
        return 1
    fi  # Added missing fi

    return 0
}

# Main deployment process
main() {
    log_info "🐳 Starting GoatMeasure Pro deployment..."

    check_prerequisites
    setup_environment
    stop_containers
    start_containers

    # Check services health
    if check_health; then
        log_info "✅ GoatMeasure Pro is running successfully!"
        log_info "🌐 Access your application at: http://goatmorpho.info"
        log_info "📊 API health check: http://goatmorpho.info/api/health"
    else
        log_error "Deployment failed. Showing recent logs:"
        docker compose logs --tail=50
        exit 1
    fi

    # Show helpful commands
    echo -e "\n📚 Useful commands:"
    echo "  View logs:     docker compose logs -f"
    echo "  Restart:       docker compose restart"
    echo "  Stop:         docker compose down"
    echo "  Update:       git pull && ./docker-deploy.sh"
    echo "  View status:  docker compose ps"
}

# Run main function
main "$@"