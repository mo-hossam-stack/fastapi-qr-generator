# ADR-006: Dynamic QR Code Implementation

## Status

**Accepted**

## Date

January 2026

## Context

Dynamic QR codes are a core feature that allows users to change the destination URL after the QR code has been printed/distributed. We need to decide how to implement the redirection mechanism.

Requirements:
- URL can be changed without regenerating the QR code
- Fast redirect response time (<100ms)
- Track scan analytics
- Support millions of redirects
- Handle high traffic spikes

## Decision

**Selected: Short URL service with database-backed redirects and Redis caching**

We will implement a **dedicated short URL service** that handles dynamic QR redirects, using PostgreSQL for persistence and Redis for hot URL caching.

## Alternatives Considered

### Option 1: Direct Database Lookup

| Aspect | Assessment |
|--------|------------|
| Latency | Moderate (10-50ms) |
| Scalability | Limited by DB connections |
| Reliability | Good |
| Complexity | Low |

### Option 2: Redis-Only Storage

| Aspect | Assessment |
|--------|------------|
| Latency | Excellent (<5ms) |
| Scalability | Excellent |
| Reliability | Moderate (persistence concerns) |
| Complexity | Low |

### Option 3: Database + Redis Cache

| Aspect | Assessment |
|--------|------------|
| Latency | Excellent (<10ms typical) |
| Scalability | Excellent |
| Reliability | Excellent |
| Complexity | Moderate |

### Option 4: External Short URL Service

| Aspect | Assessment |
|--------|------------|
| Latency | Variable |
| Scalability | Depends on provider |
| Reliability | Depends on provider |
| Complexity | Low (but less control) |

## Comparison Matrix

| Criteria | Weight | DB Only | Redis Only | DB + Cache | External |
|----------|--------|---------|------------|------------|----------|
| Latency | 25% | 6 | 10 | 9 | 7 |
| Reliability | 25% | 9 | 6 | 10 | 7 |
| Scalability | 20% | 6 | 9 | 9 | 8 |
| Control | 15% | 10 | 10 | 10 | 4 |
| Complexity | 15% | 9 | 8 | 7 | 9 |
| **Weighted Score** | | **7.65** | **8.35** | **9.05** | **7.0** |

## Short Code Generation

### Format

```
Short Code Format: [a-zA-Z0-9]{6-8}

Examples:
- aB3xY7
- K9mNp2Qr
- xY7kL3

Character Set: 
- Lowercase: a-z (26)
- Uppercase: A-Z (26)  
- Numbers: 0-9 (10)
- Total: 62 characters

Capacity:
- 6 chars: 62^6 = 56.8 billion combinations
- 7 chars: 62^7 = 3.5 trillion combinations
- 8 chars: 62^8 = 218 trillion combinations
```

### Generation Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│              Short Code Generation Algorithm                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Generate random 6-character code                         │
│  2. Check for collision in database                          │
│  3. If collision:                                            │
│     a. Try 3 more random codes                               │
│     b. If still collision, increase length to 7             │
│     c. Repeat until unique                                   │
│  4. Store mapping: short_code → destination_url             │
│  5. Warm cache with new mapping                              │
│                                                              │
│  Collision Rate: ~0.0000001% at 1M codes                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Redirect Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Redirect Flow                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│   │ Scanner │───▶│  Edge   │───▶│  Redis  │───▶│ Return  │        │
│   │ Device  │    │ Server  │    │  Cache  │    │ Redirect│        │
│   └─────────┘    └─────────┘    └────┬────┘    └─────────┘        │
│                                      │                              │
│                                 Cache Miss                          │
│                                      │                              │
│                                      ▼                              │
│                                 ┌─────────┐    ┌─────────┐        │
│                                 │ Database│───▶│ Warm    │        │
│                                 │ Lookup  │    │ Cache   │        │
│                                 └─────────┘    └─────────┘        │
│                                                                      │
│   Response: HTTP 302 Found                                          │
│   Location: {destination_url}                                       │
│                                                                      │
│   Async: Log scan event to analytics queue                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Model

### Redirect Table

```sql
CREATE TABLE qr_redirects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    qr_code_id UUID REFERENCES qr_codes(id) ON DELETE CASCADE,
    destination_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    password_hash VARCHAR(255),  -- Optional password protection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_redirects_short_code ON qr_redirects(short_code);
CREATE INDEX idx_redirects_qr_code ON qr_redirects(qr_code_id);
```

### Redis Cache Structure

```
Key: redirect:{short_code}
Value: {
    "url": "https://example.com/destination",
    "active": true,
    "expires": 1704153600,
    "password": false
}
TTL: 5 minutes (refresh on access)
```

## Analytics Collection

### Scan Event Data

```json
{
    "event_id": "uuid",
    "short_code": "aB3xY7",
    "qr_code_id": "uuid",
    "timestamp": "2026-01-28T12:00:00Z",
    "ip_address": "hashed",
    "user_agent": "Mozilla/5.0...",
    "device_type": "mobile",
    "os": "iOS",
    "browser": "Safari",
    "country": "US",
    "city": "New York",
    "referrer": null
}
```

### Analytics Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   Analytics Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Scan ──▶ Redis Queue ──▶ Worker ──▶ PostgreSQL            │
│   Event    (buffer)        (batch)    (partitioned)         │
│                                                              │
│   - Buffer: 100 events or 10 seconds                        │
│   - Batch insert for efficiency                              │
│   - Partitioned by month for query performance              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## URL Validation

Before storing destination URLs, validate:

```
Validation Rules:
1. Valid URL format (RFC 3986)
2. Allowed schemes: http, https
3. Not in blocklist (known malware domains)
4. Length limit: 2048 characters
5. No credentials in URL
6. Resolve and check for redirects to blocked domains
```

## Consequences

### Positive

- **Fast redirects**: <10ms with Redis cache
- **Flexible**: URL can be changed anytime
- **Analytics**: Full tracking of scan events
- **Reliable**: Database backup with cache for speed
- **Scalable**: Redis handles traffic spikes

### Negative

- **Dependency on server**: QR code useless if service down
- **Cache invalidation**: Need to handle URL updates
- **Complexity**: Two-tier storage system

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Server dependency | Multi-region deployment, high availability |
| Cache invalidation | Invalidate on URL update, short TTL |
| Complexity | Well-defined cache-aside pattern |

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Redirect latency (P50) | <20ms | APM monitoring |
| Redirect latency (P99) | <100ms | APM monitoring |
| Cache hit rate | >95% | Redis metrics |
| Availability | 99.99% | Uptime monitoring |

## References

- [URL Shortener System Design](https://www.educative.io/blog/url-shortening-system-design)
- [Redis Caching Patterns](https://redis.io/docs/manual/patterns/)
- [High Scalability URL Shorteners](http://highscalability.com/)

---