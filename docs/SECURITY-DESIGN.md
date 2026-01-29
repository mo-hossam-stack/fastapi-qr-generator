# Security Design Document

## QR Code Generator Security Architecture

**Version:** 1.0  
**Date:** January 2026  
**Status:** Approved

---

## 1. Overview

This document outlines the security architecture, controls, and best practices for the QR Code Generator system. Security is a critical concern given the system handles user data, processes file uploads, and redirects users to external URLs.

---

## 2. Threat Model

### 2.1 Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| User credentials | High | Account takeover |
| API keys | High | Unauthorized API access |
| User data (PII) | High | Privacy violation, legal |
| QR code content | Medium | Business disruption |
| Analytics data | Medium | Competitive intelligence |
| System infrastructure | Critical | Complete service compromise |

### 2.2 Threat Actors

| Actor | Motivation | Capability |
|-------|------------|------------|
| Script kiddies | Mischief, learning | Low |
| Cybercriminals | Financial gain | Medium-High |
| Competitors | Business intelligence | Medium |
| Malicious users | Abuse service | Low-Medium |
| Nation-state | Espionage | High |

### 2.3 Attack Vectors

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ATTACK SURFACE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  EXTERNAL                           INTERNAL                         │
│  ┌─────────────────────────┐       ┌─────────────────────────┐     │
│  │ • API endpoints         │       │ • Database injection     │     │
│  │ • File uploads          │       │ • Privilege escalation   │     │
│  │ • URL redirects         │       │ • Data exfiltration      │     │
│  │ • Authentication        │       │ • Insider threats        │     │
│  │ • Rate limit bypass     │       │ • Configuration errors   │     │
│  │ • DDoS attacks          │       │ • Dependency vulns       │     │
│  └─────────────────────────┘       └─────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Authentication Security

### 3.1 Password Requirements

| Requirement | Specification |
|-------------|---------------|
| Minimum length | 8 characters |
| Maximum length | 128 characters |
| Complexity | At least 1 uppercase, 1 number, 1 special character |
| Common passwords | Rejected (top 10,000 list) |
| Breached passwords | Checked against HaveIBeenPwned |

### 3.2 Password Storage

```
Algorithm: Argon2id (recommended) or bcrypt
- Argon2id parameters:
  - Memory: 64 MB
  - Iterations: 3
  - Parallelism: 4
  - Salt: 16 bytes (random)
  
- bcrypt parameters:
  - Cost factor: 12
  - Salt: Built-in (22 characters)
```

### 3.3 JWT Security

| Control | Implementation |
|---------|----------------|
| Algorithm | HS256 (HMAC-SHA256) |
| Secret length | 256 bits minimum |
| Token expiry | 15 minutes (access), 7 days (refresh) |
| Issuer validation | Required |
| Audience validation | Required |
| Storage | HttpOnly, Secure, SameSite=Strict cookies |

### 3.4 API Key Security

| Control | Implementation |
|---------|----------------|
| Format | `qrg_{env}_{32_char_random}` |
| Storage | SHA-256 hash only |
| Transmission | HTTPS, Authorization header |
| Rotation | User-initiated, immediate effect |
| Revocation | Immediate, cached for 5 minutes |

### 3.5 Rate Limiting for Auth

| Action | Limit | Lockout |
|--------|-------|---------|
| Login attempts | 5 per 15 minutes | 15 minute lockout |
| Password reset | 3 per hour | 1 hour cooldown |
| Registration | 3 per hour per IP | 1 hour cooldown |
| API key creation | 10 per day | Daily limit |

---

## 4. Input Validation

### 4.1 Validation Principles

1. **Server-side validation is mandatory** - Never trust client-side validation
2. **Whitelist approach** - Define what IS allowed, reject everything else
3. **Validate early** - Check input before any processing
4. **Fail safely** - Reject invalid input, don't try to fix it
5. **Log validation failures** - For security monitoring

### 4.2 URL Validation

```
URL Validation Pipeline:
┌─────────────────────────────────────────────────────────────────┐
│  1. SYNTAX CHECK                                                 │
│     • Valid URL format (RFC 3986)                               │
│     • Maximum length: 2048 characters                           │
│     • Allowed schemes: http, https only                         │
│     • No credentials in URL (user:pass@)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. DOMAIN CHECK                                                 │
│     • Not an IP address (unless explicitly allowed)             │
│     • Not localhost/internal domains                            │
│     • Not on blocklist (malware, phishing)                      │
│     • Valid TLD                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. CONTENT CHECK (optional, for dynamic QR)                    │
│     • Resolve URL (follow redirects, max 5)                     │
│     • Check final destination against blocklist                 │
│     • Verify SSL certificate (for https)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 File Upload Validation

```
File Validation Pipeline:
┌─────────────────────────────────────────────────────────────────┐
│  1. PRE-UPLOAD CHECKS                                            │
│     • Content-Length header < 10MB                               │
│     • Content-Type header matches allowed types                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. MAGIC BYTES VALIDATION                                       │
│     • Read first 16 bytes                                        │
│     • Match against known signatures                             │
│     • Reject if mismatch                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. IMAGE PARSING                                                │
│     • Attempt to open with Pillow                                │
│     • Reject if fails to parse                                   │
│     • Check dimensions (max 4096x4096)                          │
│     • Re-encode to strip malicious metadata                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. MALWARE SCAN (optional)                                      │
│     • Send to virus scanning service                             │
│     • Reject if flagged                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Magic Bytes Reference

| Format | Magic Bytes | Hex |
|--------|-------------|-----|
| PNG | `\x89PNG\r\n\x1a\n` | 89 50 4E 47 0D 0A 1A 0A |
| JPEG | `\xff\xd8\xff` | FF D8 FF |
| GIF | `GIF87a` or `GIF89a` | 47 49 46 38 37/39 61 |
| WebP | `RIFF....WEBP` | 52 49 46 46 .. .. .. .. 57 45 42 50 |
| SVG | `<?xml` or `<svg` | 3C 3F 78 6D 6C or 3C 73 76 67 |

### 4.5 Text Input Sanitization

| Field Type | Sanitization |
|------------|--------------|
| Names | Strip HTML, limit to alphanumeric + basic punctuation |
| Email | Validate format, normalize (lowercase) |
| URLs | URL-encode special characters |
| Free text | Escape HTML entities for display |
| JSON | Parse and validate schema |

---

## 5. Output Security

### 5.1 Response Headers

```http
# Security Headers (all responses)
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Content-Security-Policy: default-src 'self'; img-src 'self' https://cdn.qrgenerator.com; script-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### 5.2 CORS Configuration

```python
CORS_SETTINGS = {
    "allowed_origins": [
        "https://qrgenerator.com",
        "https://app.qrgenerator.com",
    ],
    "allowed_methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
    "allowed_headers": ["Authorization", "Content-Type"],
    "allow_credentials": True,
    "max_age": 86400,  # 24 hours
}
```

### 5.3 Data Masking

| Data Type | Display Format |
|-----------|----------------|
| Email | `j***@example.com` |
| API Key | `qrg_live_a1b2...` (first 12 chars) |
| IP Address | Hashed for storage |
| Phone | `+1-***-***-4567` |

---

## 6. Injection Prevention

### 6.1 SQL Injection

**Controls:**
- Use parameterized queries (SQLAlchemy ORM)
- Never concatenate user input into queries
- Validate and whitelist column names for sorting
- Use prepared statements for raw SQL

**Example (Python/SQLAlchemy):**
```python
# GOOD - Parameterized
result = db.execute(
    text("SELECT * FROM qr_codes WHERE user_id = :user_id"),
    {"user_id": user_id}
)

# BAD - String concatenation
result = db.execute(f"SELECT * FROM qr_codes WHERE user_id = '{user_id}'")
```

### 6.2 Command Injection

**Controls:**
- Never pass user input to shell commands
- Use subprocess with list arguments, not shell=True
- Whitelist allowed commands and arguments

### 6.3 Path Traversal

**Controls:**
- Validate file paths against allowed directories
- Use `os.path.realpath()` and check prefix
- Never use user input directly in file paths

```python
def safe_file_path(base_dir: str, user_input: str) -> str:
    """Safely resolve file path, preventing traversal."""
    # Normalize the path
    requested = os.path.realpath(os.path.join(base_dir, user_input))
    base = os.path.realpath(base_dir)
    
    # Ensure it's within allowed directory
    if not requested.startswith(base + os.sep):
        raise SecurityError("Path traversal detected")
    
    return requested
```

---

## 7. Rate Limiting & Abuse Prevention

### 7.1 Rate Limit Tiers

| Resource | Free | Pro | Business | Enterprise |
|----------|------|-----|----------|------------|
| QR generation | 10/hour | 100/hour | 1000/hour | Unlimited |
| API calls | 100/hour | 1000/hour | 10000/hour | Custom |
| File uploads | 5/hour | 50/hour | 500/hour | Custom |
| Redirects | 1000/min | 10000/min | 100000/min | Unlimited |

### 7.2 Rate Limit Implementation

```
Algorithm: Sliding Window with Redis

Key: ratelimit:{resource}:{identifier}:{window}
Example: ratelimit:api:usr_abc123:hour

