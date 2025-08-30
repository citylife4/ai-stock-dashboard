#!/bin/bash

# OCI Load Balancer Certificate Renewal Script
# This script automates the process of updating SSL certificates on OCI Load Balancer
# Prerequisites:
# - OCI CLI configured with proper authentication
# - certbot installed and certificates generated
# - Required environment variables set

set -euo pipefail

# Suppress OCI CLI warning about API key security
export SUPPRESS_LABEL_WARNING=True

# Configuration - Set these variables according to your environment
LOAD_BALANCER_ID="${OCI_LB_ID:-}"
LISTENER_NAME="${OCI_LISTENER_NAME:-https}"
CERTIFICATE_NAME_PREFIX="${OCI_CERT_PREFIX:-letsencrypt-cert}"
DOMAIN_NAME="${DOMAIN_NAME:-}"
CERT_PATH="${CERT_PATH:-/etc/letsencrypt/live}"
COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-}"
OCI_CLI_PATH="${OCI_CLI_PATH:-/home/ubuntu/oracle/oracle-cli/bin/oci}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if required tools are installed
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v "$OCI_CLI_PATH" &> /dev/null; then
        error "OCI CLI is not installed or not found at: $OCI_CLI_PATH"
        exit 1
    fi
    
    if ! command -v certbot &> /dev/null; then
        error "certbot is not installed or not in PATH"
        exit 1
    fi
    
    # Check OCI CLI authentication
    if ! "$OCI_CLI_PATH" iam region list &> /dev/null; then
        error "OCI CLI is not properly configured. Please run '$OCI_CLI_PATH setup config'"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Function to validate required environment variables
validate_config() {
    log "Validating configuration..."
    
    local missing_vars=()
    
    [ -z "$LOAD_BALANCER_ID" ] && missing_vars+=("OCI_LB_ID")
    [ -z "$DOMAIN_NAME" ] && missing_vars+=("DOMAIN_NAME")
    [ -z "$COMPARTMENT_ID" ] && missing_vars+=("OCI_COMPARTMENT_ID")
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        error "Please set the following environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  export $var=<value>"
        done
        exit 1
    fi
    
    success "Configuration validation passed"
}

# Function to check if certificate files exist
check_certificate_files() {
    log "Checking certificate files for domain: $DOMAIN_NAME"
    
    local cert_dir="$CERT_PATH/$DOMAIN_NAME"
    local cert_file="$cert_dir/cert.pem"
    local privkey_file="$cert_dir/privkey.pem"
    local chain_file="$cert_dir/chain.pem"
    local fullchain_file="$cert_dir/fullchain.pem"
    
    if [ ! -d "$cert_dir" ]; then
        error "Certificate directory not found: $cert_dir"
        error "Please run certbot to generate certificates first"
        exit 1
    fi
    
    for file in "$cert_file" "$privkey_file" "$chain_file" "$fullchain_file"; do
        if [ ! -f "$file" ]; then
            error "Certificate file not found: $file"
            exit 1
        fi
    done
    
    success "Certificate files found and accessible"
    
    # Export file paths for use in other functions
    export CERT_FILE="$cert_file"
    export PRIVKEY_FILE="$privkey_file"
    export CHAIN_FILE="$chain_file"
    export FULLCHAIN_FILE="$fullchain_file"
}

# Function to create certificate bundle in OCI
create_certificate_bundle() {
    log "Creating new certificate bundle in OCI Load Balancer..."
    
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local new_cert_name="${CERTIFICATE_NAME_PREFIX}-${timestamp}"
    
    # Read certificate files
    local cert_content=$(cat "$FULLCHAIN_FILE")
    local private_key_content=$(cat "$PRIVKEY_FILE")
    
    # Create the certificate bundle
    local create_result=$("$OCI_CLI_PATH" lb certificate create \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --certificate-name "$new_cert_name" \
        --public-certificate "$cert_content" \
        --private-key "$private_key_content" \
        --wait-for-state SUCCEEDED \
        --max-wait-seconds 300 2>&1)
    
    if [ $? -eq 0 ]; then
        success "Certificate bundle '$new_cert_name' created successfully"
        export NEW_CERT_NAME="$new_cert_name"
        return 0
    else
        error "Failed to create certificate bundle: $create_result"
        return 1
    fi
}

# Function to get current listener configuration
get_current_listener_config() {
    log "Getting current listener configuration..."
    
    local lb_data=$("$OCI_CLI_PATH" lb load-balancer get \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --query 'data' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ "$lb_data" != "null" ]; then
        # Extract the specific listener configuration
        local listener_config=$(echo "$lb_data" | jq -r ".listeners.\"$LISTENER_NAME\" // empty")
        
        if [ -n "$listener_config" ] && [ "$listener_config" != "null" ]; then
            export CURRENT_CERT_NAME=$(echo "$listener_config" | jq -r '.["ssl-configuration"]["certificate-name"] // empty')
            success "Current listener configuration retrieved"
            if [ -n "$CURRENT_CERT_NAME" ]; then
                log "Current certificate: $CURRENT_CERT_NAME"
            else
                warning "No SSL certificate currently configured on listener"
            fi
            return 0
        else
            error "Listener '$LISTENER_NAME' not found in load balancer"
            return 1
        fi
    else
        error "Failed to get load balancer configuration"
        return 1
    fi
}

