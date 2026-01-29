# Data Design Document

## QR Code Generator Data Architecture

**Version:** 1.0  
**Date:** January 2026  
**Status:** Draft

---

## 1. Overview

This document defines the data architecture for the QR Code Generator system, including database schemas, storage strategies, caching patterns, and data lifecycle management.

---

## 2. Database Schema

### 2.1 Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    plan VARCHAR(20) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'business', 'enterprise')),
    settings JSONB DEFAULT '{}',
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_plan ON users(plan);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;
```

**Settings JSONB Structure:**
```json
{
    "notifications": {
        "email_scan_alerts": true,
        "email_weekly_report": true
    },
    "defaults": {
        "qr_size": 500,
        "error_correction": "M",
        "foreground_color": "#000000",
        "background_color": "#FFFFFF"
    },
    "timezone": "America/New_York"
}
```

---

### 2.2 API Keys Table

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,  -- e.g., "qrg_live_a1b2"
    key_hash VARCHAR(64) NOT NULL,     -- SHA-256 hash of full key
    environment VARCHAR(10) DEFAULT 'live' CHECK (environment IN ('live', 'test')),
    permissions JSONB DEFAULT '["qr:read", "qr:write"]',
    ip_allowlist TEXT[],
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

---

### 2.3 QR Codes Table

```sql
CREATE TABLE qr_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- QR Content
    type VARCHAR(20) NOT NULL CHECK (type IN ('url', 'text', 'vcard', 'wifi', 'email', 'sms', 'phone', 'geo', 'image')),
    content TEXT NOT NULL,  -- Encoded content (URL, vCard string, etc.)
    content_hash VARCHAR(64),  -- For deduplication
    
    -- Dynamic QR
    is_dynamic BOOLEAN DEFAULT FALSE,
    short_code VARCHAR(10) UNIQUE,  -- For dynamic QR redirects
    
    -- Display Options
    options JSONB NOT NULL DEFAULT '{}',
    
    -- Storage
    storage_paths JSONB NOT NULL DEFAULT '{}',  -- {"png": "path", "svg": "path", ...}
    
    -- Metadata
    name VARCHAR(100),
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    tags TEXT[] DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete
);

CREATE INDEX idx_qr_codes_user ON qr_codes(user_id);
CREATE INDEX idx_qr_codes_short_code ON qr_codes(short_code) WHERE short_code IS NOT NULL;
CREATE INDEX idx_qr_codes_folder ON qr_codes(folder_id);
CREATE INDEX idx_qr_codes_type ON qr_codes(type);
CREATE INDEX idx_qr_codes_tags ON qr_codes USING GIN(tags);
CREATE INDEX idx_qr_codes_created ON qr_codes(created_at DESC);
CREATE INDEX idx_qr_codes_active ON qr_codes(is_active) WHERE is_active = TRUE;
```

**Options JSONB Structure:**
```json
{
    "size": 500,
    "error_correction": "H",
    "foreground_color": "#000000",
    "background_color": "#FFFFFF",
    "style": "square",
    "logo": {
        "storage_path": "logos/usr_abc/logo_123.png",
        "size_ratio": 0.25
    },
    "frame": {
        "style": "banner",
        "text": "Scan Me!",
        "font_size": 14,
        "color": "#333333"
    }
}
```

**Storage Paths JSONB Structure:**
```json
{
    "png": "qr-codes/usr_abc/qr_123/original.png",
    "svg": "qr-codes/usr_abc/qr_123/original.svg",
    "jpg": "qr-codes/usr_abc/qr_123/original.jpg",
    "eps": "qr-codes/usr_abc/qr_123/original.eps",
    "thumb": "qr-codes/usr_abc/qr_123/thumb_200.png"
}
```

---

### 2.4 QR Redirects Table

```sql
CREATE TABLE qr_redirects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qr_code_id UUID UNIQUE NOT NULL REFERENCES qr_codes(id) ON DELETE CASCADE,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    destination_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255),  -- Optional password protection
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_redirects_short_code ON qr_redirects(short_code);
CREATE INDEX idx_redirects_qr_code ON qr_redirects(qr_code_id);
CREATE INDEX idx_redirects_active ON qr_redirects(is_active) WHERE is_active = TRUE;
```

---

### 2.5 Scan Events Table (Partitioned)

```sql
CREATE TABLE scan_events (
    id UUID DEFAULT gen_random_uuid(),
    qr_code_id UUID NOT NULL,
    short_code VARCHAR(10),
    
    -- Scan Context
    scanned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_hash VARCHAR(64),  -- Hashed for privacy
    user_agent TEXT,
    
    -- Parsed User Agent
    device_type VARCHAR(20),  -- mobile, tablet, desktop
    os VARCHAR(50),
    os_version VARCHAR(20),
    browser VARCHAR(50),
    browser_version VARCHAR(20),
    
    -- Geo Data
    country_code CHAR(2),
    country_name VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Referrer
    referrer TEXT,
    referrer_domain VARCHAR(255),
    
    PRIMARY KEY (id, scanned_at)
) PARTITION BY RANGE (scanned_at);

