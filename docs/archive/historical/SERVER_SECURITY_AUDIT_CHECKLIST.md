# Production Server Security Audit Checklist

**Purpose:** Comprehensive security audit checklist for Ubuntu production servers hosting SaaS applications
**Date:** 2025-12-27
**Framework:** CIS Benchmarks, NIST 800-53, PCI DSS Requirements

---

## 📋 Executive Summary

This checklist provides a systematic approach to auditing and hardening Ubuntu production servers. Use this checklist to:
- Identify security weaknesses in current configuration
- Verify compliance with security standards (CIS, NIST, PCI DSS)
- Track hardening progress
- Maintain security baseline

**Audit Frequency:**
- **Full Audit:** Quarterly
- **Critical Controls:** Monthly
- **Log Monitoring:** Continuous/Daily

---

## 🔍 Section 1: Identity and Access Control

### 1.1 User Account Management

- [ ] **Remove default accounts**
  ```bash
  # Check for default accounts
  cat /etc/passwd | grep -E "(guest|test|demo|default)"
  ```

- [ ] **Remove unnecessary user accounts**
  ```bash
  # List all human users
  awk -F: '($3 >= 1000) && ($1 != "nobody") {print $1, $3}' /etc/passwd
  ```

- [ ] **Verify no accounts with empty passwords**
  ```bash
  sudo awk -F: '($2 == "") {print $1}' /etc/shadow
  ```

- [ ] **Ensure all accounts have password expiry set**
  ```bash
  sudo chage -l username | grep "Password expires"
  ```

- [ ] **Lock unused accounts**
  ```bash
  sudo usermod --lock username
  sudo chage --expiredate 1970-01-01 username
  ```

### 1.2 Root Account Security

- [ ] **Direct root login disabled in SSH**
  ```bash
  sudo grep "^PermitRootLogin" /etc/ssh/sshd_config
  # Expected: PermitRootLogin no
  ```

- [ ] **Root account password set (or disabled)**
  ```bash
  sudo passwd -S root
  # Good: NP (no password) or P (password)
  ```

- [ ] **Limit sudo access to specific users**
  ```bash
  sudo cat /etc/sudoers.d/*
  # Verify only authorized users have sudo
  ```

- [ ] **Require sudo password for all commands**
  ```bash
  sudo grep "!authenticate" /etc/sudoers /etc/sudoers.d/*
  # Should return empty (no passwordless sudo)
  ```

### 1.3 SSH Configuration

- [ ] **SSH protocol version 2 only**
  ```bash
  sudo grep "^Protocol" /etc/ssh/sshd_config
  # Expected: Protocol 2
  ```

- [ ] **Disable password authentication (key-based only)**
  ```bash
  sudo grep "^PasswordAuthentication" /etc/ssh/sshd_config
  # Expected: PasswordAuthentication no
  ```

- [ ] **Limit SSH access to specific users/groups**
  ```bash
  sudo grep "^AllowUsers" /etc/ssh/sshd_config
  # Expected: AllowUsers user1 user2
  ```

- [ ] **Set idle timeout interval**
  ```bash
  sudo grep "^ClientAliveInterval" /etc/ssh/sshd_config
  # Expected: ClientAliveInterval 300
  sudo grep "^ClientAliveCountMax" /etc/ssh/sshd_config
  # Expected: ClientAliveCountMax 3
  ```

- [ ] **Disable X11 forwarding**
  ```bash
  sudo grep "^X11Forwarding" /etc/ssh/sshd_config
  # Expected: X11Forwarding no
  ```

- [ ] **Use non-standard SSH port**
  ```bash
  sudo grep "^Port" /etc/ssh/sshd_config
  # Good: Port 2222 (or any non-22)
  ```

- [ ] **Enable SSH key hardening**
  ```bash
  sudo grep "^PubkeyAuthentication" /etc/ssh/sshd_config
  # Expected: PubkeyAuthentication yes
  ```

---

## 🔒 Section 2: Network Security

### 2.1 Firewall Configuration (UFW)

- [ ] **UFW enabled and active**
  ```bash
  sudo ufw status
  # Expected: Status: active
  ```

- [ ] **Default inbound policy set to DENY**
  ```bash
  sudo ufw status verbose
  # Expected: Default: deny (incoming)
  ```

- [ ] **Default outbound policy set to ALLOW (or DENY for strict)**
  ```bash
  sudo ufw status verbose
  # Expected: Default: allow (outgoing)
  ```

- [ ] **Only necessary ports open**
  ```bash
  sudo ufw status numbered
  # Verify only: HTTP (80), HTTPS (443), SSH (custom port), maybe 8000
  ```

- [ ] **Limit rate on SSH port**
  ```bash
  sudo ufw status | grep "LIMIT"
  # Should see rate limiting on SSH
  ```

