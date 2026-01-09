#!/bin/bash

################################################################################
# Unauthorized Login Detection Script
# Purpose: Detect and alert on suspicious login activity
# Usage: Run via cron hourly: 0 * * * * /path/to/detect-unauthorized-logins.sh
#
# Features:
# - Detects failed login attempts
# - Detects successful logins from unusual locations
# - Detects brute force attacks
# - Detects logins at unusual times
# - Detects multiple concurrent sessions
# - Generates alerts and reports
################################################################################

set -euo pipefail

# Configuration
ALERT_EMAIL="${ALERT_EMAIL:-security@yourdomain.com}"
LOG_DIR="/var/log/security-scanner"
REPORT_DIR="$LOG_DIR/reports"
ALERT_LOG="$LOG_DIR/unauthorized-login-alerts.log"
SUMMARY_REPORT="$REPORT_DIR/daily-login-summary-$(date +%Y%m%d).txt"

# Thresholds
MAX_FAILED_ATTEMPTS=5
MAX_FAILED_FROM_IP=10
MAX_CONCURRENT_SESSIONS=3
UNUSUAL_HOUR_START=22  # 10 PM
UNUSUAL_HOUR_END=6     # 6 AM

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

################################################################################
# Helper Functions
################################################################################

log_alert() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $message" | tee -a "$ALERT_LOG"
}

log_warning() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $message" | tee -a "$ALERT_LOG"
}

log_info() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $message"
}

send_email_alert() {
    local subject="$1"
    local message="$2"

    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "[SECURITY ALERT] $subject" "$ALERT_EMAIL"
        log_info "Email alert sent to $ALERT_EMAIL"
    else
        log_warning "Email not configured. Alert: $subject"
    fi
}

get_server_ip() {
    hostname -I | awk '{print $1}'
}

################################################################################
# Detection Functions
################################################################################

# Function 1: Detect failed login attempts
detect_failed_logins() {
    log_info "Checking for failed login attempts..."

    local failed_logins_file="$REPORT_DIR/failed-logins-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    # Get failed logins in the last hour
    grep "Failed password\|Failed publickey" /var/log/auth.log \
        | grep -v "Invalid user" \
        | grep "since=$since_time" \
        | awk '{print $1, $2, $3, $9, $11, $13, $15, $NF}' \
        > "$failed_logins_file" 2>/dev/null || true

    local failed_count=$(wc -l < "$failed_logins_file" 2>/dev/null || echo "0")

    if [[ $failed_count -gt $MAX_FAILED_ATTEMPTS ]]; then
        log_alert "High number of failed logins: $failed_count attempts in last hour"

        # Get top offending IPs
        local top_ips=$(awk '{print $NF}' "$failed_logins_file" \
            | sort | uniq -c | sort -rn | head -5)

        echo "═══════════════════════════════════════════════════" >> "$ALERT_LOG"
        echo "FAILED LOGIN ATTEMPTS DETECTED" >> "$ALERT_LOG"
        echo "Time Range: Last 1 hour" >> "$ALERT_LOG"
        echo "Total Attempts: $failed_count" >> "$ALERT_LOG"
        echo "Top Offending IPs:" >> "$ALERT_LOG"
        echo "$top_ips" >> "$ALERT_LOG"
        echo "═══════════════════════════════════════════════════" >> "$ALERT_LOG"

        send_email_alert "Failed Login Attempts - $(hostname)" \
            "Detected $failed_count failed login attempts in the last hour.\n\nTop IPs:\n$top_ips"

        return 1
    else
        log_info "Failed logins within normal range: $failed_count"
        return 0
    fi
}

