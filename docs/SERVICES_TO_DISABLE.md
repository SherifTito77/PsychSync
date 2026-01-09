# Linux Services to Disable for Minimal Attack Surface

**Purpose:** Comprehensive guide on unnecessary Linux services that should be disabled on production SaaS servers
**Date:** 2025-12-27
**Platform:** Ubuntu Server 20.04 LTS / 22.04 LTS
**Goal:** Reduce attack surface by disabling unused services

---

## 📋 Executive Summary

Production servers should run **only the services necessary** for their purpose. Every additional service running is a potential attack vector. This document provides a comprehensive list of Linux services that should be disabled on production SaaS servers.

**Principle:** **If you don't need it, disable it.**

**Risk Reduction:** Disabling unnecessary services can reduce attack surface by 60-80%

---

## 🔴 CRITICAL: Services That MUST Be Disabled

These services present **significant security risks** and should **always** be disabled unless absolutely required.

### 1. Telnet Server (`telnetd`)

**Why Disable:**
- Transmits data in **clear text** (including passwords)
- No encryption
- Obsolete protocol replaced by SSH
- Severely vulnerable to eavesdropping and man-in-the-middle attacks

**Check if running:**
```bash
systemctl status inetd
systemctl status telnetd
dpkg -l | grep telnetd
```

**Disable:**
```bash
sudo systemctl stop inetd
sudo systemctl disable inetd
sudo apt-get purge telnetd -y
```

**Replacement:** SSH (with key-based authentication)

---

### 2. RSH Server (`rsh-server`)

**Why Disable:**
- **Zero security** - no authentication
- Transmits everything in clear text
- Trusted hosts bypass authentication entirely
- Severely vulnerable to IP spoofing

**Check if running:**
```bash
systemctl status rsh
systemctl status rlogin
systemctl status rexec
dpkg -l | grep rsh-server
```

**Disable:**
```bash
sudo systemctl stop rsh
sudo systemctl disable rsh
sudo systemctl stop rlogin
sudo systemctl disable rlogin
sudo systemctl stop rexec
sudo systemctl disable rexec
sudo apt-get purge rsh-server -y
```

**Replacement:** SSH, SCP, SFTP

---

### 3. FTP Server (`vsftpd`, `proftpd`, `pure-ftpd`)

**Why Disable:**
- Transmits credentials in **clear text**
- Vulnerable to packet sniffing
- Unless using FTPS (FTP over SSL/TLS)
- Better alternatives exist (SFTP, SCP)

**Check if running:**
```bash
systemctl status vsftpd
systemctl status proftpd
systemctl status pure-ftpd
dpkg -l | grep -E "(vsftpd|proftpd|pure-ftpd)"
```

**Disable:**
```bash
# For vsftpd
sudo systemctl stop vsftpd
sudo systemctl disable vsftpd
sudo apt-get purge vsftpd -y

# For proftpd
sudo systemctl stop proftpd
sudo systemctl disable proftpd
sudo apt-get purge proftpd -y

# For pure-ftpd
sudo systemctl stop pure-ftpd
sudo systemctl disable pure-ftpd
sudo apt-get purge pure-ftpd -y
```

**Replacement:** SFTP (Subsystem in SSH), SCP

**Exception:** If FTPS (FTP over TLS) is required for legacy compatibility, ensure:
- SSL/TLS is **enforced**
- Clear text FTP is **disabled**
- Only secure ciphers are enabled

---

### 4. TFTP Server (`tftpd`)

**Why Disable:**
- **Trivial FTP** - no authentication whatsoever
- Used primarily for PXE boot (not needed in production)
- Anyone can read/write files

**Check if running:**
```bash
systemctl status tftpd
dpkg -l | grep tftp
```

**Disable:**
```bash
sudo systemctl stop tftpd
sudo systemctl disable tftpd
sudo apt-get purge tftpd -y
```

---

## 🟠 HIGH: Services That Should Be Disabled

These services present **moderate security risks** or are typically unnecessary on production servers.

### 5. Avahi Daemon (mDNS/DNS-SD)

