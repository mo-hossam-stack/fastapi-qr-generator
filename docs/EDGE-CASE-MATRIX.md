# Edge Case Matrix

## QR Code Generator Error Handling

**Version:** 1.0  
**Date:** January 2026  
**Status:** Approved

---

## 1. Overview

This document catalogs all edge cases, error conditions, and exceptional scenarios the QR Code Generator system must handle. Each edge case includes detection criteria, handling strategy, and user-facing messages.

---

## 2. URL Input Edge Cases

### 2.1 Invalid URL Format

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| URL-001 | Empty URL | `len(url) == 0` | Reject | 400 | VALIDATION_ERROR |
| URL-002 | Whitespace only | `url.strip() == ""` | Reject | 400 | VALIDATION_ERROR |
| URL-003 | Missing scheme | No `://` in URL | Reject | 400 | INVALID_URL |
| URL-004 | Invalid scheme | Not `http://` or `https://` | Reject | 400 | INVALID_URL |
| URL-005 | Malformed URL | URL parsing fails | Reject | 400 | INVALID_URL |
| URL-006 | URL too long | `len(url) > 2048` | Reject | 400 | URL_TOO_LONG |
| URL-007 | Non-ASCII characters | Contains non-ASCII | Encode to punycode | - | - |
| URL-008 | Credentials in URL | `user:pass@` pattern | Reject | 400 | INVALID_URL |

**User Messages:**

| Error Code | Message |
|------------|---------|
| VALIDATION_ERROR | "URL is required" |
| INVALID_URL | "Please enter a valid URL starting with http:// or https://" |
| URL_TOO_LONG | "URL exceeds maximum length of 2048 characters" |

### 2.2 Dangerous URLs

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| URL-010 | Localhost URL | `localhost`, `127.0.0.1` | Reject | 400 | URL_BLOCKED |
| URL-011 | Private IP | RFC 1918 addresses | Reject | 400 | URL_BLOCKED |
| URL-012 | Known malware domain | Domain blocklist check | Reject | 400 | URL_BLOCKED |
| URL-013 | Known phishing domain | Domain blocklist check | Reject | 400 | URL_BLOCKED |
| URL-014 | URL shortener | bit.ly, tinyurl, etc. | Allow with warning | 200 | - |
| URL-015 | JavaScript URL | `javascript:` scheme | Reject | 400 | INVALID_URL |
| URL-016 | Data URL | `data:` scheme | Reject | 400 | INVALID_URL |
| URL-017 | File URL | `file:` scheme | Reject | 400 | INVALID_URL |

**User Messages:**

| Error Code | Message |
|------------|---------|
| URL_BLOCKED | "This URL cannot be used for security reasons" |

### 2.3 URL Resolution Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| URL-020 | DNS resolution fails | DNS lookup timeout | Allow (static), Warn (dynamic) | 200 | - |
| URL-021 | Domain doesn't exist | NXDOMAIN response | Allow with warning | 200 | - |
| URL-022 | SSL certificate invalid | Certificate validation fails | Allow with warning | 200 | - |
| URL-023 | Redirect loop | >5 redirects | Warn user | 200 | - |
| URL-024 | Final redirect blocked | Ends at blocked domain | Reject | 400 | URL_BLOCKED |

---

## 3. Image Upload Edge Cases

### 3.1 File Validation Errors

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| IMG-001 | No file uploaded | File field empty | Reject | 400 | VALIDATION_ERROR |
| IMG-002 | Empty file | File size = 0 | Reject | 400 | IMAGE_EMPTY |
| IMG-003 | File too large | Size > 10MB | Reject | 413 | IMAGE_TOO_LARGE |
| IMG-004 | Unsupported format | Extension not in whitelist | Reject | 400 | IMAGE_FORMAT_UNSUPPORTED |
| IMG-005 | Extension mismatch | Magic bytes don't match extension | Reject | 400 | IMAGE_INVALID |
| IMG-006 | Corrupted file | Image parsing fails | Reject | 400 | IMAGE_CORRUPTED |
| IMG-007 | Truncated file | Incomplete image data | Reject | 400 | IMAGE_CORRUPTED |

