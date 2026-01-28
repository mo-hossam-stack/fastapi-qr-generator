# ADR-001: API Framework Selection

## Status

**Accepted**

## Date

January 2026

## Context

We need to select a backend API framework for the QR Code Generator service. The framework must support:

- RESTful API design
- High-performance request handling
- Async processing for image operations
- Easy integration with QR/image libraries
- Strong ecosystem and community support
- Good developer experience

The service is expected to handle 100+ QR code generations per second at peak load.

## Decision

**Selected: Python with FastAPI**

We will use **FastAPI** as the primary API framework for the QR Code Generator backend.

## Alternatives Considered

### Option 1: Node.js with Express

| Aspect | Assessment |
|--------|------------|
| Performance | Good (V8 engine, async I/O) |
| Ecosystem | Excellent (npm, vast libraries) |
| QR Libraries | Good (qrcode, qr-image) |
| Image Processing | Moderate (Sharp, Jimp) |
| Type Safety | Requires TypeScript |
| API Documentation | Manual (Swagger setup required) |
| Learning Curve | Low |

**Pros:**
- Large developer pool
- Excellent async handling
- Vast middleware ecosystem

**Cons:**
- Image processing less mature than Python
- No built-in API documentation
- Type safety requires additional setup

### Option 2: Python with FastAPI

| Aspect | Assessment |
|--------|------------|
| Performance | Excellent (async, Starlette) |
| Ecosystem | Excellent (PyPI, scientific libraries) |
| QR Libraries | Excellent (qrcode, segno, python-qrcode) |
| Image Processing | Excellent (Pillow, OpenCV) |
| Type Safety | Built-in (Pydantic) |
| API Documentation | Automatic (OpenAPI/Swagger) |
| Learning Curve | Low-Medium |

**Pros:**
- Superior image processing ecosystem (Pillow, OpenCV)
- Automatic API documentation (OpenAPI)
- Built-in data validation (Pydantic)
- Type hints and validation
- Excellent QR code libraries
- Async support with high performance

**Cons:**
- GIL limitations (mitigated by async)
- Slightly smaller web developer pool

### Option 3: Go with Gin/Echo

| Aspect | Assessment |
|--------|------------|
| Performance | Excellent (compiled, concurrent) |
| Ecosystem | Good (growing) |
| QR Libraries | Moderate (go-qrcode) |
| Image Processing | Moderate (image package) |
| Type Safety | Excellent (static typing) |
| API Documentation | Manual |
| Learning Curve | Medium-High |

**Pros:**
- Best raw performance
- Excellent concurrency
- Single binary deployment

**Cons:**
- Smaller ecosystem for image processing
- Less flexible for rapid iteration
- More verbose code

### Option 4: Rust with Actix-web

| Aspect | Assessment |
|--------|------------|
| Performance | Exceptional |
| Ecosystem | Moderate (growing) |
| QR Libraries | Moderate (qrcode-rust) |
| Image Processing | Moderate (image crate) |
| Type Safety | Excellent |
| Learning Curve | High |

**Pros:**
- Best performance
- Memory safety

**Cons:**
- Steep learning curve
- Smaller ecosystem
- Slower development velocity

## Comparison Matrix

| Criteria | Weight | Express | FastAPI | Go/Gin | Rust/Actix |
|----------|--------|---------|---------|--------|------------|
| Performance | 20% | 7 | 9 | 10 | 10 |
| Image Processing | 25% | 6 | 10 | 6 | 6 |
| QR Libraries | 20% | 7 | 10 | 6 | 6 |
| Developer Experience | 15% | 9 | 9 | 7 | 5 |
| Documentation | 10% | 6 | 10 | 6 | 6 |
| Ecosystem | 10% | 10 | 9 | 7 | 6 |
| **Weighted Score** | | **7.25** | **9.45** | **6.95** | **6.45** |

## Consequences

### Positive

- **Excellent image processing**: Pillow and OpenCV provide industry-leading capabilities
- **Automatic API docs**: OpenAPI/Swagger generated automatically
- **Type safety**: Pydantic validates all inputs automatically
- **Async performance**: Handles concurrent requests efficiently
- **Rich QR ecosystem**: Multiple mature QR libraries available
- **Rapid development**: Python enables fast iteration

### Negative

- **GIL limitations**: CPU-bound tasks need process workers (mitigated by Celery/async)
- **Deployment complexity**: Requires ASGI server (Uvicorn/Gunicorn)
- **Memory usage**: Higher than compiled languages

### Mitigations

| Concern | Mitigation |
|---------|------------|
| GIL/CPU-bound | Use Celery workers for heavy image processing |
| Memory usage | Container resource limits, horizontal scaling |
| Deployment | Docker containerization with Uvicorn |

## Implementation Notes

```
Tech Stack:
- Framework: FastAPI 
- ASGI Server: Uvicorn with Gunicorn
- Validation: Pydantic v2
- QR Library: python-qrcode, segno
- Image Processing: Pillow, OpenCV (optional)
- Async ORM: SQLAlchemy 2.0 with asyncpg
```