- [ ] **Logging enabled for UFW**
  ```bash
  sudo ufw status | grep "Logging"
  # Expected: Logging: on (or on: low/medium/high)
  ```

### 2.2 IP Tables Rules

- [ ] **No permissive IP tables rules**
  ```bash
  sudo iptables -L -n -v
  # Check for ACCEPT rules without restrictions
  ```

- [ ] **Check for suspicious rules**
  ```bash
  sudo iptables -L INPUT -n -v | grep -E "(ACCEPT|DROP)"
  # Verify rules are appropriate
  ```

### 2.3 Network Configuration

- [ ] **Disable IP forwarding**
  ```bash
  sysctl net.ipv4.ip_forward
  # Expected: net.ipv4.ip_forward = 0
  ```

- [ ] **Disable source routing**
  ```bash
  sysctl net.ipv4.conf.all.accept_source_route
  # Expected: net.ipv4.conf.all.accept_source_route = 0
  ```

- [ ] **Enable SYN cookies**
  ```bash
  sysctl net.ipv4.tcp_syncookies
  # Expected: net.ipv4.tcp_syncookies = 1
  ```

- [ ] **Disable ICMP redirects**
  ```bash
  sysctl net.ipv4.conf.all.accept_redirects
  # Expected: net.ipv4.conf.all.accept_redirects = 0
  ```

- [ ] **Enable bad error message protection**
  ```bash
  sysctl net.ipv4.icmp_ignore_bogus_error_responses
  # Expected: net.ipv4.icmp_ignore_bogus_error_responses = 1
  ```

---

## 🚪 Section 3: Intrusion Detection & Prevention

### 3.1 Fail2Ban Configuration

- [ ] **Fail2ban installed and running**
  ```bash
  sudo systemctl status fail2ban
  # Expected: active (running)
  ```

- [ ] **SSH jail enabled**
  ```bash
  sudo fail2ban-client status sshd
  # Should show status
  ```

- [ ] **Recidive jail enabled (repeat offenders)**
  ```bash
  sudo fail2ban-client status recidive
  # Should show status
  ```

- [ ] **Appropriate ban time configured**
  ```bash
  sudo grep "bantime" /etc/fail2ban/jail.local
  # Recommended: 3600 (1 hour) or 86400 (24 hours)
  ```

- [ ] **Max retry attempts set**
  ```bash
  sudo grep "maxretry" /etc/fail2ban/jail.local
  # Recommended: 3-5 attempts
  ```

- [ ] **Find time configured**
  ```bash
  sudo grep "findtime" /etc/fail2ban/jail.local
  # Recommended: 600 (10 minutes)
  ```

- [ ] **Email alerts configured (optional)**
  ```bash
  sudo grep "destemail" /etc/fail2ban/jail.local
  # Should have valid email
  ```

### 3.2 Log Monitoring

- [ ] **Auth logs being monitored**
  ```bash
  sudo tail -f /var/log/auth.log
  # Should see login attempts
  ```

- [ ] **Syslog configured**
  ```bash
  sudo ls -la /var/log/syslog
  # Should exist and be recent
  ```

- [ ] **Logrotate configured**
  ```bash
  sudo ls -la /etc/logrotate.d/
  # Should have configs for apps
  ```

- [ ] **Disk space monitoring for logs**
  ```bash
  df -h /var/log
  # Should have sufficient space
  ```

---

## 📦 Section 4: Software and Package Management

### 4.1 System Updates

- [ ] **System packages up to date**
  ```bash
  sudo apt list --upgradable
  # Should return empty or minimal
  ```

- [ ] **Security patches applied**
  ```bash
  sudo apt list --upgradable | grep -i security
  # Should be empty
  ```

- [ ] **Unattended upgrades enabled**
  ```bash
  sudo systemctl status unattended-upgrades
  # Expected: active (running) or enabled
  ```

### 4.2 Package Security

- [ ] **No unnecessary packages installed**
  ```bash
  dpkg -l | grep -E "(telnet|ftp|rsh|rlogin)"
  # Should return empty (insecure protocols)
  ```

- [ ] **Repository sources are official**
  ```bash
  sudo cat /etc/apt/sources.list
  # Should use official Ubuntu repos
  ```

- [ ] **GPG keys for repositories valid**
  ```bash
  sudo apt-key list
  # Should show valid keys
  ```

### 4.3 Application Security

- [ ] **Services running as non-root users**
  ```bash
  sudo ps aux | awk '{print $1}' | sort | uniq
  # Minimize processes running as root
  ```

- [ ] **No services listening on 0.0.0.0**
  ```bash
  sudo ss -tulpn | grep "0.0.0.0"
  # Minimize services listening on all interfaces
  ```