**User Messages:**

| Error Code | Message |
|------------|---------|
| VALIDATION_ERROR | "Please select an image file to upload" |
| IMAGE_EMPTY | "The uploaded file is empty" |
| IMAGE_TOO_LARGE | "Image exceeds maximum size of 10MB" |
| IMAGE_FORMAT_UNSUPPORTED | "Supported formats: PNG, JPG, GIF, WebP, SVG" |
| IMAGE_INVALID | "The file does not appear to be a valid image" |
| IMAGE_CORRUPTED | "The image file appears to be corrupted" |

### 3.2 Image Dimension Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| IMG-010 | Image too small | Width or height < 10px | Reject | 400 | IMAGE_TOO_SMALL |
| IMG-011 | Image too large | Width or height > 4096px | Resize to max | 200 | - |
| IMG-012 | Extreme aspect ratio | Ratio > 10:1 or < 1:10 | Allow with warning | 200 | - |
| IMG-013 | Animated GIF | Multiple frames detected | Use first frame | 200 | - |
| IMG-014 | Animated WebP | Multiple frames detected | Use first frame | 200 | - |

**User Messages:**

| Error Code | Message |
|------------|---------|
| IMAGE_TOO_SMALL | "Image must be at least 10x10 pixels" |

### 3.3 Image Content Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| IMG-020 | CMYK color space | Color mode detection | Convert to RGB | 200 | - |
| IMG-021 | 16-bit color depth | Bit depth detection | Convert to 8-bit | 200 | - |
| IMG-022 | Embedded ICC profile | Profile detected | Strip and convert | 200 | - |
| IMG-023 | Malicious EXIF | EXIF parsing attempt | Strip all metadata | 200 | - |
| IMG-024 | SVG with scripts | `<script>` tags detected | Sanitize or reject | 400 | IMAGE_INVALID |
| IMG-025 | SVG external refs | External URLs in SVG | Remove external refs | 200 | - |
| IMG-026 | Transparent logo | Alpha channel detected | Preserve transparency | 200 | - |
| IMG-027 | Very dark logo | Average luminance low | Warn user | 200 | - |
| IMG-028 | Very light logo | Average luminance high | Warn user | 200 | - |

---

## 4. QR Code Generation Edge Cases

### 4.1 Content Capacity

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| QR-001 | Content too large | Exceeds QR capacity | Reject | 400 | CONTENT_TOO_LARGE |
| QR-002 | Content near limit | >90% capacity | Allow with warning | 200 | - |
| QR-003 | Binary content | Non-text data | Encode as binary | 200 | - |
| QR-004 | Unicode content | Non-ASCII text | Encode as UTF-8 | 200 | - |

**QR Code Capacity Limits (with Error Correction H):**

| Version | Numeric | Alphanumeric | Binary | Kanji |
|---------|---------|--------------|--------|-------|
| 1 | 17 | 10 | 7 | 4 |
| 10 | 395 | 240 | 165 | 101 |
| 20 | 1,249 | 758 | 520 | 320 |
| 40 | 3,057 | 1,852 | 1,273 | 784 |

**User Messages:**

| Error Code | Message |
|------------|---------|
| CONTENT_TOO_LARGE | "The content is too large to fit in a QR code. Please shorten the URL or text." |

### 4.2 Logo Embedding Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| QR-010 | Logo too large (ratio) | Logo size > 30% of QR | Reject | 400 | LOGO_SIZE_INVALID |
| QR-011 | QR unreadable with logo | Scan test fails | Reduce logo size, retry | 200 | - |
| QR-012 | Logo aspect mismatch | Logo not square | Center and fit | 200 | - |
| QR-013 | Transparent logo on dark QR | Transparency + dark fg | Warn user | 200 | - |
| QR-014 | Logo color conflicts | Low contrast | Warn user | 200 | - |

**User Messages:**

| Error Code | Message |
|------------|---------|
| LOGO_SIZE_INVALID | "Logo size must be between 10% and 30% of the QR code size" |