# Function 2: Detect brute force attacks from single IP
detect_brute_force() {
    log_info "Checking for brute force attacks..."

    local brute_logins_file="$REPORT_DIR/brute-force-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    # Check for multiple failed attempts from single IP
    grep "Failed password" /var/log/auth.log \
        | grep "since=$since_time" \
        | awk '{for(i=1;i<=NF;i++) if($i ~ /rhost=/) {print $i}}' \
        | sed 's/rhost=//' | sed 's/$//' \
        | sort | uniq -c | sort -rn \
        > "$brute_logins_file" 2>/dev/null || true

    # Check if any IP exceeds threshold
    local brute_ips=$(awk -v threshold="$MAX_FAILED_FROM_IP" '$1 > threshold {print $2}' "$brute_logins_file")

    if [[ -n "$brute_ips" ]]; then
        log_alert "Brute force attack detected from IPs:"

        while read -r ip; do
            local attempts=$(grep "$ip" "$brute_logins_file" | awk '{print $1}')
            log_alert "  - $ip: $attempts failed attempts"
        done <<< "$brute_ips"

        # Check if IP is already blocked by fail2ban
        if command -v fail2ban-client &> /dev/null; then
            log_info "Checking Fail2Ban status..."
            fail2ban-client status sshd | grep "$ip" || log_warning "IP $ip not blocked by Fail2Ban"
        fi

        send_email_alert "Brute Force Attack - $(hostname)" \
            "Brute force attack detected from:\n$brute_ips"

        return 1
    else
        log_info "No brute force attacks detected"
        return 0
    fi
}

# Function 3: Detect successful logins from new/unusual locations
detect_unusual_logins() {
    log_info "Checking for unusual login locations..."

    local logins_file="$REPORT_DIR/recent-logins-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    # Get successful logins in the last hour
    grep "Accepted\|session opened" /var/log/auth.log \
        | grep "since=$since_time" \
        | tail -20 \
        > "$logins_file" 2>/dev/null || true

    local login_count=$(wc -l < "$logins_file" 2>/dev/null || echo "0")

    if [[ $login_count -gt 0 ]]; then
        log_info "Found $login_count successful logins in last hour"

        # Extract IPs and usernames
        awk '{print $9, $11}' "$logins_file" | while read -r user ip; do
            # Check if IP is in known locations (whitelist)
            # This is a simplified check - customize based on your needs
            if [[ "$ip" =~ ^(192\.168\.|10\.|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[01]\.) ]]; then
                log_info "  - Login from internal IP: $user from $ip"
            else
                log_warning "  - Login from external IP: $user from $ip"

                # Could add GeoIP check here
                # Example: if ! is_known_country "$ip"; then alert
            fi
        done

        return 0
    else
        log_info "No recent logins to analyze"
        return 0
    fi
}

# Function 4: Detect logins at unusual times
detect_unusual_time_logins() {
    log_info "Checking for logins at unusual times..."

    local current_hour=$(date +%H)
    local logins_file="$REPORT_DIR/unusual-time-logins-$(date +%Y%m%d-%H%M).txt"

    # Only check during unusual hours (10 PM - 6 AM)
    if [[ $current_hour -ge $UNUSUAL_HOUR_START ]] || [[ $current_hour -lt $UNUSUAL_HOUR_END ]]; then
        # Get logins in the last hour
        local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

        grep "Accepted\|session opened" /var/log/auth.log \
            | grep "since=$since_time" \
            > "$logins_file" 2>/dev/null || true

        local login_count=$(wc -l < "$logins_file" 2>/dev/null || echo "0")

        if [[ $login_count -gt 0 ]]; then
            log_warning "Detected $login_count logins during unusual hours ($current_hour:00)"

            echo "═══════════════════════════════════════════════════" >> "$ALERT_LOG"
            echo "UNUSUAL TIME LOGINS" >> "$ALERT_LOG"
            echo "Current Time: $(date)" >> "$ALERT_LOG"
            cat "$logins_file" >> "$ALERT_LOG"
            echo "═══════════════════════════════════════════════════" >> "$ALERT_LOG"

            # Don't send email for every unusual time login (too noisy)
            # Just log it for review
            return 0
        fi
    fi

    return 0
}

# Function 5: Detect multiple concurrent sessions
detect_concurrent_sessions() {
    log_info "Checking for multiple concurrent sessions..."

    # Count active SSH sessions per user
    local sessions_file="$REPORT_DIR/concurrent-sessions-$(date +%Y%m%d-%H%M).txt"

    who | awk '{print $1}' | sort | uniq -c > "$sessions_file" 2>/dev/null || true

    local excessive_sessions=$(awk -v threshold="$MAX_CONCURRENT_SESSIONS" '$1 > threshold {print $2}' "$sessions_file")

    if [[ -n "$excessive_sessions" ]]; then
        log_warning "Users with excessive concurrent sessions:"
        while read -r user; do
            local count=$(grep "$user" "$sessions_file" | awk '{print $1}')
            log_warning "  - $user: $count sessions"
        done <<< "$excessive_sessions"

        return 1
    else
        log_info "No excessive concurrent sessions detected"
        return 0
    fi
}

