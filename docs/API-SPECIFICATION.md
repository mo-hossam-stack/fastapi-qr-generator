# API Specification

## QR Code Generator REST API

**Version:** 1.0  
**OpenAPI:** Available at `/docs` and `/openapi.json`

---

## 1. Overview

### Authentication

All authenticated endpoints accept two forms of authentication:

1. **JWT Token** (for web dashboard users)
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **API Key** (for programmatic access)
   ```
   Authorization: Bearer qrg_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

### Rate Limiting

Rate limits are applied per API key or user:
# the following table outlines limits by plan still not accepted:
| Plan | Requests/Hour | Burst Limit |
|------|---------------|-------------|
| Free | 100 | 10/minute |
| Pro | 1,000 | 100/minute |
| Business | 10,000 | 1,000/minute |
| Enterprise | Unlimited | Custom |

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704153600
```

### Response Format

All responses follow a consistent JSON structure:

**Success Response:**
```json
{
    "success": true,
    "data": { ... },
    "meta": {
        "request_id": "req_abc123",
        "timestamp": "2026-01-29T12:00:00Z"
    }
}
```

**Error Response:**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid URL format",
        "details": [
            {
                "field": "url",
                "message": "URL must start with http:// or https://"
            }
        ]
    },
    "meta": {
        "request_id": "req_abc123",
        "timestamp": "2026-01-28T12:00:00Z"
    }
}
```

---

## 2. Authentication Endpoints

### POST /auth/register

Register a new user account.

**Request:**
```json
{
    "email": "user@example.com",
    "password": "SecureP@ssw0rd!",
    "name": "John Doe"
}
```

**Validation Rules:**
| Field | Rules |
|-------|-------|
| email | Required, valid email format, unique |
| password | Required, min 8 chars, 1 uppercase, 1 number, 1 special |
| name | Required, 2-100 characters |

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "usr_abc123",
            "email": "user@example.com",
            "name": "John Doe",
            "plan": "free",
            "created_at": "2026-01-28T12:00:00Z"
        },
        "tokens": {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "expires_in": 900
        }
    }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| EMAIL_EXISTS | 409 | Email already registered |
| VALIDATION_ERROR | 400 | Invalid input data |

---

### POST /auth/login

Authenticate and receive tokens.

**Request:**
```json
{
    "email": "user@example.com",
    "password": "SecureP@ssw0rd!"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "usr_abc123",
            "email": "user@example.com",
            "name": "John Doe",
            "plan": "pro"
        },
        "tokens": {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "expires_in": 900
        }
    }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_CREDENTIALS | 401 | Wrong email or password |
| ACCOUNT_LOCKED | 403 | Too many failed attempts |

---

### POST /auth/refresh

Refresh an expired access token.