**Why Disable:**
- Zeroconf networking (unnecessary on servers)
- Exposes services on local network
- Can be used for network reconnaissance
- Generally not needed on production servers

**Check if running:**
```bash
systemctl status avahi-daemon
dpkg -l | grep avahi
```

**Disable:**
```bash
sudo systemctl stop avahi-daemon
sudo systemctl disable avahi-daemon
sudo apt-get purge avahi-daemon -y
```

---

### 6. CUPS (Print Server)

**Why Disable:**
- Production servers typically don't need printing
- Historically vulnerable to exploitation
- Unnecessary network exposure
- Resource intensive

**Check if running:**
```bash
systemctl status cups
systemctl status cups-browsed
dpkg -l | grep cups
```

**Disable:**
```bash
sudo systemctl stop cups
sudo systemctl disable cups
sudo systemctl stop cups-browsed
sudo systemctl disable cups-browsed
sudo apt-get purge cups -y
```

---

### 7. Bluetooth Services

**Why Disable:**
- Servers don't use Bluetooth
- Potential attack vector (BlueBorne, etc.)
- Unnecessary radio frequency exposure
- Historically vulnerable

**Check if running:**
```bash
systemctl status bluetooth
dpkg -l | grep bluez
```

**Disable:**
```bash
sudo systemctl stop bluetooth
sudo systemctl disable bluetooth
sudo apt-get purge bluez -y
```

**Also disable kernel module:**
```bash
echo "blacklist bluetooth" | sudo tee /etc/modprobe.d/bluetooth.conf
```

---

### 8. PCMCIA Services

**Why Disable:**
- Legacy hardware support (obsolete)
- Production servers don't use PCMCIA cards
- Unnecessary kernel modules

**Check if running:**
```bash
systemctl status pcmcia
```

**Disable:**
```bash
sudo systemctl stop pcmcia
sudo systemctl disable pcmcia
```

---

### 9. ISDN Services

**Why Disable:**
- Legacy telephony hardware
- Not relevant for modern production servers
- Unnecessary attack surface

**Check if running:**
```bash
systemctl status isdn
dpkg -l | grep isdn
```

**Disable:**
```bash
sudo systemctl stop isdn
sudo systemctl disable isdn
sudo apt-get purge isdnutils -y
```

---

## 🟡 MEDIUM: Services to Consider Disabling

These services may be needed in some scenarios but should be evaluated for necessity.

### 10. Network Manager (`network-manager`)

**Why Consider Disabling:**
- Servers typically use static network configuration
- Unnecessary overhead
- Better to use `/etc/network/interfaces` or netplan

**When to Keep:**
- Laptop or desktop environment
- Dynamic network configuration needed
- Cloud instances with dynamic networking

**Check if running:**
```bash
systemctl status NetworkManager
```

**Disable (if using static networking):**
```bash
sudo systemctl stop NetworkManager
sudo systemctl disable NetworkManager
```

---

### 11. DHCP Client (when using static IP)

**Why Consider Disabling:**
- Servers should use static IPs
- DHCP adds unnecessary complexity
- Predictable IP addressing is better

**When to Keep:**
- Dynamic IP from cloud provider (AWS, GCP, Azure)
- Non-critical development servers

**Check if running:**
```bash
systemctl status dhclient
```

**Disable (if using static IP):**
```bash
sudo systemctl stop dhclient
sudo systemctl disable dhclient
```

---

### 12. Sendmail/Postfix (if not acting as mail server)

**Why Consider Disabling:**
- Running a mail server adds significant attack surface
- Most applications can use external email services (SendGrid, Mailgun, AWS SES)
- Mail servers require continuous security patching

**When to Keep:**
- Server IS the mail server
- Need to receive email directly
- Air-gapped environment requiring local mail

**Check if running:**
```bash
systemctl status sendmail
systemctl status postfix
dpkg -l | grep -E "(sendmail|postfix)"
```

