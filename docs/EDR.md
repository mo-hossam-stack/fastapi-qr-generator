# Engineering Design Records (EDR)

## QR Code Generator System Architecture

**Version:** 1.0  
**Date:** January 2026  
**Status:** Approved

---

## 1. System Overview

The QR Code Generator is a backend-first, API-driven system designed to generate, manage, and track QR codes. The system supports both static and dynamic QR codes with full customization options.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL CLIENTS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │  Web App     │    │  Mobile App  │    │  3rd Party   │                 │
│   │  (Frontend)  │    │  (Future)    │    │  Integrations│                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
└──────────┼───────────────────┼───────────────────┼──────────────────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CDN / LOAD BALANCER                             │
│                           (CloudFlare / AWS ALB)                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Redirect Svc   │    │   Static CDN    │
│   /api/v1/*     │    │  qr.link/*      │    │   /assets/*     │
└────────┬────────┘    └────────┬────────┘    └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │  QR Generation  │    │  User & Auth    │    │   Analytics     │        │
│   │    Service      │    │    Service      │    │    Service      │        │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│            │                      │                      │                  │
│            └──────────────────────┼──────────────────────┘                  │
│                                   │                                          │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    PostgreSQL   │      │      Redis      │      │   Object Store  │
│   (Primary DB)  │      │  (Cache/Queue)  │      │   (S3/MinIO)    │
└─────────────────┘      └─────────────────┘      └─────────────────┘

```

---

## 2. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QR GENERATOR SYSTEM COMPONENTS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        API GATEWAY (FastAPI)                           │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  • Request routing                                                     │ │
│  │  • Authentication middleware                                           │ │
│  │  • Rate limiting middleware                                            │ │
│  │  • Request validation (Pydantic)                                       │ │
│  │  • Error handling                                                      │ │
│  │  • OpenAPI documentation                                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│         ┌────────────────────────────┼────────────────────────────┐         │
│         │                            │                            │         │
│         ▼                            ▼                            ▼         │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │   QR SERVICE    │      │   AUTH SERVICE  │      │ ANALYTICS SVC   │    │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤    │
│  │ • URL to QR     │      │ • JWT handling  │      │ • Scan tracking │    │
│  │ • Image embed   │      │ • API key mgmt  │      │ • Aggregation   │    │
│  │ • Customization │      │ • User CRUD     │      │ • Export        │    │
│  │ • Format export │      │ • OAuth         │      │ • Real-time     │    │
│  │ • Dynamic QR    │      │ • Rate limits   │      │ • GeoIP lookup  │    │
│  └────────┬────────┘      └────────┬────────┘      └────────┬────────┘    │
│           │                        │                        │              │
│  ┌────────┴────────┐      ┌────────┴────────┐      ┌────────┴────────┐    │
│  │ IMAGE PROCESSOR │      │  REDIRECT SVC   │      │  NOTIFICATION   │    │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤    │
│  │ • Pillow        │      │ • URL mapping   │      │ • Email         │    │
│  │ • Logo resize   │      │ • Redis cache   │      │ • Webhooks      │    │
│  │ • Color apply   │      │ • 302 redirect  │      │ • Alerts        │    │
│  │ • Format convert│      │ • Log scans     │      │                 │    │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagrams

### 3.1 URL to QR Code Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    URL TO QR CODE GENERATION FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client                API                QR Service         Storage         │
│    │                    │                     │                │            │
│    │  POST /api/v1/qr   │                     │                │            │
│    │  {url, options}    │                     │                │            │
│    │───────────────────▶│                     │                │            │
│    │                    │                     │                │            │
│    │                    │  Validate request   │                │            │
│    │                    │  Check auth/limits  │                │            │
│    │                    │─────────────────────│                │            │
│    │                    │                     │                │            │
│    │                    │  Generate QR        │                │            │
│    │                    │────────────────────▶│                │            │
│    │                    │                     │                │            │
│    │                    │                     │  Create QR     │            │
│    │                    │                     │  matrix        │            │
│    │                    │                     │                │            │
│    │                    │                     │  Apply colors  │            │
│    │                    │                     │  & styles      │            │
│    │                    │                     │                │            │
│    │                    │                     │  Embed logo    │            │
│    │                    │                     │  (if provided) │            │
│    │                    │                     │                │            │
│    │                    │                     │  Save to S3    │            │
│    │                    │                     │───────────────▶│            │
│    │                    │                     │                │            │
│    │                    │                     │  S3 URL        │            │
│    │                    │                     │◀───────────────│            │
│    │                    │                     │                │            │
│    │                    │  Save metadata      │                │            │
│    │                    │  to PostgreSQL      │                │            │
│    │                    │◀────────────────────│                │            │
│    │                    │                     │                │            │
│    │  200 OK            │                     │                │            │
│    │  {qr_id, urls}     │                     │                │            │
│    │◀───────────────────│                     │                │            │
│    │                    │                     │                │            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Dynamic QR Redirect Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DYNAMIC QR REDIRECT FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scanner         Redirect Svc         Redis           DB          Analytics │
│    │                  │                 │              │              │     │
│    │  GET /abc123     │                 │              │              │     │
│    │─────────────────▶│                 │              │              │     │
│    │                  │                 │              │              │     │
│    │                  │  GET redirect:  │              │              │     │
│    │                  │  abc123         │              │              │     │
│    │                  │────────────────▶│              │              │     │
│    │                  │                 │              │              │     │
│    │                  │           ┌─────┴─────┐       │              │     │
│    │                  │           │Cache Hit? │       │              │     │
│    │                  │           └─────┬─────┘       │              │     │
│    │                  │                 │              │              │     │
│    │                  │  ┌──────────────┴──────────────┐              │     │
│    │                  │  │                             │              │     │
│    │                  │  ▼ YES                         ▼ NO           │     │
│    │                  │  Return URL            Query Database         │     │
│    │                  │◀────────────────       ───────────────▶│     │     │
│    │                  │                                        │     │     │
│    │                  │                        Return URL      │     │     │
│    │                  │                        + Warm cache    │     │     │
│    │                  │◀───────────────────────────────────────│     │     │
│    │                  │                 │              │              │     │
│    │                  │  Log scan event (async)        │              │     │
│    │                  │─────────────────────────────────────────────▶│     │
│    │                  │                 │              │              │     │
│    │  302 Redirect    │                 │              │              │     │
│    │  Location: URL   │                 │              │              │     │
│    │◀─────────────────│                 │              │              │     │
│    │                  │                 │              │              │     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Image-to-QR Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IMAGE EMBEDDING PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐                                                           │
│   │   INPUT     │                                                           │
│   │  - URL/Data │                                                           │
│   │  - Logo     │                                                           │
│   │  - Options  │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    VALIDATION STAGE                              │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  1. Validate URL format (RFC 3986)                               │      │
│   │  2. Check URL against blocklist                                  │      │
│   │  3. Validate logo file (magic bytes, size, dimensions)          │      │
│   │  4. Check user quotas and rate limits                           │      │
│   └──────────────────────────┬──────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    LOGO PREPROCESSING                            │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  1. Strip EXIF metadata (security + privacy)                     │      │
│   │  2. Convert to RGBA color space                                  │      │
│   │  3. Resize to max dimensions (1024x1024)                        │      │
│   │  4. Calculate optimal logo size (20-30% of QR)                  │      │
│   │  5. Resize logo to calculated size                               │      │
│   │  6. Add white padding/border                                     │      │
│   └──────────────────────────┬──────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    QR GENERATION                                 │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  1. Encode URL/data into QR matrix                               │      │
│   │  2. Apply error correction level (H for logo embedding)         │      │
│   │  3. Render QR code at target resolution                          │      │
│   │  4. Apply foreground/background colors                           │      │
│   │  5. Apply style (square, dots, rounded)                         │      │
│   └──────────────────────────┬──────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    LOGO COMPOSITION                              │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  1. Calculate center position                                    │      │
│   │  2. Create mask for logo area                                    │      │
│   │  3. Composite logo onto QR code                                  │      │
│   │  4. Apply transparency if needed                                 │      │
│   └──────────────────────────┬──────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    VERIFICATION                                  │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  1. Test decode generated QR code                                │      │
│   │  2. Verify decoded data matches input                           │      │
│   │  3. If scan fails: reduce logo size and retry                   │      │
│   │  4. Generate scan confidence score                               │      │
│   └──────────────────────────┬──────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    OUTPUT GENERATION                             │      │
│   ├─────────────────────────────────────────────────────────────────┤      │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │      │
│   │  │  PNG    │  │  SVG    │  │  JPG    │  │  EPS    │            │      │
│   │  │ (Pillow)│  │ (Segno) │  │ (Pillow)│  │ (Cairo) │            │      │
│   │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │      │
│   │       │            │            │            │                   │      │
│   │       └────────────┴────────────┴────────────┘                   │      │
│   │                         │                                        │      │
│   │                         ▼                                        │      │
│   │                  Upload to S3                                    │      │
│   │                  Return CDN URLs                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Sequence Diagrams

### 4.1 User Registration and QR Creation

```
┌────────┐     ┌─────────┐     ┌──────────┐     ┌────────┐     ┌─────────┐
│ Client │     │   API   │     │   Auth   │     │   QR   │     │   DB    │
└───┬────┘     └────┬────┘     └────┬─────┘     └───┬────┘     └────┬────┘
    │               │               │               │               │
    │  POST /register               │               │               │
    │──────────────▶│               │               │               │
    │               │  createUser() │               │               │
    │               │──────────────▶│               │               │
    │               │               │  INSERT user  │               │
    │               │               │──────────────────────────────▶│
    │               │               │               │    user_id    │
    │               │               │◀──────────────────────────────│
    │               │  JWT token    │               │               │
    │               │◀──────────────│               │               │
    │  201 Created  │               │               │               │
    │  {token}      │               │               │               │
    │◀──────────────│               │               │               │
    │               │               │               │               │
    │  POST /qr     │               │               │               │
    │  Auth: Bearer │               │               │               │
    │──────────────▶│               │               │               │
    │               │  verifyToken()│               │               │
    │               │──────────────▶│               │               │
    │               │  user_id      │               │               │
    │               │◀──────────────│               │               │
    │               │               │               │               │
    │               │  generateQR() │               │               │
    │               │──────────────────────────────▶│               │
    │               │               │               │  INSERT qr    │
    │               │               │               │──────────────▶│
    │               │               │               │    qr_id      │
    │               │               │               │◀──────────────│
    │               │  {qr_id, url} │               │               │
    │               │◀──────────────────────────────│               │
    │  201 Created  │               │               │               │
    │  {qr_data}    │               │               │               │
    │◀──────────────│               │               │               │
    │               │               │               │               │
```

### 4.2 Analytics Collection

```
┌─────────┐   ┌──────────┐   ┌───────┐   ┌─────────┐   ┌────────┐   ┌──────┐
│ Scanner │   │ Redirect │   │ Redis │   │ Worker  │   │   DB   │   │ GeoIP│
└────┬────┘   └────┬─────┘   └───┬───┘   └────┬────┘   └───┬────┘   └──┬───┘
     │             │             │            │            │           │
     │ GET /abc123 │             │            │            │           │
     │────────────▶│             │            │            │           │
     │             │ GET url     │            │            │           │
     │             │────────────▶│            │            │           │
     │             │ destination │            │            │           │
     │             │◀────────────│            │            │           │
     │             │             │            │            │           │
     │             │ LPUSH scan_events        │            │           │
     │             │─────────────────────────▶│            │           │
     │             │             │            │            │           │
     │ 302 Redirect│             │            │            │           │
     │◀────────────│             │            │            │           │
     │             │             │            │            │           │
     │             │             │ (async)    │            │           │
     │             │             │ BRPOP      │            │           │
     │             │             │───────────▶│            │           │
     │             │             │ event      │            │           │
     │             │             │◀───────────│            │           │
     │             │             │            │            │           │
     │             │             │            │ lookup(ip) │           │
     │             │             │            │───────────────────────▶│
     │             │             │            │ geo_data   │           │
     │             │             │            │◀───────────────────────│
     │             │             │            │            │           │
     │             │             │            │ INSERT     │           │
     │             │             │            │ scan_event │           │
     │             │             │            │───────────▶│           │
     │             │             │            │ OK         │           │
     │             │             │            │◀───────────│           │
     │             │             │            │            │           │
```

---

## 5. Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATABASE ENTITY RELATIONSHIPS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │      USERS       │         │    API_KEYS      │                         │
│  ├──────────────────┤         ├──────────────────┤                         │
│  │ id (PK)          │────────▶│ id (PK)          │                         │
│  │ email            │    1:N  │ user_id (FK)     │                         │
│  │ password_hash    │         │ key_prefix       │                         │
│  │ name             │         │ key_hash         │                         │
│  │ plan             │         │ name             │                         │
│  │ created_at       │         │ last_used_at     │                         │
│  │ updated_at       │         │ created_at       │                         │
│  └────────┬─────────┘         └──────────────────┘                         │
│           │                                                                  │
│           │ 1:N                                                              │
│           ▼                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │    QR_CODES      │         │   QR_REDIRECTS   │                         │
│  ├──────────────────┤         ├──────────────────┤                         │
│  │ id (PK)          │────────▶│ id (PK)          │                         │
│  │ user_id (FK)     │    1:1  │ qr_code_id (FK)  │                         │
│  │ type             │         │ short_code       │                         │
│  │ content          │         │ destination_url  │                         │
│  │ is_dynamic       │         │ is_active        │                         │
│  │ settings (JSONB) │         │ expires_at       │                         │
│  │ folder_id (FK)   │         │ created_at       │                         │
│  │ created_at       │         │ updated_at       │                         │
│  │ updated_at       │         └──────────────────┘                         │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           │ 1:N                                                              │
│           ▼                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │   SCAN_EVENTS    │         │     FOLDERS      │                         │
│  ├──────────────────┤         ├──────────────────┤                         │
│  │ id (PK)          │         │ id (PK)          │                         │
│  │ qr_code_id (FK)  │         │ user_id (FK)     │                         │
│  │ scanned_at       │         │ name             │                         │
│  │ ip_hash          │         │ parent_id (FK)   │                         │
│  │ user_agent       │         │ created_at       │                         │
│  │ device_type      │         └──────────────────┘                         │
│  │ os               │                                                       │
│  │ browser          │         ┌──────────────────┐                         │
│  │ country          │         │  SUBSCRIPTIONS   │                         │
│  │ city             │         ├──────────────────┤                         │
│  │ referrer         │         │ id (PK)          │                         │
│  └──────────────────┘         │ user_id (FK)     │                         │
│  (Partitioned by month)       │ plan             │                         │
│                               │ status           │                         │
│                               │ starts_at        │                         │
│                               │ ends_at          │                         │
│                               │ stripe_id        │                         │
│                               └──────────────────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Technology Stack Details

### Backend Services

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| API Framework | FastAPI | 0.100+ | REST API |
| ASGI Server | Uvicorn | 0.24+ | Production server |
| ORM | SQLAlchemy | 2.0+ | Database access |
| Validation | Pydantic | 2.0+ | Request/response models |
| Auth | python-jose | 3.3+ | JWT handling |
| Task Queue | Celery | 5.3+ | Async processing |
| QR Generation | qrcode | 7.4+ | QR matrix generation |
| QR SVG | segno | 1.5+ | SVG output |
| Image Processing | Pillow | 10.0+ | Image manipulation |

### Data Stores

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Primary DB | PostgreSQL | 15+ | Relational data |
| Cache | Redis | 7.0+ | Caching, queues |
| Object Storage | S3/MinIO | - | File storage |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container | Docker | Application packaging |
| Orchestration | Kubernetes | Container orchestration |
| CDN | CloudFlare | Global delivery |
| Load Balancer | AWS ALB / nginx | Traffic distribution |
| Monitoring | Prometheus + Grafana | Metrics and alerting |
| Logging | ELK Stack | Centralized logging |

---

## 7. API Endpoints Overview

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | User registration | None |
| POST | `/api/v1/auth/login` | User login | None |
| POST | `/api/v1/auth/refresh` | Refresh token | JWT |
| GET | `/api/v1/users/me` | Get current user | JWT/API Key |
| POST | `/api/v1/qr` | Create QR code | JWT/API Key |
| GET | `/api/v1/qr` | List QR codes | JWT/API Key |
| GET | `/api/v1/qr/{id}` | Get QR code | JWT/API Key |
| PATCH | `/api/v1/qr/{id}` | Update QR code | JWT/API Key |
| DELETE | `/api/v1/qr/{id}` | Delete QR code | JWT/API Key |
| GET | `/api/v1/qr/{id}/analytics` | Get analytics | JWT/API Key |
| POST | `/api/v1/qr/{id}/download` | Download QR | JWT/API Key |
| GET | `/{short_code}` | Redirect (dynamic QR) | None |

---

## 8. Performance Specifications

### Response Time Targets

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Simple QR generation | 100ms | 200ms | 500ms |
| QR with logo | 200ms | 400ms | 800ms |
| Dynamic redirect | 10ms | 30ms | 100ms |
| Analytics query | 50ms | 200ms | 500ms |
| Bulk export | 1s | 5s | 10s |

### Throughput Targets

| Metric | Target |
|--------|--------|
| QR generations/sec | 100+ |
| Redirects/sec | 10,000+ |
| Concurrent users | 10,000+ |

---

*Document Owner: Engineering Team*  
*Last Updated: January 2026*