# Function 6: Detect root access attempts
detect_root_access() {
    log_info "Checking for root access attempts..."

    local root_attempts_file="$REPORT_DIR/root-attempts-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    # Check for direct root login attempts
    grep "root.*from.*Failed\|Failed.*root" /var/log/auth.log \
        | grep "since=$since_time" \
        > "$root_attempts_file" 2>/dev/null || true

    local root_count=$(wc -l < "$root_attempts_file" 2>/dev/null || echo "0")

    if [[ $root_count -gt 0 ]]; then
        log_alert "Detected $root_count root access attempts"

        send_email_alert "Root Access Attempts - $(hostname)" \
            "Detected $root_count attempts to access root account.\n\n$(cat $root_attempts_file)"

        return 1
    else
        log_info "No root access attempts detected"
        return 0
    fi
}

# Function 7: Detect invalid user attempts
detect_invalid_users() {
    log_info "Checking for invalid user login attempts..."

    local invalid_file="$REPORT_DIR/invalid-users-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    grep "Invalid user" /var/log/auth.log \
        | grep "since=$since_time" \
        > "$invalid_file" 2>/dev/null || true

    local invalid_count=$(wc -l < "$invalid_file" 2>/dev/null || echo "0")

    if [[ $invalid_count -gt 10 ]]; then
        log_warning "High number of invalid user attempts: $invalid_count"

        # Get top attempted usernames
        local top_users=$(awk '{print $8}' "$invalid_file" | sort | uniq -c | sort -rn | head -10)

        log_warning "Most attempted invalid usernames:"
        echo "$top_users" | tee -a "$ALERT_LOG"

        return 1
    else
        log_info "Invalid user attempts within normal range: $invalid_count"
        return 0
    fi
}

# Function 8: Detect successful logins after previous failures
detect_breakins() {
    log_info "Checking for successful logins after failures (potential break-ins)..."

    local breakins_file="$REPORT_DIR/potential-breakins-$(date +%Y%m%d-%H%M).txt"
    local since_time="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')"

    # This is a simplified check - in production, you'd correlate failed/successful logins by IP
    # Get IPs that had failed logins then successful logins
    grep "Failed password" /var/log/auth.log \
        | grep "since=$since_time" \
        | awk '{for(i=1;i<=NF;i++) if($i ~ /rhost=/) {print $i}}' \
        | sed 's/rhost=//' | sed 's/$//' \
        | sort -u > "/tmp/failed_ips.txt" 2>/dev/null || true

    grep "Accepted" /var/log/auth.log \
        | grep "since=$since_time" \
        | awk '{for(i=1;i<=NF;i++) if($i ~ /rhost=/) {print $i}}' \
        | sed 's/rhost=//' | sed 's/$//' \
        | sort -u > "/tmp/success_ips.txt" 2>/dev/null || true

    # Find IPs in both lists
    comm -12 /tmp/failed_ips.txt /tmp/success_ips.txt > "$breakins_file" 2>/dev/null || true

    local breakin_count=$(wc -l < "$breakins_file" 2>/dev/null || echo "0")

    if [[ $breakin_count -gt 0 ]]; then
        log_alert "POTENTIAL BREAK-INS DETECTED!"
        log_alert "IPs with failed then successful logins: $breakin_count"

        while read -r ip; do
            log_alert "  - Suspicious IP: $ip"
        done < "$breakins_file"

        send_email_alert "Potential Break-in Detected - $(hostname)" \
            "IPs detected with failed logins followed by successful logins:\n$(cat $breakins_file)"

        return 1
    else
        log_info "No break-ins detected"
        return 0
    fi

    # Cleanup temp files
    rm -f /tmp/failed_ips.txt /tmp/success_ips.txt
}