- [ ] **Services bound to localhost only (where possible)**
  ```bash
  sudo ss -tulpn | grep "127.0.0.1"
  # Good: Databases, Redis, etc. on localhost
  ```

---

## 🔐 Section 5: File System Security

### 5.1 Permission Auditing

- [ ] **No world-writable files**
  ```bash
  sudo find / -type f -perm -002 2>/dev/null
  # Should return minimal (or none)
  ```

- [ ] **No world-writable directories**
  ```bash
  sudo find / -type d -perm -002 2>/dev/null | grep -v "^/proc"
  # Should return minimal
  ```

- [ ] **Check for SUID binaries**
  ```bash
  sudo find / -type f -perm -4000 2>/dev/null
  # Review list, remove unnecessary
  ```

- [ ] **Check for SGID binaries**
  ```bash
  sudo find / -type f -perm -2000 2>/dev/null
  # Review list
  ```

- [ ] **Home directory permissions are 750 or stricter**
  ```bash
  ls -ld /home/*
  # Should be drwxr-x--- or drwx------
  ```

- [ ] **Critical files have correct permissions**
  ```bash
  ls -l /etc/passwd /etc/shadow /etc/sudoers
  # Expected:
  # /etc/passwd: -rw-r--r--
  # /etc/shadow: -rw-r-----
  # /etc/sudoers: -r--r-----
  ```

### 5.2 Mount Points

- [ ] **Separate partition for /tmp**
  ```bash
  df -h /tmp
  # Should be separate partition
  ```

- [ ] **/tmp mounted with noexec, nodev, nosuid**
  ```bash
  mount | grep /tmp
  # Expected: noexec,nodev,nosuid
  ```

- [ ] **Separate partition for /var**
  ```bash
  df -h /var
  # Good: separate partition (prevents DoS)
  ```

- [ ] **Separate partition for /home**
  ```bash
  df -h /home
  # Good: separate partition
  ```

---

## 📊 Section 6: Logging and Monitoring

### 6.1 System Logs

- [ ] **Syslog running**
  ```bash
  sudo systemctl status rsyslog
  # Expected: active (running)
  ```

- [ ] **Auth.log exists and being written**
  ```bash
  sudo tail -20 /var/log/auth.log
  # Should show recent entries
  ```

- [ ] **Kernel log configured**
  ```bash
  sudo ls -la /var/log/kern.log
  # Should exist
  ```

### 6.2 Audit Logging

- [ ] **Auditd installed and running**
  ```bash
  sudo systemctl status auditd
  # Expected: active (running)
  ```

- [ ] **Audit rules configured**
  ```bash
  sudo auditctl -l
  # Should show rules
  ```

- [ ] **Audit logs being written**
  ```bash
  sudo ls -la /var/log/audit/
  # Should have logs
  ```

### 6.3 Log Retention

- [ ] **Log rotation configured**
  ```bash
  sudo cat /etc/logrotate.conf | grep -v "^#"
  # Should have rotation rules
  ```

- [ ] **Sufficient disk space for logs**
  ```bash
  df -h /var/log
  # Should have >20% free space
  ```

- [ ] **Remote log forwarding configured (optional)**
  ```bash
  sudo grep -r "^*.*@" /etc/rsyslog.d/
  # For centralized logging
  ```

---

## 🔧 Section 7: Service Hardening

### 7.1 Unnecessary Services Disabled

- [ ] **Telnet server not installed**
  ```bash
  dpkg -l | grep telnetd
  # Should return empty
  ```

- [ ] **FTP server not installed (or secured)**
  ```bash
  dpkg -l | grep ftpd
  # Should return empty (or vsftpd with SSL)
  ```

- [ ] **RSH/Rlogin not installed**
  ```bash
  dpkg -l | grep -E "(rsh-server|rsh-client)"
  # Should return empty
  ```

- [ ] **NIS not running (unless needed)**
  ```bash
  sudo systemctl status nis
  # Should be inactive or not found
  ```

### 7.2 Critical Services Configured

- [ ] **NTP service configured**
  ```bash
  sudo systemctl status chrony
  # or
  sudo systemctl status ntpsec
  # Expected: active (running)
  ```

- [ ] **Time synchronization working**
  ```bash
  timedatectl
  # Should show "System clock synchronized: yes"
  ```

---

## 🚨 Section 8: Incident Response Preparedness

### 8.1 Backup Configuration

- [ ] **Automated backups configured**
  ```bash
  sudo systemctl status backup.service
  # Should have backup service
  ```

- [ ] **Backups tested regularly**
  ```bash
  # Manual: Test restore procedure
  ```

- [ ] **Backups stored off-site**
  ```bash
  # Verify backup destination
  ```