-- Create monthly partitions
CREATE TABLE scan_events_2026_01 PARTITION OF scan_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE scan_events_2026_02 PARTITION OF scan_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Indexes on partitioned table
CREATE INDEX idx_scans_qr_code ON scan_events(qr_code_id, scanned_at);
CREATE INDEX idx_scans_short_code ON scan_events(short_code, scanned_at);
CREATE INDEX idx_scans_country ON scan_events(country_code, scanned_at);
```

---

### 2.6 Folders Table

```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),  -- Hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_folder_name UNIQUE (user_id, parent_id, name)
);

CREATE INDEX idx_folders_user ON folders(user_id);
CREATE INDEX idx_folders_parent ON folders(parent_id);
```

---

### 2.7 Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'canceled', 'expired')),
    
    -- Billing Provider
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    
    -- Period
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    canceled_at TIMESTAMP
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
```

---

### 2.8 Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,  -- e.g., 'qr.create', 'user.login'
    resource_type VARCHAR(50),    -- e.g., 'qr_code', 'user'
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    changes JSONB,  -- Before/after values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at);
```

---

## 3. Redis Data Structures

### 3.1 Session Cache

```
Key: session:{user_id}:{session_id}
Type: Hash
TTL: 24 hours (or 30 days for "remember me")

Fields:
- user_id
- email
- plan
- permissions (JSON array)
- created_at
- last_activity
```

### 3.2 Rate Limiting

```
Key: ratelimit:{identifier}:{window}
Type: String (counter)
TTL: Window duration

Examples:
- ratelimit:api_key:qrg_live_abc:hour -> 45
- ratelimit:user:usr_123:minute -> 12
- ratelimit:ip:192.168.1.1:minute -> 5
```

### 3.3 Redirect Cache

```
Key: redirect:{short_code}
Type: Hash
TTL: 5 minutes (refresh on access)

Fields:
- url: "https://example.com/page"
- active: "true"
- expires: "1704153600" (Unix timestamp, 0 = no expiry)
- password: "false"
```

### 3.4 Analytics Buffer

```
Key: scan_buffer
Type: List (FIFO queue)
TTL: None (processed by workers)

Values: JSON strings
{
    "qr_code_id": "uuid",
    "short_code": "abc123",
    "scanned_at": "2026-01-28T12:00:00Z",
    "ip_hash": "sha256...",
    "user_agent": "Mozilla/5.0...",
    "geo": {...}
}
```

### 3.5 QR Code Metadata Cache

```
Key: qr:{qr_id}:meta
Type: Hash
TTL: 1 hour

Fields:
- user_id
- type
- is_dynamic
- short_code
- is_active
- created_at
```

---

## 4. Object Storage Structure

### 4.1 Bucket Layout

```
qr-generator-storage/
│
├── qr-codes/
│   └── {user_id}/
│       └── {qr_id}/
│           ├── original.png      (Full resolution)
│           ├── original.svg
│           ├── original.jpg
│           ├── original.eps
│           ├── thumb_200.png     (200px thumbnail)
│           └── metadata.json     (Generation metadata)
│
├── logos/
│   └── {user_id}/
│       ├── {logo_id}.png
│       ├── {logo_id}_processed.png  (Optimized version)
│       └── ...
│
├── exports/
│   └── {user_id}/
│       └── {export_id}/
│           ├── export.zip
│           └── manifest.json
│
└── temp/
    └── {session_id}/
        └── processing_*.tmp
```

### 4.2 File Naming Convention

```
QR Codes:
  qr-codes/{user_id}/{qr_id}/original.{format}
  qr-codes/{user_id}/{qr_id}/thumb_{size}.png

Logos:
  logos/{user_id}/{logo_id}.{ext}
  logos/{user_id}/{logo_id}_processed.png

Exports:
  exports/{user_id}/{export_id}/export.zip