# Function 9: Generate summary report
generate_summary_report() {
    log_info "Generating daily login summary report..."

    cat > "$SUMMARY_REPORT" << EOF
================================================================================
                    DAILY LOGIN SECURITY SUMMARY
================================================================================

Server: $(hostname)
IP Address: $(get_server_ip)
Date: $(date '+%Y-%m-%d')
Generated: $(date '+%Y-%m-%d %H:%M:%S')

================================================================================
OVERALL STATISTICS
================================================================================

Total Failed Logins Today: $(grep "Failed password" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)
Total Successful Logins Today: $(grep "Accepted" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)
Total Invalid User Attempts Today: $(grep "Invalid user" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)

================================================================================
CURRENT ACTIVE SESSIONS
================================================================================
$(who)

================================================================================
RECENT FAILED LOGINS (Last 10)
================================================================================
$(grep "Failed password" /var/log/auth.log | tail -10 || echo "None")

================================================================================
RECENT SUCCESSFUL LOGINS (Last 10)
================================================================================
$(grep "Accepted" /var/log/auth.log | tail -10 || echo "None")

================================================================================
TOP OFFENDING IPs (Failed attempts today)
================================================================================
$(grep "Failed password" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | awk '{for(i=1;i<=NF;i++) if($i ~ /rhost=/) {print $i}}' | sed 's/rhost=//' | sed 's/$//' | sort | uniq -c | sort -rn | head -10 || echo "None")

================================================================================
FAILED LOGIN BREAKDOWN BY USER
================================================================================
$(grep "Failed password" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | awk '{for(i=1;i<=NF;i++) if($i ~ /user=/) {print $i}}' | sed 's/user=//' | sort | uniq -c | sort -rn | head -10 || echo "None")

================================================================================
FAIL2BAN STATUS
================================================================================
$(if command -v fail2ban-client &> /dev/null; then fail2ban-client status || echo "Fail2Ban not running"; else echo "Fail2Ban not installed"; fi)

================================================================================
RECOMMENDATIONS
================================================================================
EOF

    # Add recommendations based on findings
    local failed_count=$(grep "Failed password" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)
    local invalid_count=$(grep "Invalid user" /var/log/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)

    if [[ $failed_count -gt 100 ]]; then
        echo "- ⚠️  High number of failed logins detected ($failed_count)" >> "$SUMMARY_REPORT"
        echo "- ⚠️  Consider tightening Fail2Ban rules" >> "$SUMMARY_REPORT"
        echo "- ⚠️  Review firewall rules and consider geo-blocking" >> "$SUMMARY_REPORT"
    fi

    if [[ $invalid_count -gt 50 ]]; then
        echo "- ⚠️  High number of invalid user attempts ($invalid_count)" >> "$SUMMARY_REPORT"
        echo "- ⚠️  Consider implementing port knocking" >> "$SUMMARY_REPORT"
        echo "- ⚠️  Consider changing SSH port" >> "$SUMMARY_REPORT"
    fi

    echo "" >> "$SUMMARY_REPORT"
    echo "For detailed alerts, see: $ALERT_LOG" >> "$SUMMARY_REPORT"
    echo "" >> "$SUMMARY_REPORT"
    echo "================================================================================" >> "$SUMMARY_REPORT"
    echo "END OF REPORT" >> "$SUMMARY_REPORT"
    echo "================================================================================" >> "$SUMMARY_REPORT"

    log_info "Summary report generated: $SUMMARY_REPORT"
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "═══════════════════════════════════════════════════════════"
    log_info "     UNAUTHORIZED LOGIN DETECTION SCAN STARTED"
    log_info "═══════════════════════════════════════════════════════════"
    log_info "Server: $(hostname)"
    log_info "Time: $(date)"
    log_info "═══════════════════════════════════════════════════════════"

    local alerts_triggered=0

    # Run all detection functions
    detect_failed_logins || ((alerts_triggered++))
    detect_brute_force || ((alerts_triggered++))
    detect_unusual_logins || ((alerts_triggered++))
    detect_unusual_time_logins || ((alerts_triggered++))
    detect_concurrent_sessions || ((alerts_triggered++))
    detect_root_access || ((alerts_triggered++))
    detect_invalid_users || ((alerts_triggered++))
    detect_breakins || ((alerts_triggered++))

    # Generate summary report
    generate_summary_report

    log_info "═══════════════════════════════════════════════════════════"
    log_info "     SCAN COMPLETE"
    log_info "═══════════════════════════════════════════════════════════"

    if [[ $alerts_triggered -gt 0 ]]; then
        log_alert "Total alerts triggered: $alerts_triggered"
    else
        log_info "✓ No alerts triggered - all checks passed"
    fi

    log_info "═══════════════════════════════════════════════════════════"
}

# Run main function
main "$@"

exit 0