**Disable (if using external email service):**
```bash
# For Sendmail
sudo systemctl stop sendmail
sudo systemctl disable sendmail
sudo apt-get purge sendmail -y

# For Postfix
sudo systemctl stop postfix
sudo systemctl disable postfix
sudo apt-get purge postfix -y

# Install nullmailer instead (for local mail only)
sudo apt-get install nullmailer -y
```

**Recommendation for SaaS:** Use external email services (SendGrid, Mailgun, AWS SES) instead of running your own mail server.

---

### 13. NIS (Network Information Service)

**Why Consider Disabling:**
- Legacy centralized authentication
- Replaced by LDAP or Active Directory
- Known security vulnerabilities
- Rarely needed in modern environments

**Check if running:**
```bash
systemctl status nis
systemctl status ypbind
dpkg -l | grep nis
```

**Disable:**
```bash
sudo systemctl stop nis
sudo systemctl stop ypbind
sudo systemctl disable nis
sudo systemctl disable ypbind
sudo apt-get purge nis -y
```

**Replacement:** LDAP, FreeIPA, Active Directory, or local authentication

---

### 14. RPCbind (`rpcbind`)

**Why Consider Disabling:**
- Used for NFS (Network File System)
- Not needed unless using NFS
- Historically vulnerable
- Exposes network services

**When to Keep:**
- Using NFS for file sharing
- Using NIS (see above)

**Check if running:**
```bash
systemctl status rpcbind
```

**Disable (if not using NFS):**
```bash
sudo systemctl stop rpcbind
sudo systemctl disable rpcbind
```

---

## 🟢 LOW: Development/Debug Services

These services should **never** be enabled in production.

### 15. Debugging Shells

**Why Disable:**
- Provide unnecessary remote access
- Often have weaker security requirements
- Should be disabled in production

**Services to check:**
```bash
# Kdump (crash kernel)
sudo systemctl status kdump

# Kernel debugging
sudo systemctl status kexec

# Coredump
sudo systemctl status systemd-coredump
```

**Disable:**
```bash
sudo systemctl stop kdump
sudo systemctl disable kdump
sudo systemctl stop kexec
sudo systemctl disable kexec
```

---

### 16. Development Services

**Why Disable:**
- Development tools expose information about your system
- Should never be accessible in production
- Provide reconnaissance opportunities for attackers

**Services to disable:**

```bash
# Webmin (web-based system administration)
sudo systemctl stop webmin
sudo systemctl disable webmin
sudo apt-get purge webmin -y

# PHP Xdebug
# Remove from php.ini

# Development servers (test frameworks)
sudo systemctl stop python-test-server
sudo systemctl disable python-test-server
```

---

## 📊 Complete Disable Script

Here's a comprehensive script to disable all unnecessary services:

```bash
#!/bin/bash

################################################################################
# Disable Unnecessary Services for Minimal Attack Surface
# WARNING: Review before running - some services may be needed in your environment
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Services to disable
SERVICES=(
    "inetd"
    "telnetd"
    "rsh"
    "rlogin"
    "rexec"
    "vsftpd"
    "proftpd"
    "pure-ftpd"
    "tftpd"
    "avahi-daemon"
    "cups"
    "cups-browsed"
    "bluetooth"
    "pcmcia"
    "isdn"
    "nis"
    "ypbind"
    "rpcbind"
)

# Packages to remove (if installed)
PACKAGES_TO_REMOVE=(
    "telnetd"
    "rsh-server"
    "vsftpd"
    "proftpd"
    "pure-ftpd"
    "tftpd"
    "avahi-daemon"
    "cups"
    "bluez"
    "isdnutils"
    "nis"
    "webmin"
)

log_info "Disabling unnecessary services..."

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        log_info "Stopping $service..."
        sudo systemctl stop "$service"
        sudo systemctl disable "$service"
        echo "✓ Disabled $service"
    else
        echo "- $service not running"
    fi
done

log_info "Removing unnecessary packages..."

for package in "${PACKAGES_TO_REMOVE[@]}"; do
    if dpkg -l | grep -q "^ii.*$package"; then
        log_info "Removing $package..."
        sudo apt-get purge "$package" -y
        echo "✓ Removed $package"
    else
        echo "- $package not installed"
    fi
done

# Additional hardening
log_info "Applying additional service hardening..."

# Disable Bluetooth kernel module
echo "blacklist bluetooth" | sudo tee /etc/modprobe.d/bluetooth.conf

# Disable IPv6 (if not needed)
# Uncomment if you don't use IPv6
# echo "net.ipv6.conf.all.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.conf
# sudo sysctl -p

log_info "Service hardening complete!"
log_warning "Please review changes and reboot if necessary"
```

