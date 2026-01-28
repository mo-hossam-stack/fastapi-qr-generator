# ADR-002: Database Selection

## Status

**Accepted**

## Date

January 2026

## Context

We need to select a primary database for the QR Code Generator service. The database must store:

- User accounts and authentication data
- QR code metadata (not the images themselves)
- Dynamic QR code mappings (short URL → destination)
- Analytics data (scan events)

Requirements:
- Strong consistency for user data
- High read performance for URL redirects
- Efficient time-series queries for analytics
- ACID compliance for financial data
- Scalability to millions of QR codes

## Decision

**Selected: PostgreSQL as primary database with Redis for caching**

We will use **PostgreSQL 15+** as the primary relational database, complemented by **Redis** for caching and rate limiting.

## Alternatives Considered

### Option 1: PostgreSQL

| Aspect | Assessment |
|--------|------------|
| Consistency | Strong (ACID) |
| Performance | Excellent with proper indexing |
| Scalability | Good (read replicas, partitioning) |
| JSON Support | Excellent (JSONB) |
| Analytics | Good (window functions, CTEs) |
| Ecosystem | Excellent (mature, well-supported) |
| Cost | Low (open source) |

### Option 2: MySQL/MariaDB

| Aspect | Assessment |
|--------|------------|
| Consistency | Strong (ACID with InnoDB) |
| Performance | Good |
| Scalability | Good |
| JSON Support | Moderate |
| Analytics | Moderate |
| Ecosystem | Excellent |
| Cost | Low (open source) |

### Option 3: MongoDB

| Aspect | Assessment |
|--------|------------|
| Consistency | Eventual (configurable) |
| Performance | Excellent for writes |
| Scalability | Excellent (native sharding) |
| JSON Support | Native (BSON) |
| Analytics | Moderate (aggregation pipeline) |
| Ecosystem | Good |
| Cost | Medium (managed services) |

### Option 4: CockroachDB

| Aspect | Assessment |
|--------|------------|
| Consistency | Strong (serializable) |
| Performance | Good |
| Scalability | Excellent (distributed) |
| JSON Support | Good |
| Analytics | Good |
| Ecosystem | Growing |
| Cost | High (enterprise features) |

## Comparison Matrix

| Criteria | Weight | PostgreSQL | MySQL | MongoDB | CockroachDB |
|----------|--------|------------|-------|---------|-------------|
| ACID Compliance | 20% | 10 | 9 | 6 | 10 |
| Read Performance | 20% | 9 | 8 | 8 | 8 |
| JSON Support | 15% | 10 | 6 | 10 | 8 |
| Analytics Queries | 15% | 10 | 7 | 6 | 9 |
| Ecosystem/Tooling | 15% | 10 | 10 | 8 | 7 |
| Cost | 15% | 10 | 10 | 7 | 5 |
| **Weighted Score** | | **9.7** | **8.35** | **7.35** | **7.95** |

## Database Schema Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Primary Database                         │
├─────────────────────────────────────────────────────────────┤
│  users              │ User accounts, authentication          │
│  api_keys           │ API key management                     │
│  qr_codes           │ QR code metadata                       │
│  qr_redirects       │ Dynamic QR short URL mappings          │
│  scan_events        │ Analytics (partitioned by date)        │
│  subscriptions      │ Billing and plan information           │
│  folders            │ QR code organization                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Redis Cache                              │
├─────────────────────────────────────────────────────────────┤
│  rate_limits        │ API rate limiting counters             │
│  sessions           │ User session data                      │
│  redirect_cache     │ Hot redirect URL cache                 │
│  analytics_buffer   │ Scan event buffer before DB write      │
└─────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive

- **Proven reliability**: PostgreSQL is battle-tested at scale
- **JSONB flexibility**: Store variable QR metadata without schema changes
- **Advanced analytics**: Window functions, CTEs for complex queries
- **Cost effective**: Open source, no licensing fees
- **Excellent tooling**: pgAdmin, DataGrip, extensive monitoring
- **SQLAlchemy support**: Excellent async support with FastAPI

### Negative

- **Single-node limitations**: Requires read replicas for high read loads
- **Partitioning complexity**: Manual setup for analytics tables
- **Operational overhead**: Requires DBA expertise for optimization

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Read scalability | Read replicas for analytics, Redis cache for redirects |
| Analytics volume | Table partitioning by date, archive old data |
| Complexity | Use managed PostgreSQL (RDS, Cloud SQL) |

## Redis Usage

Redis will be used for:

1. **Rate Limiting**: Sliding window counters per API key
2. **Session Cache**: JWT session data for fast validation
3. **Redirect Cache**: Cache hot short URLs (TTL: 5 minutes)
4. **Analytics Buffer**: Buffer scan events before batch insert

```
Cache Strategy:
- Redirect lookups: Cache-aside with 5-minute TTL
- Rate limits: Sliding window with Redis MULTI
- Sessions: Store with user_id key, 24-hour TTL
```

## References

- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [Redis Caching Patterns](https://redis.io/docs/manual/patterns/)
- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)

---

*Decision made by: Engineering Team*  
*Approved by: Architecture Review Board*