### 4.3 Color Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| QR-020 | Invalid hex color | Regex validation fails | Reject | 400 | INVALID_COLOR |
| QR-021 | Low contrast | Calculate contrast ratio | Warn if < 4.5:1 | 200 | - |
| QR-022 | Same fg/bg color | fg_color == bg_color | Reject | 400 | INVALID_COLOR |
| QR-023 | Light foreground | Fg lighter than bg | Swap and warn | 200 | - |
| QR-024 | Gradient colors | Not supported | Use solid colors | 200 | - |

**User Messages:**

| Error Code | Message |
|------------|---------|
| INVALID_COLOR | "Please enter a valid hex color (e.g., #000000)" |

---

## 5. Dynamic QR Edge Cases

### 5.1 Redirect Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| DYN-001 | Short code not found | DB lookup returns null | Return 404 page | 404 | REDIRECT_NOT_FOUND |
| DYN-002 | QR code disabled | `is_active = false` | Return disabled page | 410 | REDIRECT_DISABLED |
| DYN-003 | QR code expired | `expires_at < now()` | Return expired page | 410 | REDIRECT_EXPIRED |
| DYN-004 | Password required | `password_hash` set | Show password form | 401 | - |
| DYN-005 | Wrong password | Password doesn't match | Return error | 401 | INVALID_PASSWORD |
| DYN-006 | Destination unreachable | URL returns error | Redirect anyway | 302 | - |

**User Pages:**

| Scenario | Page Content |
|----------|--------------|
| Not found | "This QR code does not exist" |
| Disabled | "This QR code has been deactivated by its owner" |
| Expired | "This QR code has expired" |

### 5.2 URL Update Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| DYN-010 | Update static QR | `is_dynamic = false` | Reject | 400 | QR_NOT_DYNAMIC |
| DYN-011 | Update to blocked URL | New URL on blocklist | Reject | 400 | URL_BLOCKED |
| DYN-012 | Cache invalidation fails | Redis error | Log, continue | 200 | - |

**User Messages:**

| Error Code | Message |
|------------|---------|
| QR_NOT_DYNAMIC | "Static QR codes cannot be edited. Create a new QR code or upgrade to dynamic." |

---

## 6. Authentication Edge Cases

### 6.1 Login Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| AUTH-001 | Email not found | DB lookup returns null | Generic error | 401 | INVALID_CREDENTIALS |
| AUTH-002 | Wrong password | bcrypt verify fails | Generic error | 401 | INVALID_CREDENTIALS |
| AUTH-003 | Account locked | `locked_until > now()` | Reject | 403 | ACCOUNT_LOCKED |
| AUTH-004 | Email not verified | `email_verified = false` | Allow login, prompt | 200 | - |
| AUTH-005 | Account deleted | `deleted_at` is set | Generic error | 401 | INVALID_CREDENTIALS |
| AUTH-006 | Concurrent sessions | Multiple active sessions | Allow (configurable) | 200 | - |

**User Messages:**

| Error Code | Message |
|------------|---------|
| INVALID_CREDENTIALS | "Invalid email or password" |
| ACCOUNT_LOCKED | "Account temporarily locked. Please try again in 15 minutes." |

### 6.2 Token Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| AUTH-010 | Token missing | No Authorization header | Reject | 401 | UNAUTHORIZED |
| AUTH-011 | Token malformed | Parse error | Reject | 401 | TOKEN_INVALID |
| AUTH-012 | Token expired | `exp < now()` | Reject | 401 | TOKEN_EXPIRED |
| AUTH-013 | Token signature invalid | Verify fails | Reject | 401 | TOKEN_INVALID |
| AUTH-014 | Token revoked | In blacklist | Reject | 401 | TOKEN_INVALID |
| AUTH-015 | Refresh token reuse | Same refresh used twice | Revoke all, alert | 401 | TOKEN_INVALID |