---

## ✅ Verification Checklist

After disabling services, verify:

- [ ] Server functionality is intact
- [ ] Required applications still work
- [ ] No errors in system logs: `sudo journalctl -xe`
- [ ] Network connectivity maintained: `ping -c 4 google.com`
- [ ] SSH access still works: `ssh -p 2222 user@server`
- [ ] Web server running (if applicable): `sudo systemctl status nginx`
- [ ] Database running (if applicable): `sudo systemctl status postgresql`
- [ ] Application responding: `curl http://localhost:8000/health`

---

## 🔍 Services Audit Commands

### List all running services:
```bash
systemctl list-units --type=service --state=running
```

### List all enabled services:
```bash
systemctl list-unit-files --type=service --state=enabled
```

### List all listening network sockets:
```bash
sudo ss -tulpn
```

### List all open ports:
```bash
sudo netstat -tulpn
```

### Check service status:
```bash
sudo systemctl status <service-name>
```

### Find services using resources:
```bash
ps aux --sort=-%mem | head -20
ps aux --sort=-%cpu | head -20
```

---

## 📊 Risk Reduction Summary

| Service Category | Risk Level | Attack Surface Reduction |
|------------------|------------|-------------------------|
| **Clear Text Protocols** | CRITICAL | 30-40% |
| **Legacy Services** | HIGH | 10-15% |
| **Desktop Services** | MEDIUM | 5-10% |
| **Development Tools** | HIGH | 5-10% |
| **Unnecessary Network Services** | MEDIUM | 10-15% |

**Total Potential Attack Surface Reduction: 60-80%**

---

## 🎯 Recommendations for SaaS Production Servers

### Minimum Required Services:

1. **SSH** (custom port, key-based auth only)
2. **Nginx/Apache** (web server)
3. **PostgreSQL/MySQL** (database)
4. **Redis** (caching, if needed)
5. **Systemd-journald** (logging)
6. **Rsyslog** (system logging)
7. **Cron** (scheduled tasks)
8. **Network Time Protocol** (NTP/chrony)

### Security Services to Run:

1. **Fail2ban** (intrusion prevention)
2. **UFW** (firewall)
3. **Auditd** (file access monitoring)
4. **Rkhunter/Chkrootkit** (rootkit detection)

### Monitoring Services (Optional):

1. **Prometheus/node_exporter** (metrics)
2. **Filebeat** (log forwarding)
3. **Osquery** (endpoint visibility)

---

## 🔄 Automated Monitoring

### Check for new services after updates:
```bash
#!/bin/bash
# Add to cron to run daily
BEFORE="/tmp/services-before.txt"
AFTER="/tmp/services-after.txt"

# Save current state
systemctl list-units --type=service --state=running > "$BEFORE"

# After apt upgrade, compare
systemctl list-units --type=service --state=running > "$AFTER"

diff "$BEFORE" "$AFTER" && echo "No new services" || mail -s "New services detected" admin@example.com
```

---

## 📝 Change Management

Before disabling any service:

1. **Document the current state:**
   ```bash
   systemctl list-units --type=service > /root/before-services.txt
   ```

2. **Test in non-production first**

3. **Have rollback plan:**
   ```bash
   systemctl enable <service>
   systemctl start <service>
   ```

4. **Monitor after changes:**
   ```bash
   journalctl -f
   ```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Maintained By:** Security Team

## Additional Resources

- CIS Ubuntu Benchmark: https://www.cisecurity.org/benchmark/ubuntu_linux
- NIST Security Configuration Checklist: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-70.pdf
- Ubuntu Server Guide: https://ubuntu.com/server/docs