```

### 4.3 Metadata File

```json
{
    "qr_id": "qr_abc123",
    "generated_at": "2026-01-28T12:00:00Z",
    "options": {
        "size": 500,
        "error_correction": "H",
        "foreground_color": "#000000",
        "background_color": "#FFFFFF"
    },
    "files": {
        "png": {"size": 15234, "hash": "sha256:abc..."},
        "svg": {"size": 8456, "hash": "sha256:def..."}
    },
    "version": "1.0"
}
```

---

## 5. Data Lifecycle

### 5.1 Retention Policies

| Data Type | Active Retention | Archive | Deletion |
|-----------|-----------------|---------|----------|
| User accounts | Indefinite | N/A | On request + 30 days |
| QR codes | Indefinite | N/A | On deletion + 30 days |
| QR images | Indefinite | After 1 year inactive | With QR code |
| Scan events | 2 years | Years 3-5 (aggregated) | After 5 years |
| Audit logs | 1 year | Years 2-3 | After 3 years |
| Temp files | 1 hour | N/A | Immediate |
| Export files | 24 hours | N/A | Immediate |

### 5.2 Scan Event Aggregation

After 2 years, individual scan events are aggregated:

```sql
-- Aggregated scans table
CREATE TABLE scan_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qr_code_id UUID NOT NULL,
    period_type VARCHAR(10) NOT NULL,  -- 'day', 'week', 'month'
    period_start DATE NOT NULL,
    
    -- Counts
    total_scans INTEGER DEFAULT 0,
    unique_scans INTEGER DEFAULT 0,
    
    -- Device breakdown
    mobile_scans INTEGER DEFAULT 0,
    tablet_scans INTEGER DEFAULT 0,
    desktop_scans INTEGER DEFAULT 0,
    
    -- Top countries (JSON)
    top_countries JSONB DEFAULT '[]',
    
    -- Top OS (JSON)
    top_os JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(qr_code_id, period_type, period_start)
);
```

### 5.3 Cleanup Jobs

```
Daily Jobs:
- Delete expired temp files (> 1 hour old)
- Delete expired export files (> 24 hours old)
- Process soft-deleted records (> 30 days)

Weekly Jobs:
- Archive old scan partitions
- Update analytics aggregates
- Clean orphaned storage files

Monthly Jobs:
- Create new scan event partitions
- Review and optimize indexes
- Generate usage reports
```

---

## 6. Backup Strategy

### 6.1 PostgreSQL Backups

| Type | Frequency | Retention | Storage |
|------|-----------|-----------|---------|
| Full backup | Daily | 30 days | S3 Glacier |
| Incremental | Hourly | 7 days | S3 Standard |
| WAL archiving | Continuous | 7 days | S3 Standard |

### 6.2 Redis Backups

| Type | Frequency | Retention |
|------|-----------|-----------|
| RDB snapshot | Every 15 min | 24 hours |
| AOF | Continuous | 24 hours |

### 6.3 Object Storage

- Versioning enabled on all buckets
- Cross-region replication for production
- 30-day version retention

---

## 7. Data Migration Patterns

### 7.1 Adding New Columns

```sql
-- Always use defaults for new columns
ALTER TABLE qr_codes 
ADD COLUMN scan_count INTEGER DEFAULT 0;

-- Backfill in batches
UPDATE qr_codes 
SET scan_count = (SELECT COUNT(*) FROM scan_events WHERE qr_code_id = qr_codes.id)
WHERE id IN (SELECT id FROM qr_codes LIMIT 1000);
```

### 7.2 Changing Column Types

```sql
-- 1. Add new column
ALTER TABLE qr_codes ADD COLUMN new_type VARCHAR(30);

-- 2. Backfill
UPDATE qr_codes SET new_type = type;

-- 3. Switch (during maintenance window)
ALTER TABLE qr_codes DROP COLUMN type;
ALTER TABLE qr_codes RENAME COLUMN new_type TO type;
```

---

## 8. Performance Considerations

### 8.1 Indexes Strategy

- Primary key indexes on all tables
- Foreign key indexes for joins
- Partial indexes for common filters (e.g., `WHERE is_active = TRUE`)
- GIN indexes for JSONB and array columns
- Covering indexes for frequent queries

### 8.2 Query Optimization

- Use `EXPLAIN ANALYZE` for query planning
- Limit result sets with pagination
- Use materialized views for complex aggregations
- Partition large tables (scan_events)

### 8.3 Connection Pooling

```
PgBouncer Configuration:
- pool_mode: transaction
- default_pool_size: 20
- max_client_conn: 1000
- min_pool_size: 5
```

---

*Document Owner: Engineering Team*  
*Last Updated: January 2026*