**Request:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "expires_in": 900
    }
}
```

---

## 3. QR Code Generation Endpoints

### POST /qr/generate/url

Generate a QR code from a URL.

**Request:**
```json
{
    "url": "https://example.com/my-page",
    "type": "dynamic",
    "options": {
        "size": 500,
        "error_correction": "H",
        "foreground_color": ".....",
        "background_color": ".....",
        "style": "square",
        "logo": {
            "url": "https://example.com/logo.png",
            "size": 0.25
        },
        "frame": {
            "style": "banner",
            "text": "Scan Me!"
        }
    },
    "metadata": {
        "name": "My Campaign QR",
        "folder_id": "fld_abc123",
        "tags": ["marketing", "campaign-2026"]
    }
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | string | Yes | Target URL (max 2048 chars) |
| type | enum | No | `static` or `dynamic` (default: `static`) |
| options.size | integer | No | Size in pixels (100-2000, default: 500) |
| options.error_correction | enum | No | `L`, `M`, `Q`, `H` (default: `M`) |
| options.foreground_color | string | No | Hex color (default: `#000000`) |
| options.background_color | string | No | Hex color (default: `#FFFFFF`) |
| options.style | enum | No | `square`, `dots`, `rounded` (default: `square`) |
| options.logo.url | string | No | Logo image URL |
| options.logo.size | float | No | Logo size ratio 0.1-0.3 (default: 0.2) |
| options.frame.style | enum | No | `none`, `banner`, `box` |
| options.frame.text | string | No | Frame text (max 50 chars) |
| metadata.name | string | No | QR code name (max 100 chars) |
| metadata.folder_id | string | No | Folder to save in |
| metadata.tags | array | No | Tags for organization |

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "qr_code": {
            "id": "qr_abc123",
            "type": "dynamic",
            "short_code": "aB3xY7",
            "short_url": "https://qr.link/aB3xY7",
            "destination_url": "https://example.com/my-page",
            "images": {
                "png": "https://cdn.qrgenerator.com/qr/qr_abc123.png",
                "svg": "https://cdn.qrgenerator.com/qr/qr_abc123.svg",
                "jpg": "https://cdn.qrgenerator.com/qr/qr_abc123.jpg"
            },
            "options": {
                "size": 500,
                "error_correction": "H",
                "foreground_color": "#000000",
                "background_color": "#FFFFFF",
                "style": "square"
            },
            "metadata": {
                "name": "My Campaign QR",
                "folder_id": "fld_abc123",
                "tags": ["marketing", "campaign-2026"]
            },
            "created_at": "2026-01-28T12:00:00Z"
        }
    }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_URL | 400 | URL format invalid |
| URL_BLOCKED | 400 | URL is on blocklist |
| INVALID_COLOR | 400 | Invalid hex color format |
| LOGO_TOO_LARGE | 400 | Logo exceeds 10MB |
| QUOTA_EXCEEDED | 429 | QR code limit reached |

---

### POST /qr/generate/image

Generate a QR code with embedded image content (converts image to data URL or hosted URL).

**Request (multipart/form-data):**
```
POST /qr/generate/image
Content-Type: multipart/form-data

file: [binary image data]
options: {
    "size": 500,
    "error_correction": "H",
    "foreground_color": "#000000",
    "background_color": "#FFFFFF"
}
metadata: {
    "name": "Image QR"
}
```

**Alternatively (JSON with URL):**
```json
{
    "image_url": "https://example.com/image.png",
    "options": {
        "size": 500,
        "error_correction": "H"
    }
}
```

**Validation Rules:**
| Field | Rules |
|-------|-------|
| file/image_url | Required, one of: PNG, JPG, GIF, WebP |
| file size | Max 10MB |
| image dimensions | Max 4096x4096 pixels |

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "qr_code": {
            "id": "qr_def456",
            "type": "static",
            "content_type": "image",
            "hosted_image_url": "https://cdn.qrgenerator.com/hosted/img_xyz.png",
            "images": {
                "png": "https://cdn.qrgenerator.com/qr/qr_def456.png",
                "svg": "https://cdn.qrgenerator.com/qr/qr_def456.svg"
            },
            "created_at": "2026-01-28T12:00:00Z"
        }
    }
}
```

---

### POST /qr/generate/vcard

Generate a vCard QR code.

**Request:**
```json
{
    "vcard": {
        "first_name": "John",
        "last_name": "Doe",
        "organization": "Acme Inc.",
        "title": "Software Engineer",
        "email": "john.doe@acme.com",
        "phone": "+1-555-123-4567",
        "mobile": "+1-555-987-6543",
        "website": "https://johndoe.com",
        "address": {
            "street": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
            "country": "USA"
        }
    },
    "options": {
        "size": 500,
        "foreground_color": "#1a365d"
    }
}
```

**Response (201 Created):** Same structure as URL generation.

---

### POST /qr/generate/wifi

Generate a WiFi network QR code.

**Request:**
```json
{
    "wifi": {
        "ssid": "MyNetwork",
        "password": "SecurePassword123",
        "security": "WPA",
        "hidden": false
    },
    "options": {
        "size": 500
    }
}
```

**Validation Rules:**
| Field | Rules |
|-------|-------|
| ssid | Required, max 32 characters |
| password | Required for WPA/WPA2, max 63 characters |
| security | `WPA`, `WEP`, `nopass` |
| hidden | Boolean, default false |

---

## 4. QR Code Management Endpoints

### GET /qr

List all QR codes for the authenticated user.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| type | enum | Filter by `static` or `dynamic` |
| folder_id | string | Filter by folder |
| search | string | Search by name or URL |
| sort | string | Sort field: `created_at`, `name`, `scans` |
| order | enum | `asc` or `desc` (default: `desc`) |

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "qr_codes": [
            {
                "id": "qr_abc123",
                "type": "dynamic",
                "name": "My Campaign QR",
                "short_url": "https://qr.link/aB3xY7",
                "destination_url": "https://example.com",
                "thumbnail": "https://cdn.qrgenerator.com/qr/qr_abc123_thumb.png",
                "total_scans": 1250,
                "created_at": "2026-01-28T12:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 45,
            "total_pages": 3
        }
    }
}
```

---

### GET /qr/{id}

Get a specific QR code by ID.

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "qr_code": {
            "id": "qr_abc123",
            "type": "dynamic",
            "short_code": "aB3xY7",
            "short_url": "https://qr.link/aB3xY7",
            "destination_url": "https://example.com/my-page",
            "images": {
                "png": "https://cdn.qrgenerator.com/qr/qr_abc123.png",
                "svg": "https://cdn.qrgenerator.com/qr/qr_abc123.svg",
                "jpg": "https://cdn.qrgenerator.com/qr/qr_abc123.jpg"
            },
            "options": {
                "size": 500,
                "error_correction": "H",
                "foreground_color": "#000000",
                "background_color": "#FFFFFF",
                "style": "square"
            },
            "metadata": {
                "name": "My Campaign QR",
                "folder_id": "fld_abc123",
                "tags": ["marketing"]
            },
            "analytics_summary": {
                "total_scans": 1250,
                "unique_scans": 980,
                "last_scan_at": "2026-01-28T11:30:00Z"
            },
            "created_at": "2026-01-01T12:00:00Z",
            "updated_at": "2026-01-15T09:00:00Z"
        }
    }
}
```

---

### PATCH /qr/{id}

Update a QR code (dynamic QR codes only for URL changes).

**Request:**
```json
{
    "destination_url": "https://example.com/new-page",
    "metadata": {
        "name": "Updated Campaign QR",
        "tags": ["marketing", "updated"]
    },
    "is_active": true
}
```

**Updatable Fields:**
| Field | Applies To | Description |
|-------|-----------|-------------|
| destination_url | Dynamic only | New destination URL |
| metadata.name | All | QR code name |
| metadata.folder_id | All | Move to folder |
| metadata.tags | All | Update tags |
| is_active | Dynamic only | Enable/disable redirect |
| expires_at | Dynamic only | Set expiration date |

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "qr_code": {
            "id": "qr_abc123",
            "destination_url": "https://example.com/new-page",
            "updated_at": "2026-01-28T12:00:00Z"
        }
    }
}
```

---

### DELETE /qr/{id}

Delete a QR code.

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "message": "QR code deleted successfully",
        "id": "qr_abc123"
    }
}
```

---

### POST /qr/{id}/download

Download QR code in specified format.

**Request:**
```json
{
    "format": "png",
    "size": 1000,
    "include_quiet_zone": true
}
```

**Supported Formats:**
| Format | Content-Type | Use Case |
|--------|--------------|----------|
| png | image/png | Web, print |
| svg | image/svg+xml | Scalable, print |
| jpg | image/jpeg | Photos, web |
| eps | application/postscript | Professional print |

**Response (200 OK):**
Returns binary file with appropriate Content-Type header.

---

## 5. Analytics Endpoints

### GET /qr/{id}/analytics

Get analytics for a specific QR code.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | date | Start of period (ISO 8601) |
| end_date | date | End of period (ISO 8601) |
| granularity | enum | `hour`, `day`, `week`, `month` |

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "summary": {
            "total_scans": 1250,
            "unique_scans": 980,
            "first_scan_at": "2026-01-01T08:30:00Z",
            "last_scan_at": "2026-01-28T11:30:00Z"
        },
        "time_series": [
            {
                "date": "2026-01-01",
                "scans": 45,
                "unique_scans": 38
            },
            {
                "date": "2026-01-02",
                "scans": 52,
                "unique_scans": 44
            }
        ],
        "by_country": [
            {"country": "US", "scans": 650, "percentage": 52.0},
            {"country": "UK", "scans": 180, "percentage": 14.4},
            {"country": "DE", "scans": 120, "percentage": 9.6}
        ],
        "by_device": [
            {"device": "mobile", "scans": 1050, "percentage": 84.0},
            {"device": "tablet", "scans": 125, "percentage": 10.0},
            {"device": "desktop", "scans": 75, "percentage": 6.0}
        ],
        "by_os": [
            {"os": "iOS", "scans": 580, "percentage": 46.4},
            {"os": "Android", "scans": 520, "percentage": 41.6},
            {"os": "Other", "scans": 150, "percentage": 12.0}
        ]
    }
}
```

---

### POST /qr/{id}/analytics/export

Export analytics data.

**Request:**
```json
{
    "format": "csv",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "include": ["time_series", "by_country", "by_device"]
}
```

**Response (202 Accepted):**
```json
{
    "success": true,
    "data": {
        "export_id": "exp_abc123",
        "status": "processing",
        "download_url": null,
        "estimated_completion": "2026-01-28T12:05:00Z"
    }
}
```

---

## 6. QR Code Scanning Endpoint (Future)

### POST /scan

Decode a QR code from an image.

**Request (multipart/form-data):**
```
POST /scan
Content-Type: multipart/form-data

file: [binary image data]
```

**Alternatively (JSON with URL):**
```json
{
    "image_url": "https://example.com/qr-image.png"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "decoded": true,
        "content": "https://example.com/my-page",
        "content_type": "url",
        "qr_version": 3,
        "error_correction": "M",
        "is_safe": true,
        "safety_check": {
            "malware": false,
            "phishing": false,
            "checked_at": "2026-01-28T12:00:00Z"
        }
    }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| QR_NOT_FOUND | 400 | No QR code detected in image |
| DECODE_FAILED | 400 | QR code found but couldn't decode |
| IMAGE_INVALID | 400 | Invalid or corrupt image |

---

## 7. Error Codes Reference

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 202 | Accepted - Request accepted for processing |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Application Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Input validation failed |
| INVALID_URL | URL format is invalid |
| URL_BLOCKED | URL is on security blocklist |
| INVALID_COLOR | Invalid hex color format |
| INVALID_IMAGE | Image is corrupt or invalid format |
| IMAGE_TOO_LARGE | Image exceeds size limit |
| LOGO_TOO_LARGE | Logo exceeds size limit |
| QR_NOT_FOUND | QR code not found |
| QUOTA_EXCEEDED | Plan quota exceeded |
| RATE_LIMITED | Too many requests |
| EMAIL_EXISTS | Email already registered |
| INVALID_CREDENTIALS | Wrong email or password |
| TOKEN_EXPIRED | JWT token has expired |
| TOKEN_INVALID | JWT token is invalid |
| API_KEY_INVALID | API key is invalid or revoked |
| PERMISSION_DENIED | User lacks required permission |

---

## 8. Webhooks (Future)

### Webhook Events

| Event | Trigger |
|-------|---------|
| qr.scanned | QR code was scanned |
| qr.milestone | Scan milestone reached (100, 1000, etc.) |
| qr.expired | Dynamic QR code expired |
| export.complete | Analytics export ready |

### Webhook Payload

```json
{
    "event": "qr.scanned",
    "timestamp": "2026-01-28T12:00:00Z",
    "data": {
        "qr_code_id": "qr_abc123",
        "scan": {
            "country": "US",
            "device": "mobile",
            "os": "iOS"
        }
    },
    "signature": "sha256=..."
}
```

---

*Last Updated: January 2026*
