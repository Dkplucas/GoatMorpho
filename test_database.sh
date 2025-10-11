#!/bin/bash
# Test Database Connection Script for GoatMorpho
# Tests connection to existing PostgreSQL database

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Database credentials (existing setup)
DB_NAME="goat_morpho"
DB_USER="goat_morpho_user"
DB_PASSWORD="123456789"
DB_HOST="localhost"
DB_PORT="5432"

print_status "Testing connection to existing PostgreSQL database..."
print_status "Database: $DB_NAME"
print_status "User: $DB_USER"
print_status "Host: $DB_HOST"
print_status "Port: $DB_PORT"

# Test PostgreSQL service
if ! command -v psql >/dev/null 2>&1; then
    print_error "PostgreSQL client not installed"
    print_status "Install with: sudo apt install postgresql-client"
    exit 1
fi

# Test if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT >/dev/null 2>&1; then
    print_error "PostgreSQL server is not running or not accessible"
    print_status "Check if PostgreSQL is running: sudo systemctl status postgresql"
    exit 1
fi

print_success "PostgreSQL server is running"

# Test database connection
if PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" >/dev/null 2>&1; then
    print_success "Database connection successful"
    
    # Get database version
    DB_VERSION=$(PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version();" 2>/dev/null | head -1 | xargs)
    print_status "PostgreSQL Version: $DB_VERSION"
    
    # Check database size
    DB_SIZE=$(PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
    print_status "Database Size: $DB_SIZE"
    
    # Check if Django tables exist
    TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
    print_status "Tables in database: $TABLE_COUNT"
    
    if [ "$TABLE_COUNT" -gt "0" ]; then
        print_success "Database appears to have existing data"
        
        # List some key tables
        print_status "Key Django tables found:"
        PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%auth%' OR table_name LIKE '%django%' OR table_name LIKE '%goat%' OR table_name LIKE '%measurement%' ORDER BY table_name;" 2>/dev/null | head -10 | while read table; do
            if [ -n "$(echo $table | xargs)" ]; then
                echo "  - $(echo $table | xargs)"
            fi
        done
    else
        print_warning "Database exists but appears empty (no tables found)"
        print_status "You may need to run Django migrations"
    fi
    
else
    print_error "Cannot connect to database"
    print_error "Please verify:"
    print_error "  1. PostgreSQL is running: sudo systemctl status postgresql"
    print_error "  2. Database exists: $DB_NAME"
    print_error "  3. User exists: $DB_USER"
    print_error "  4. Password is correct: $DB_PASSWORD"
    print_error "  5. User has access to database"
    exit 1
fi

# Test Django database connection if manage.py exists
if [ -f "manage.py" ]; then
    print_status "Testing Django database connection..."
    
    # Set environment variables for Django
    export DB_NAME="$DB_NAME"
    export DB_USER="$DB_USER"
    export DB_PASSWORD="$DB_PASSWORD"
    export DB_HOST="$DB_HOST"
    export DB_PORT="$DB_PORT"
    
    # Test Django connection
    if python manage.py check --database default >/dev/null 2>&1; then
        print_success "Django database connection successful"
        
        # Check migrations
        UNAPPLIED=$(python manage.py showmigrations --plan 2>/dev/null | grep "\[ \]" | wc -l)
        if [ "$UNAPPLIED" -gt "0" ]; then
            print_warning "There are $UNAPPLIED unapplied migrations"
            print_status "Run: python manage.py migrate"
        else
            print_success "All migrations are applied"
        fi
        
    else
        print_warning "Django cannot connect to database"
        print_status "This might be due to missing dependencies or configuration issues"
    fi
else
    print_status "Django project not found in current directory"
fi

print_success "Database connection test completed"
print_status "Your existing PostgreSQL setup is ready for GoatMorpho deployment"
