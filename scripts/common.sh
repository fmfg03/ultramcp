#!/bin/bash

# Common utilities for UltraMCP scripts

LOG_FILE="logs/combined.log"
mkdir -p logs

# Ensure log file exists
touch "$LOG_FILE"

# Logging functions
log_info() {
    local service="$1"
    local message="$2"
    local timestamp=$(date -Iseconds)
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"info\",\"service\":\"$service\",\"message\":\"$message\"}" >> "$LOG_FILE"
}

log_error() {
    local service="$1" 
    local message="$2"
    local timestamp=$(date -Iseconds)
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"error\",\"service\":\"$service\",\"message\":\"$message\"}" >> "$LOG_FILE"
    echo "❌ ERROR: $message" >&2
}

log_success() {
    local service="$1"
    local message="$2" 
    local timestamp=$(date -Iseconds)
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"success\",\"service\":\"$service\",\"message\":\"$message\"}" >> "$LOG_FILE"
    echo "✅ $message"
}

# Error handling with recovery suggestions
handle_error() {
    local service="$1"
    local error_code="$2"
    local error_message="$3"
    local recovery_suggestions="$4"
    
    local timestamp=$(date -Iseconds)
    cat << EOF >> "$LOG_FILE"
{
  "timestamp": "$timestamp",
  "level": "error",
  "service": "$service",
  "error_code": "$error_code",
  "message": "$error_message",
  "recovery_suggestions": $recovery_suggestions,
  "context": {
    "pwd": "$(pwd)",
    "user": "$(whoami)",
    "system": "$(uname -s)"
  }
}
EOF

    echo "❌ ERROR [$error_code]: $error_message"
    echo "💡 Recovery suggestions:"
    echo "$recovery_suggestions" | jq -r '.[]' 2>/dev/null || echo "$recovery_suggestions"
}

# Check if required tools are available
check_requirements() {
    local missing_tools=()
    
    command -v node >/dev/null || missing_tools+=("node")
    command -v python3 >/dev/null || missing_tools+=("python3") 
    command -v jq >/dev/null || missing_tools+=("jq")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        handle_error "system" "MISSING_REQUIREMENTS" "Missing required tools" "$(printf '%s\n' "${missing_tools[@]}" | jq -R . | jq -s .)"
        exit 1
    fi
}

# Generate task ID for tracking
generate_task_id() {
    echo "task_$(date +%s)_$(shuf -i 1000-9999 -n 1 2>/dev/null || echo $RANDOM)"
}

# Check if service is running
is_service_running() {
    local service_name="$1"
    pgrep -f "$service_name" > /dev/null
}

# Start service if not running
ensure_service_running() {
    local service_name="$1"
    local start_command="$2"
    
    if ! is_service_running "$service_name"; then
        log_info "service-manager" "Starting $service_name"
        eval "$start_command" &
        sleep 2
        
        if is_service_running "$service_name"; then
            log_success "service-manager" "$service_name started successfully"
        else
            handle_error "service-manager" "START_FAILED" "Failed to start $service_name" '["Check command syntax", "Verify dependencies", "Check logs for errors"]'
            return 1
        fi
    fi
}

# Safe curl with timeout and error handling
safe_curl() {
    local url="$1"
    local timeout="${2:-30}"
    local max_retries="${3:-3}"
    
    for i in $(seq 1 $max_retries); do
        if curl -s --connect-timeout "$timeout" --max-time "$timeout" "$url"; then
            return 0
        fi
        
        if [ $i -lt $max_retries ]; then
            log_info "http-client" "Retry $i/$max_retries for $url"
            sleep 2
        fi
    done
    
    return 1
}

# Format and display JSON response
format_json_response() {
    local response="$1"
    local service="$2"
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo "$response" | jq .
    else
        log_error "$service" "Invalid JSON response: $response"
        echo "❌ Invalid response format"
        return 1
    fi
}

# Check if port is available
is_port_available() {
    local port="$1"
    ! nc -z localhost "$port" 2>/dev/null
}

# Wait for service to be ready
wait_for_service() {
    local service_url="$1"
    local max_wait="${2:-30}"
    local check_interval="${3:-2}"
    
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if safe_curl "$service_url/health" 5 1 >/dev/null 2>&1; then
            return 0
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    return 1
}

# Cleanup function for graceful shutdown
cleanup_and_exit() {
    local exit_code="${1:-0}"
    log_info "system" "Performing cleanup before exit"
    
    # Kill background processes if any
    jobs -p | xargs -r kill 2>/dev/null
    
    exit $exit_code
}

# Set up signal handlers
trap 'cleanup_and_exit 130' INT TERM

# Environment validation
validate_environment() {
    local required_vars=("$@")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        handle_error "environment" "MISSING_ENV_VARS" "Missing environment variables" "$(printf '%s\n' "${missing_vars[@]}" | jq -R . | jq -s .)"
        return 1
    fi
}

# File operation helpers
ensure_directory() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_info "filesystem" "Created directory: $dir"
    fi
}

backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup_name="${file}.backup.$(date +%s)"
        cp "$file" "$backup_name"
        log_info "filesystem" "Backed up $file to $backup_name"
    fi
}

# Progress indicator
show_progress() {
    local message="$1"
    local duration="${2:-3}"
    
    echo -n "$message"
    for i in $(seq 1 $duration); do
        echo -n "."
        sleep 1
    done
    echo " ✅"
}

# System information
get_system_info() {
    cat << EOF
{
  "hostname": "$(hostname)",
  "user": "$(whoami)", 
  "os": "$(uname -s)",
  "arch": "$(uname -m)",
  "uptime": "$(uptime -p 2>/dev/null || uptime)",
  "memory": "$(free -h 2>/dev/null | awk '/^Mem:/ {print $3"/"$2}' || echo 'unknown')",
  "disk": "$(df -h . 2>/dev/null | awk 'NR==2 {print $3"/"$2" ("$5" used)"}' || echo 'unknown')",
  "timestamp": "$(date -Iseconds)"
}
EOF
}