- [ ] **Backup encryption enabled**
  ```bash
  # Check backup scripts for encryption
  ```

### 8.2 Security Tools

- [ ] **Lynis installed (security auditing)**
  ```bash
  which lynis
  # Should show path
  ```

- [ ] **RKHunter installed (rootkit detection)**
  ```bash
  which rkhunter
  # Should show path
  ```

- [ ] **CHKRootKit installed (rootkit detection)**
  ```bash
  which chkrootkit
  # Should show path
  ```

- [ ] **Security scans scheduled**
  ```bash
  sudo crontab -l | grep -E "(lynis|rkhunter|chkrootkit)"
  # Should have scheduled scans
  ```

---

## 🌐 Section 9: Web Server Security (if applicable)

### 9.1 Nginx/Apache Configuration

- [ ] **Server version hidden**
  ```bash
  curl -I http://localhost
  # Should NOT show server version
  ```

- [ ] **SSL/TLS configured**
  ```bash
  openssl s_client -connect localhost:443
  # Should show valid certificate
  ```

- [ ] **Strong SSL ciphers only**
  ```bash
  # Check nginx/apache config
  ```

- [ ] **HTTP security headers enabled**
  ```bash
  curl -I http://localhost | grep -E "(X-Frame-Options|X-XSS-Protection)"
  # Should show security headers
  ```

- [ ] **No default pages served**
  ```bash
  curl http://localhost
  # Should NOT show "Welcome to nginx"
  ```

### 9.2 Application Security

- [ ] **Application runs as non-root**
  ```bash
  ps aux | grep "nginx\|apache"
  # Should run as www-data or similar
  ```

- [ ] **Application firewall configured**
  ```bash
  # Check for WAF (ModSecurity, etc.)
  ```

---

## 📱 Section 10: Compliance and Documentation

### 10.1 Documentation

- [ ] **Server build documented**
  ```bash
  # Check for runbooks/README
  ```

- [ ] **Security procedures documented**
  ```bash
  # Check for incident response procedures
  ```

- [ ] **Change management process in place**
  ```bash
  # Check for change log
  ```

### 10.2 Compliance Evidence

- [ ] **Audit trail maintained**
  ```bash
  sudo lastlog | head -20
  # Should show login history
  ```

- [ ] **Security logs archived**
  ```bash
  ls -la /var/log/archive/
  # Should have archived logs
  ```

- [ ] **Periodic security reviews scheduled**
  ```bash
  sudo crontab -l | grep security
  # Should have scheduled reviews
  ```

---

## 🎯 Quick Security Scorecard

### Critical Security Controls (Must Have)

- [ ] Root login disabled via SSH
- [ ] Password authentication disabled (key-based auth only)
- [ ] Firewall enabled with restrictive rules
- [ ] Fail2ban running and configured
- [ ] System updates automated
- [ ] No unnecessary services running
- [ ] Auth logs monitored
- [ ] Backups automated and tested

**Score:** ___ / 8 critical controls

### High-Priority Controls (Should Have)

- [ ] Auditd running
- [ ] Separate partitions (/tmp, /var, /home)
- [ ] Intrusion detection tools installed
- [ ] Security scanning scheduled
- [ ] SSL/TLS properly configured
- [ ] Non-root service users
- [ ] Log rotation configured
- [ ] Incident response plan

**Score:** ___ / 8 high-priority controls

### Best Practices (Nice to Have)

- [ ] Centralized logging
- [ ] File Integrity Monitoring (FIM)
- [ ] Security Information and Event Management (SIEM)
- [ ] Automated security baseline enforcement
- [ ] Regular penetration testing
- [ ] Security training for operators

**Score:** ___ / 6 best practices

---

## 📝 Audit Completion

**Auditor:** ______________________
**Date:** _________________________
**Server:** ________________________
**IP Address:** ___________________
**Overall Risk Level:** ☐ Critical ☐ High ☐ Medium ☐ Low

**Critical Findings:** ___
**High-Priority Findings:** ___
**Medium-Priority Findings:** ___
**Low-Priority Findings:** ___

**Recommendations:**
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

**Follow-up Actions:**
- [ ] Create remediation plan
- [ ] Assign ownership for each finding
- [ ] Set remediation deadlines
- [ ] Schedule follow-up audit

**Sign-off:**
Auditor: _________________ Date: _________
Server Owner: _____________ Date: _________
Security Lead: ____________ Date: _________

---

**Next Steps:**
1. Run the automated hardening script: `scripts/harden-ubuntu-server.sh`
2. Set up unauthorized login detection: `scripts/detect-unauthorized-logins.sh`
3. Review services to disable: `docs/SERVICES_TO_DISABLE.md`
4. Schedule quarterly follow-up audit

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Maintained By:** Security Team