# Function to update listener with new certificate
update_listener() {
    log "Updating listener '$LISTENER_NAME' with new certificate..."
    
    # Get current listener configuration from load balancer
    local lb_data=$("$OCI_CLI_PATH" lb load-balancer get \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --query 'data')
    
    # Extract current listener configuration
    local listener_config=$(echo "$lb_data" | jq -r ".listeners.\"$LISTENER_NAME\"")
    
    if [ "$listener_config" = "null" ]; then
        error "Listener '$LISTENER_NAME' not found"
        return 1
    fi
    
    # Extract current configuration
    local port=$(echo "$listener_config" | jq -r '.port')
    local protocol=$(echo "$listener_config" | jq -r '.protocol')
    local default_backend_set=$(echo "$listener_config" | jq -r '.["default-backend-set-name"]')
    
    # Get current SSL protocols (preserve TLS 1.2 + 1.3 support)
    local current_protocols=$(echo "$listener_config" | jq -r '.["ssl-configuration"]["protocols"] // ["TLSv1.2","TLSv1.3"]')
    
    # Update the listener with new certificate and proper TLS protocols
    local update_result=$("$OCI_CLI_PATH" lb listener update \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --listener-name "$LISTENER_NAME" \
        --port "$port" \
        --protocol "$protocol" \
        --default-backend-set-name "$default_backend_set" \
        --ssl-certificate-name "$NEW_CERT_NAME" \
        --ssl-verify-peer-certificate false \
        --protocols "$current_protocols" \
        --wait-for-state SUCCEEDED \
        --max-wait-seconds 300 \
        --force 2>&1)
    
    if [ $? -eq 0 ]; then
        success "Listener updated successfully with new certificate"
        return 0
    else
        error "Failed to update listener: $update_result"
        return 1
    fi
}

# Function to delete old certificate bundle
delete_old_certificate() {
    if [ -z "${CURRENT_CERT_NAME:-}" ] || [ "$CURRENT_CERT_NAME" = "null" ]; then
        log "No old certificate to delete"
        return 0
    fi
    
    log "Deleting old certificate bundle: $CURRENT_CERT_NAME"
    
    # Wait a bit to ensure the listener update is fully propagated
    sleep 10
    
    local delete_result=$("$OCI_CLI_PATH" lb certificate delete \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --certificate-name "$CURRENT_CERT_NAME" \
        --wait-for-state SUCCEEDED \
        --max-wait-seconds 300 \
        --force 2>&1)
    
    if [ $? -eq 0 ]; then
        success "Old certificate '$CURRENT_CERT_NAME' deleted successfully"
        return 0
    else
        warning "Failed to delete old certificate (this might be expected): $delete_result"
        return 0  # Don't fail the script if old cert deletion fails
    fi
}

# Function to list all certificates for verification
list_certificates() {
    log "Listing all certificates in load balancer..."
    
    "$OCI_CLI_PATH" lb certificate list \
        --load-balancer-id "$LOAD_BALANCER_ID" \
        --query 'data[*].{Name:"certificate-name", State:"lifecycle-state"}' \
        --output table
}

# Function to verify certificate expiration
check_certificate_expiry() {
    log "Checking certificate expiry date..."
    
    local expiry_date=$(openssl x509 -in "$CERT_FILE" -noout -enddate | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry_date" +%s)
    local current_epoch=$(date +%s)
    local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ $days_until_expiry -lt 30 ]; then
        warning "Certificate expires in $days_until_expiry days"
    else
        success "Certificate is valid for $days_until_expiry more days"
    fi
}

# Main function
main() {
    log "Starting OCI Load Balancer Certificate Renewal Process"
    
    # Run all checks and operations
    check_prerequisites
    validate_config
    check_certificate_files
    check_certificate_expiry
    get_current_listener_config
    
    # Create new certificate bundle
    if ! create_certificate_bundle; then
        error "Certificate renewal failed at bundle creation step"
        exit 1
    fi
    
    # Update listener with new certificate
    if ! update_listener; then
        error "Certificate renewal failed at listener update step"
        exit 1
    fi
    
    # Clean up old certificate
    delete_old_certificate
    
    # Verify the final state
    list_certificates
    
    success "Certificate renewal process completed successfully!"
    success "Load balancer is now using certificate: $NEW_CERT_NAME"
}

# Function to display usage information
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --dry-run          Show what would be done without making changes"
    echo "  --list-certs       List current certificates and exit"
    echo "  --test-config      Test configuration and show current certificate"
    echo ""
    echo "Required Environment Variables:"
    echo "  OCI_LB_ID          OCI Load Balancer OCID"
    echo "  DOMAIN_NAME        Domain name for the certificate"
    echo "  OCI_COMPARTMENT_ID Compartment OCID"
    echo ""
    echo "Optional Environment Variables:"
    echo "  OCI_LISTENER_NAME  Listener name (default: https)"
    echo "  OCI_CERT_PREFIX    Certificate name prefix (default: letsencrypt-cert)"
    echo "  CERT_PATH          Path to certificates (default: /etc/letsencrypt/live)"
    echo "  OCI_CLI_PATH       Path to OCI CLI executable (default: /home/ubuntu/oracle/oracle-cli/bin/oci)"
    echo ""
    echo "Example:"
    echo "  export OCI_LB_ID=ocid1.loadbalancer.oc1..."
    echo "  export DOMAIN_NAME=example.com"
    echo "  export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..."
    echo "  $0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --dry-run)
            echo "Dry run mode not yet implemented"
            exit 0
            ;;
        --list-certs)
            check_prerequisites
            validate_config
            list_certificates
            exit 0
            ;;
        --test-config)
            check_prerequisites
            validate_config
            get_current_listener_config
            log "Current certificate: $CURRENT_CERT_NAME"
            echo "Load balancer configuration test completed successfully"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
