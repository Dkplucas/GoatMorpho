#!/bin/bash
# Redis Monitoring Script for GoatMorpho
# Place in /usr/local/bin/monitor_redis.sh and make executable
# Add to crontab: */5 * * * * /usr/local/bin/monitor_redis.sh

# Configuration
REDIS_PASSWORD="${REDIS_PASSWORD:-your_secure_redis_password_here}"
LOG_FILE="${LOG_FILE:-/var/log/redis_monitor.log}"
MAX_MEMORY_MB=${MAX_MEMORY_MB:-1024}
EMAIL_ALERT="${EMAIL_ALERT:-dossoukponganfleming@gmail.com}"

# Create log file if it doesn't exist
touch "$LOG_FILE"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

send_alert() {
    local message="$1"
    log_message "ALERT: $message"
    
    # Send email alert if mail command is available
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "GoatMorpho Redis Alert" "$EMAIL_ALERT"
    fi
    
    # Log to syslog
    logger -t "goatmorpho-redis" "$message"
}

check_redis() {
    log_message "Starting Redis health check..."
    
    # Check if Redis service is running
    if ! systemctl is-active --quiet redis-server; then
        send_alert "Redis service is not running - attempting to start"
        systemctl start redis-server
        sleep 5
        
        if ! systemctl is-active --quiet redis-server; then
            send_alert "Failed to start Redis service"
            return 1
        fi
    fi
    
    log_message "Redis service is running"
    
    # Check Redis connectivity
    if [ -n "$REDIS_PASSWORD" ]; then
        PING_RESULT=$(redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null)
    else
        PING_RESULT=$(redis-cli ping 2>/dev/null)
    fi
    
    if [ "$PING_RESULT" != "PONG" ]; then
        send_alert "Redis is not responding to ping - attempting restart"
        systemctl restart redis-server
        sleep 10
        
        # Test again after restart
        if [ -n "$REDIS_PASSWORD" ]; then
            PING_RESULT=$(redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null)
        else
            PING_RESULT=$(redis-cli ping 2>/dev/null)
        fi
        
        if [ "$PING_RESULT" != "PONG" ]; then
            send_alert "Redis still not responding after restart"
            return 1
        fi
    fi
    
    log_message "Redis is responding to ping"
    
    # Check memory usage
    if [ -n "$REDIS_PASSWORD" ]; then
        MEMORY_INFO=$(redis-cli -a "$REDIS_PASSWORD" info memory 2>/dev/null)
    else
        MEMORY_INFO=$(redis-cli info memory 2>/dev/null)
    fi
    
    if [ $? -eq 0 ]; then
        USED_MEMORY=$(echo "$MEMORY_INFO" | grep "used_memory:" | cut -d: -f2 | tr -d '\r')
        USED_MEMORY_HUMAN=$(echo "$MEMORY_INFO" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
        MAX_MEMORY=$(echo "$MEMORY_INFO" | grep "maxmemory:" | cut -d: -f2 | tr -d '\r')
        
        log_message "Redis memory usage: $USED_MEMORY_HUMAN"
        
        # Convert to MB for comparison
        USED_MEMORY_MB=$((USED_MEMORY / 1024 / 1024))
        
        if [ "$USED_MEMORY_MB" -gt "$MAX_MEMORY_MB" ]; then
            send_alert "Redis memory usage is high: ${USED_MEMORY_MB}MB (threshold: ${MAX_MEMORY_MB}MB)"
        fi
        
        # Check if maxmemory is set
        if [ "$MAX_MEMORY" = "0" ]; then
            log_message "WARNING: Redis maxmemory is not set (unlimited)"
        fi
    else
        send_alert "Could not retrieve Redis memory information"
    fi
    
    # Check connected clients
    if [ -n "$REDIS_PASSWORD" ]; then
        CLIENT_INFO=$(redis-cli -a "$REDIS_PASSWORD" info clients 2>/dev/null)
    else
        CLIENT_INFO=$(redis-cli info clients 2>/dev/null)
    fi
    
    if [ $? -eq 0 ]; then
        CONNECTED_CLIENTS=$(echo "$CLIENT_INFO" | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
        log_message "Connected clients: $CONNECTED_CLIENTS"
        
        # Alert if too many clients (adjust threshold as needed)
        if [ "$CONNECTED_CLIENTS" -gt 100 ]; then
            send_alert "High number of Redis clients: $CONNECTED_CLIENTS"
        fi
    fi
    
    # Test Django Redis connection
    if command -v python >/dev/null 2>&1; then
        cd /var/www/goatmorpho 2>/dev/null || cd /app 2>/dev/null
        
        if [ -f "manage.py" ]; then
            log_message "Testing Django Redis connection..."
            
            # Test Redis connection through Django
            DJANGO_TEST=$(python manage.py check_redis 2>&1 | grep "Redis connection successful")
            
            if [ -n "$DJANGO_TEST" ]; then
                log_message "Django Redis connection successful"
            else
                send_alert "Django Redis connection test failed"
            fi
        fi
    fi
    
    log_message "Redis health check completed successfully"
}

# Main execution
check_redis

# Cleanup old log entries (keep last 1000 lines)
if [ -f "$LOG_FILE" ]; then
    tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi
