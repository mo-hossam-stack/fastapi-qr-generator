# ADR-005: Storage Strategy

## Status

**Not Accepted yet **

## Date

January 2026

## Context

We need to define a storage strategy for the QR Code Generator service. Storage needs include:

1. **Generated QR Code Images**: PNG, SVG, JPG, EPS files
2. **Uploaded Logos**: User-provided images for embedding
3. **Temporary Files**: Processing intermediates
4. **Static Assets**: UI assets, default logos, templates

Requirements:
- High availability and durability
- Fast delivery (low latency)
- Cost-effective for large volumes
- Support for multiple file formats
- CDN integration for global delivery
- Automatic cleanup of temporary files

## Decision

**Selected: S3-compatible object storage with CDN**

We will use **S3-compatible object storage** (AWS S3, MinIO, or equivalent) for persistent file storage, combined with a **CDN** (CloudFlare or CloudFront) for delivery.

## Alternatives Considered

### Option 1: Local File System

| Aspect | Assessment |
|--------|------------|
| Performance | Good (local I/O) |
| Durability | Poor (single point of failure) |
| Scalability | Poor (disk limits) |
| Cost | Low (included in server) |
| CDN Integration | Manual setup |
| Complexity | Low |

### Option 2: S3-Compatible Object Storage

| Aspect | Assessment |
|--------|------------|
| Performance | Excellent (distributed) |
| Durability | Excellent (99.999999999%) |
| Scalability | Excellent (unlimited) |
| Cost | Usage-based |
| CDN Integration | Native (CloudFront) |
| Complexity | Low |

### Option 3: Database BLOB Storage

| Aspect | Assessment |
|--------|------------|
| Performance | Moderate |
| Durability | Good (with backups) |
| Scalability | Poor (database limits) |
| Cost | High (DB storage pricing) |
| CDN Integration | Poor |
| Complexity | Moderate |

### Option 4: Hybrid (S3 + Local Cache)

| Aspect | Assessment |
|--------|------------|
| Performance | Excellent |
| Durability | Excellent |
| Scalability | Excellent |
| Cost | Moderate |
| CDN Integration | Native |
| Complexity | Moderate |

## Comparison Matrix

| Criteria | Weight | Local FS | S3 | DB BLOB | Hybrid |
|----------|--------|----------|-----|---------|--------|
| Durability | 25% | 3 | 10 | 7 | 10 |
| Scalability | 25% | 3 | 10 | 4 | 10 |
| Performance | 20% | 8 | 8 | 5 | 9 |
| Cost Efficiency | 15% | 8 | 7 | 4 | 6 |
| Complexity | 15% | 9 | 8 | 6 | 6 |
| **Weighted Score** | | **5.55** | **8.95** | **5.3** | **8.7** |

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage Architecture                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐  │
│   │   Client    │────────▶│     CDN     │────────▶│   Origin    │  │
│   │  (Browser)  │◀────────│ (CloudFlare)│◀────────│    (S3)     │  │
│   └─────────────┘         └─────────────┘         └─────────────┘  │
│                                  │                                   │
│                                  │ Cache Miss                        │
│                                  ▼                                   │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐  │
│   │   API       │────────▶│   S3 API    │────────▶│   Bucket    │  │
│   │  Server     │◀────────│             │◀────────│   Storage   │  │
│   └─────────────┘         └─────────────┘         └─────────────┘  │
│         │                                                            │
│         │ Temp files                                                 │
│         ▼                                                            │
│   ┌─────────────┐                                                   │
│   │   Local     │  (Processing only, auto-cleanup)                  │
│   │   /tmp      │                                                   │
│   └─────────────┘                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Bucket Structure

```
qr-generator-storage/
├── qr-codes/
│   ├── {user_id}/
│   │   ├── {qr_id}/
│   │   │   ├── original.png
│   │   │   ├── original.svg
│   │   │   ├── thumb_200.png
│   │   │   └── metadata.json
│   │   └── ...
│   └── ...
├── logos/
│   ├── {user_id}/
│   │   ├── {logo_id}.png
│   │   └── ...
│   └── default/
│       ├── placeholder.png
│       └── ...
├── exports/
│   ├── {user_id}/
│   │   └── {export_id}.zip  (bulk exports, TTL: 24h)
│   └── ...
└── temp/
    └── {session_id}/        (TTL: 1 hour)
        └── processing_*.tmp
```

## Storage Classes

| Content Type | Storage Class | Lifecycle |
|--------------|---------------|-----------|
| QR Codes (active) | S3 Standard | Permanent (until deleted) |
| QR Codes (archived) | S3 Infrequent Access | After 90 days inactive |
| Logos | S3 Standard | Permanent (until deleted) |
| Bulk Exports | S3 Standard | Delete after 24 hours |
| Temp Files | Local /tmp | Delete after 1 hour |

## CDN Configuration

### Cache Rules

| Path Pattern | Cache TTL | Behavior |
|--------------|-----------|----------|
| `/qr-codes/*` | 24 hours | Cache, respect origin headers |
| `/logos/*` | 7 days | Cache, long-lived |
| `/static/*` | 30 days | Cache, immutable |
| `/api/*` | No cache | Pass through |

### Security Headers

```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: public, max-age=86400
```

## URL Structure

### Public URLs (via CDN)

```
# QR Code images
https://cdn.qrgenerator.com/qr/{qr_id}.png
https://cdn.qrgenerator.com/qr/{qr_id}.svg

# Dynamic QR redirect (not cached)
https://qr.link/{short_code}

# Thumbnails
https://cdn.qrgenerator.com/qr/{qr_id}/thumb.png
```

### Signed URLs (for private content)

```
# Private QR (with signature)
https://cdn.qrgenerator.com/qr/{qr_id}.png?sig={signature}&exp={expiry}

# Export downloads
https://cdn.qrgenerator.com/exports/{export_id}.zip?sig={signature}&exp={expiry}
```

## Consequences

### Positive

- **Durability**: 11 9s durability with S3
- **Scalability**: Unlimited storage capacity
- **Performance**: CDN delivers globally with low latency
- **Cost Efficiency**: Pay only for what you use
- **Simplicity**: Managed service, no infrastructure to maintain

### Negative

- **Vendor Lock-in**: S3 API dependency (mitigated by S3-compatible options)
- **Egress Costs**: Data transfer can be expensive at scale
- **Latency**: Initial upload/fetch adds network latency

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Vendor lock-in | Use S3-compatible API (MinIO for self-hosted) |
| Egress costs | CDN caching reduces origin fetches |
| Latency | Generate and serve from nearest region |

## Cost Estimation

| Component | Monthly Estimate (10K users) |
|-----------|------------------------------|
| S3 Storage (100GB) | ~$2.30 |
| S3 Requests (1M) | ~$0.50 |
| CloudFlare CDN | Free tier / $20 Pro |
| Data Transfer | Free (CloudFlare) |
| **Total** | **~$3-25/month** |

## References

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [CloudFlare CDN](https://developers.cloudflare.com/cache/)
- [MinIO Documentation](https://docs.min.io/)

---