### 6.3 API Key Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| AUTH-020 | API key missing | No key in header | Reject | 401 | UNAUTHORIZED |
| AUTH-021 | API key invalid format | Prefix doesn't match | Reject | 401 | API_KEY_INVALID |
| AUTH-022 | API key not found | Hash not in DB | Reject | 401 | API_KEY_INVALID |
| AUTH-023 | API key revoked | `revoked_at` is set | Reject | 401 | API_KEY_REVOKED |
| AUTH-024 | API key expired | `expires_at < now()` | Reject | 401 | API_KEY_EXPIRED |
| AUTH-025 | IP not in allowlist | IP check fails | Reject | 403 | IP_NOT_ALLOWED |

---

## 7. Rate Limiting Edge Cases

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| RATE-001 | Rate limit exceeded | Counter > limit | Reject | 429 | RATE_LIMITED |
| RATE-002 | Redis unavailable | Connection error | Allow (fail open) | 200 | - |
| RATE-003 | Distributed timing | Clock skew | Use Redis time | - | - |
| RATE-004 | Burst limit exceeded | Short window check | Reject | 429 | RATE_LIMITED |

**Response Headers:**
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704153600
Retry-After: 3600
```

**User Messages:**

| Error Code | Message |
|------------|---------|
| RATE_LIMITED | "Rate limit exceeded. Please try again in {time}" |

---

## 8. System Edge Cases

### 8.1 Storage Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| SYS-001 | S3 upload fails | AWS SDK error | Retry 3x, then fail | 500 | STORAGE_ERROR |
| SYS-002 | S3 read fails | AWS SDK error | Retry 3x, return cached | 500 | STORAGE_ERROR |
| SYS-003 | Disk full (temp) | Write fails | Alert, reject | 500 | SYSTEM_ERROR |
| SYS-004 | File cleanup fails | Delete error | Log, continue | - | - |

### 8.2 Database Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| SYS-010 | Connection pool exhausted | Timeout | Queue or reject | 503 | SERVICE_UNAVAILABLE |
| SYS-011 | Query timeout | Execution timeout | Cancel, retry | 500 | SYSTEM_ERROR |
| SYS-012 | Deadlock detected | DB error code | Retry 3x | 500 | SYSTEM_ERROR |
| SYS-013 | Unique constraint violation | DB error code | Return conflict | 409 | RESOURCE_EXISTS |

### 8.3 External Service Issues

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| SYS-020 | GeoIP service down | Request timeout | Skip geo data | 200 | - |
| SYS-021 | Email service down | Send failure | Queue for retry | 200 | - |
| SYS-022 | CDN invalidation fails | API error | Log, continue | 200 | - |

---

## 9. Concurrency Edge Cases

| ID | Edge Case | Detection | Handling | HTTP Code | Error Code |
|----|-----------|-----------|----------|-----------|------------|
| CONC-001 | Duplicate short code | Unique constraint | Regenerate | - | - |
| CONC-002 | Simultaneous updates | Optimistic locking | Last write wins or conflict | 409 | CONFLICT |
| CONC-003 | Race in rate limiting | Redis atomicity | Use MULTI/EXEC | - | - |
| CONC-004 | Double submission | Idempotency key | Return cached response | 200 | - |

---

## 10. Edge Case Testing Checklist

### Input Validation
- [ ] Empty inputs for all required fields
- [ ] Maximum length inputs
- [ ] Special characters in all text fields
- [ ] Unicode in names, URLs, content
- [ ] Null bytes in strings
- [ ] Array inputs where single value expected
- [ ] Object inputs where string expected

### File Uploads
- [ ] Empty file upload
- [ ] Oversized file
- [ ] Wrong file type (extension)
- [ ] Wrong file type (content)
- [ ] Corrupted image
- [ ] Image with malicious metadata
- [ ] Animated image

### Authentication
- [ ] Missing auth header
- [ ] Malformed token
- [ ] Expired token
- [ ] Revoked token
- [ ] Invalid API key
- [ ] Wrong password (multiple attempts)

### API Behavior
- [ ] Rate limit boundary
- [ ] Concurrent requests
- [ ] Request during maintenance
- [ ] Request with invalid JSON
- [ ] Request with extra fields

---

*Document Owner: Engineering Team*  
*Last Updated: January 2026*