Implementation:
1. Get current count for key
2. If count >= limit, return 429
3. Increment counter
4. Set TTL if new key
5. Process request
```

### 7.3 Abuse Detection

| Pattern | Detection | Response |
|---------|-----------|----------|
| Credential stuffing | Failed logins from multiple IPs | CAPTCHA, IP block |
| Scraping | High volume requests to listings | Rate limit, CAPTCHA |
| Spam QR codes | High volume, similar content | Manual review |
| Malicious URLs | Blocklist matches | Immediate block |
| Resource exhaustion | Large file uploads | Size limits |

---

## 8. Data Protection

### 8.1 Encryption

| Data State | Method | Key Management |
|------------|--------|----------------|
| In transit | TLS 1.3 | Managed certificates |
| At rest (DB) | AES-256 (AWS RDS) | AWS KMS |
| At rest (S3) | AES-256 (SSE-S3) | AWS managed |
| Application secrets | Environment variables | AWS Secrets Manager |

### 8.2 PII Handling

| PII Field | Storage | Access | Retention |
|-----------|---------|--------|-----------|
| Email | Encrypted | Auth only | Account lifetime |
| Name | Plain text | User profile | Account lifetime |
| IP Address | SHA-256 hash | Analytics | 2 years |
| User Agent | Truncated | Analytics | 2 years |
| Location | City level only | Analytics | 2 years |

### 8.3 GDPR Compliance

| Right | Implementation |
|-------|----------------|
| Right to access | Export API endpoint |
| Right to deletion | Delete account + 30-day grace |
| Right to portability | JSON export of all data |
| Right to rectification | Profile edit endpoints |
| Consent | Explicit opt-in for marketing |

---

## 9. Infrastructure Security

### 9.1 Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NETWORK ZONES                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INTERNET                                                            │
│  ─────────────────────────────────────────────────────────────────  │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    DMZ (Public Subnet)                         │ │
│  │  • CloudFlare WAF                                              │ │
│  │  • Load Balancer (HTTPS termination)                          │ │
│  │  • Rate limiting                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                APPLICATION (Private Subnet)                    │ │
│  │  • API servers                                                 │ │
│  │  • Worker nodes                                                │ │
│  │  • No direct internet access                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                  DATA (Isolated Subnet)                        │ │
│  │  • PostgreSQL (encrypted)                                      │ │
│  │  • Redis (encrypted)                                           │ │
│  │  • No internet access                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Firewall Rules

| Source | Destination | Port | Protocol | Action |
|--------|-------------|------|----------|--------|
| Internet | Load Balancer | 443 | HTTPS | Allow |
| Load Balancer | API Servers | 8000 | HTTP | Allow |
| API Servers | PostgreSQL | 5432 | TCP | Allow |
| API Servers | Redis | 6379 | TCP | Allow |
| API Servers | S3 | 443 | HTTPS | Allow |
| * | * | * | * | Deny |

### 9.3 Container Security

| Control | Implementation |
|---------|----------------|
| Base images | Official, minimal (Alpine/Distroless) |
| Image scanning | Trivy/Snyk in CI pipeline |
| Non-root user | All containers run as non-root |
| Read-only FS | Where possible |
| Resource limits | CPU, memory limits set |
| Network policies | Pod-to-pod restrictions |

---

## 10. Logging & Monitoring

### 10.1 Security Logging

| Event | Log Level | Data Captured |
|-------|-----------|---------------|
| Login success | INFO | user_id, ip, timestamp |
| Login failure | WARN | email, ip, reason |
| API key created | INFO | user_id, key_prefix |
| API key revoked | INFO | user_id, key_prefix |
| Permission denied | WARN | user_id, resource, action |
| Rate limit exceeded | WARN | identifier, endpoint |
| Validation failure | DEBUG | field, value (sanitized) |
| Suspicious activity | ALERT | full context |

### 10.2 Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Failed logins (user) | >5 in 15 min | Notify user, temporary lock |
| Failed logins (global) | >100 in 5 min | Alert SOC, enable CAPTCHA |
| API errors | >1% rate | Alert engineering |
| Unusual traffic pattern | ML detection | Alert SOC |
| Malicious URL detected | Any | Block, alert |

### 10.3 Audit Trail

All security-relevant actions are logged to immutable audit storage:

```json
{
    "timestamp": "2026-01-28T12:00:00Z",
    "event_type": "auth.login.success",
    "actor": {
        "user_id": "usr_abc123",
        "ip_address": "203.0.113.50",
        "user_agent": "Mozilla/5.0..."
    },
    "resource": {
        "type": "session",
        "id": "sess_xyz789"
    },
    "context": {
        "method": "password",
        "mfa_used": false
    },
    "request_id": "req_abc123"
}
```

---

## 11. Incident Response

### 11.1 Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 Critical | Active breach, data loss | 15 minutes | Credentials leaked, DB breach |
| P2 High | Vulnerability exploited | 1 hour | SQL injection found |
| P3 Medium | Potential security issue | 4 hours | Suspicious activity |
| P4 Low | Minor security concern | 24 hours | Policy violation |

### 11.2 Response Procedures

```
INCIDENT RESPONSE FLOW:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   DETECT    │───▶│   CONTAIN   │───▶│  ERADICATE  │───▶│   RECOVER   │
│             │    │             │    │             │    │             │
│ • Alerts    │    │ • Isolate   │    │ • Root cause│    │ • Restore   │
│ • Logs      │    │ • Block     │    │ • Patch     │    │ • Verify    │
│ • Reports   │    │ • Preserve  │    │ • Remove    │    │ • Monitor   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
                                                         ┌─────────────┐
                                                         │   REVIEW    │
                                                         │             │
                                                         │ • Document  │
                                                         │ • Improve   │
                                                         │ • Train     │
                                                         └─────────────┘
```

---

## 12. Security Checklist

### Pre-Deployment

- [ ] All dependencies scanned for vulnerabilities
- [ ] Secrets removed from code/configs
- [ ] Input validation implemented for all endpoints
- [ ] Authentication tested (positive and negative)
- [ ] Rate limiting configured and tested
- [ ] HTTPS enforced everywhere
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] Logging enabled for security events
- [ ] Backup and recovery tested

### Ongoing

- [ ] Weekly dependency vulnerability scans
- [ ] Monthly penetration testing (automated)
- [ ] Quarterly security review
- [ ] Annual penetration test (manual)
- [ ] Security awareness training (annual)

---

*Document Owner: Security Team*  
*Last Updated: January 2026*
