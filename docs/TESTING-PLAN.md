# Testing Plan

## QR Code Generator Test Strategy

**Version:** 1.0  
**Date:** January 2026  
**Status:** Draft

---

## 1. Overview

This document defines the testing strategy, test types, and quality gates for the QR Code Generator system. Testing covers unit, integration, API, performance, and security testing.

---

## 2. Testing Pyramid

```
                    ┌───────────────┐
                    │     E2E       │  ~5%
                    │    Tests      │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │  Integration  │  ~20%
                    │    Tests      │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │         API Tests             │  ~25%
            │    (Contract Testing)         │
            └───────────────┬───────────────┘
                            │
    ┌───────────────────────┴───────────────────────┐
    │                  Unit Tests                    │  ~50%
    │        (Functions, Classes, Modules)          │
    └───────────────────────────────────────────────┘
```

---

## 3. Test Categories

### 3.1 Unit Tests

**Scope:** Individual functions, classes, and modules in isolation.

**Coverage Target:** 80% line coverage, 70% branch coverage

#### Areas to Test

| Component | Test Focus |
|-----------|------------|
| QR Generator | Matrix generation, encoding modes, error correction |
| Image Processor | Resize, color conversion, logo embedding |
| URL Validator | Format validation, blocklist checking |
| Auth Module | Token generation, verification, hashing |
| Rate Limiter | Counter logic, window calculation |

#### Example Unit Tests

```python
# QR Generation Unit Tests
class TestQRGenerator:
    def test_generate_qr_from_url(self):
        """Test basic QR code generation from URL."""
        qr = generate_qr("https://example.com")
        assert qr is not None
        assert qr.version >= 1
        assert qr.error_correction == "M"
    
    def test_generate_qr_with_high_error_correction(self):
        """Test QR with H error correction for logo embedding."""
        qr = generate_qr("https://example.com", error_correction="H")
        assert qr.error_correction == "H"
    
    def test_generate_qr_content_too_large(self):
        """Test that oversized content raises error."""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ContentTooLargeError):
            generate_qr(long_url)
    
    def test_generate_qr_with_unicode(self):
        """Test QR generation with unicode content."""
        qr = generate_qr("https://example.com/путь/页面")
        assert qr is not None

# URL Validation Unit Tests
class TestURLValidator:
    def test_valid_https_url(self):
        assert validate_url("https://example.com") == True
    
    def test_valid_http_url(self):
        assert validate_url("http://example.com") == True
    
    def test_invalid_scheme(self):
        assert validate_url("ftp://example.com") == False
    
    def test_localhost_blocked(self):
        assert validate_url("http://localhost:8080") == False
    
    def test_private_ip_blocked(self):
        assert validate_url("http://192.168.1.1") == False
    
    def test_url_too_long(self):
        long_url = "https://example.com/" + "a" * 2100
        assert validate_url(long_url) == False

# Image Processor Unit Tests
class TestImageProcessor:
    def test_resize_image_to_max(self):
        """Test image resize to max dimensions."""
        large_image = create_test_image(5000, 5000)
        resized = resize_to_max(large_image, max_size=4096)
        assert resized.width <= 4096
        assert resized.height <= 4096
    
    def test_convert_cmyk_to_rgb(self):
        """Test CMYK to RGB conversion."""
        cmyk_image = create_cmyk_image()
        rgb_image = convert_to_rgb(cmyk_image)
        assert rgb_image.mode == "RGB"
    
    def test_strip_exif_metadata(self):
        """Test EXIF metadata removal."""
        image_with_exif = load_test_image("with_exif.jpg")
        cleaned = strip_metadata(image_with_exif)
        assert not has_exif(cleaned)
    
    def test_logo_embedding(self):
        """Test logo embedding in QR code."""
        qr_image = generate_qr_image("https://example.com", size=500)
        logo = load_test_image("logo.png")
        result = embed_logo(qr_image, logo, size_ratio=0.2)
        assert result.size == qr_image.size
```

### 3.2 Integration Tests

**Scope:** Component interactions and database operations.

**Focus Areas:**
- Database CRUD operations
- Redis caching behavior
- S3 storage operations
- Service-to-service communication

#### Example Integration Tests

```python
# Database Integration Tests
class TestQRCodeRepository:
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        return create_test_session()
    
    def test_create_qr_code(self, db_session):
        """Test QR code creation in database."""
        qr = QRCode(
            user_id=test_user.id,
            type="url",
            content="https://example.com",
            is_dynamic=True
        )
        db_session.add(qr)
        db_session.commit()
        
        assert qr.id is not None
        assert qr.short_code is not None
    
    def test_find_qr_by_short_code(self, db_session):
        """Test QR code lookup by short code."""
        qr = create_test_qr(db_session)
        
        found = QRCodeRepository.find_by_short_code(qr.short_code)
        
        assert found is not None
        assert found.id == qr.id
    
    def test_update_dynamic_qr_url(self, db_session):
        """Test updating dynamic QR destination."""
        qr = create_test_qr(db_session, is_dynamic=True)
        
        QRCodeRepository.update_destination(
            qr.id, 
            "https://newurl.com"
        )
        
        updated = QRCodeRepository.find_by_id(qr.id)
        assert updated.redirect.destination_url == "https://newurl.com"

# Redis Integration Tests
class TestRedisCache:
    @pytest.fixture
    def redis_client(self):
        """Create test Redis connection."""
        return create_test_redis()
    
    def test_cache_redirect(self, redis_client):
        """Test redirect URL caching."""
        cache_redirect("abc123", "https://example.com")
        
        cached = get_cached_redirect("abc123")
        
        assert cached == "https://example.com"
    
    def test_cache_expiry(self, redis_client):
        """Test cache TTL behavior."""
        cache_redirect("abc123", "https://example.com", ttl=1)
        
        time.sleep(2)
        
        cached = get_cached_redirect("abc123")
        assert cached is None
    
    def test_rate_limit_increment(self, redis_client):
        """Test rate limit counter."""
        key = "api:user123:hour"
        
        for i in range(5):
            increment_rate_limit(key)
        
        count = get_rate_limit_count(key)
        assert count == 5

# S3 Integration Tests
class TestS3Storage:
    @pytest.fixture
    def s3_client(self):
        """Create test S3 client (MinIO)."""
        return create_test_s3()
    
    def test_upload_qr_image(self, s3_client):
        """Test QR image upload to S3."""
        qr_image = generate_test_qr_image()
        
        url = upload_qr_image(qr_image, "test_qr_123", "png")
        
        assert url is not None
        assert "test_qr_123" in url
    
    def test_upload_and_retrieve(self, s3_client):
        """Test upload and download round-trip."""
        original = generate_test_qr_image()
        
        url = upload_qr_image(original, "test_qr_456", "png")
        retrieved = download_image(url)
        
        assert images_equal(original, retrieved)
```

### 3.3 API Tests

**Scope:** REST API endpoints, request/response validation, error handling.

**Tools:** pytest, httpx/requests, pytest-asyncio

#### Example API Tests

```python
# Authentication API Tests
class TestAuthAPI:
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecureP@ss123",
            "name": "Test User"
        })
        
        assert response.status_code == 201
        assert "access_token" in response.json()["data"]["tokens"]
    
    def test_register_duplicate_email(self, client, existing_user):
        """Test registration with existing email."""
        response = client.post("/api/v1/auth/register", json={
            "email": existing_user.email,
            "password": "SecureP@ss123",
            "name": "Test User"
        })
        
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_EXISTS"
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "weak",
            "name": "Test User"
        })
        
        assert response.status_code == 400
        assert "password" in str(response.json()["error"]["details"])
    
    def test_login_success(self, client, existing_user):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "email": existing_user.email,
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]["tokens"]
    
    def test_login_wrong_password(self, client, existing_user):
        """Test login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "email": existing_user.email,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

# QR Code Generation API Tests
class TestQRCodeAPI:
    def test_generate_url_qr(self, auth_client):
        """Test URL QR code generation."""
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "https://example.com",
            "type": "static",
            "options": {
                "size": 500,
                "error_correction": "M"
            }
        })
        
        assert response.status_code == 201
        data = response.json()["data"]["qr_code"]
        assert data["id"] is not None
        assert "png" in data["images"]
    
    def test_generate_dynamic_qr(self, auth_client):
        """Test dynamic QR code generation."""
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "https://example.com",
            "type": "dynamic"
        })
        
        assert response.status_code == 201
        data = response.json()["data"]["qr_code"]
        assert data["short_code"] is not None
        assert data["short_url"] is not None
    
    def test_generate_qr_with_logo(self, auth_client, uploaded_logo):
        """Test QR code generation with logo."""
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "https://example.com",
            "options": {
                "error_correction": "H",
                "logo": {
                    "url": uploaded_logo.url,
                    "size": 0.2
                }
            }
        })
        
        assert response.status_code == 201
    
    def test_generate_qr_invalid_url(self, auth_client):
        """Test QR generation with invalid URL."""
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "not-a-valid-url"
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_URL"
    
    def test_generate_qr_blocked_url(self, auth_client):
        """Test QR generation with blocked URL."""
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "http://localhost:8080"
        })
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "URL_BLOCKED"
    
    def test_generate_qr_unauthorized(self, client):
        """Test QR generation without auth."""
        response = client.post("/api/v1/qr/generate/url", json={
            "url": "https://example.com"
        })
        
        assert response.status_code == 401

# Dynamic QR Redirect Tests
class TestDynamicQRRedirect:
    def test_redirect_success(self, client, dynamic_qr):
        """Test dynamic QR redirect."""
        response = client.get(
            f"/{dynamic_qr.short_code}", 
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["Location"] == dynamic_qr.destination_url
    
    def test_redirect_not_found(self, client):
        """Test redirect with invalid short code."""
        response = client.get("/invalid123")
        
        assert response.status_code == 404
    
    def test_redirect_disabled(self, client, disabled_qr):
        """Test redirect for disabled QR."""
        response = client.get(f"/{disabled_qr.short_code}")
        
        assert response.status_code == 410
    
    def test_redirect_tracks_scan(self, client, dynamic_qr):
        """Test that redirect logs scan event."""
        initial_count = get_scan_count(dynamic_qr.id)
        
        client.get(f"/{dynamic_qr.short_code}")
        
        # Wait for async processing
        time.sleep(0.5)
        
        new_count = get_scan_count(dynamic_qr.id)
        assert new_count == initial_count + 1

# Rate Limiting Tests
class TestRateLimiting:
    def test_rate_limit_applied(self, auth_client):
        """Test rate limiting kicks in."""
        # Make requests up to limit
        for i in range(100):
            auth_client.post("/api/v1/qr/generate/url", json={
                "url": f"https://example.com/{i}"
            })
        
        # Next request should be rate limited
        response = auth_client.post("/api/v1/qr/generate/url", json={
            "url": "https://example.com/final"
        })
        
        assert response.status_code == 429
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
```

### 3.4 End-to-End Tests

**Scope:** Full user workflows from frontend to backend.

**Tools:** Playwright, Cypress

#### Example E2E Test Scenarios

```python
# E2E Test Scenarios
class TestUserWorkflows:
    def test_complete_registration_and_qr_creation(self, browser):
        """Test full user journey from registration to QR creation."""
        page = browser.new_page()
        
        # Register
        page.goto("/register")
        page.fill("[name=email]", "e2e@example.com")
        page.fill("[name=password]", "SecureP@ss123")
        page.fill("[name=name]", "E2E User")
        page.click("button[type=submit]")
        
        # Should redirect to dashboard
        page.wait_for_url("/dashboard")
        
        # Create QR code
        page.click("[data-testid=create-qr-btn]")
        page.fill("[name=url]", "https://example.com")
        page.click("[data-testid=generate-btn]")
        
        # Should show QR code
        page.wait_for_selector("[data-testid=qr-image]")
        assert page.locator("[data-testid=qr-image]").is_visible()
        
        # Download QR code
        with page.expect_download() as download_info:
            page.click("[data-testid=download-png-btn]")
        download = download_info.value
        assert download.suggested_filename.endswith(".png")
    
    def test_dynamic_qr_url_update(self, browser, auth_page):
        """Test updating dynamic QR destination."""
        page = auth_page
        
        # Create dynamic QR
        page.goto("/create")
        page.fill("[name=url]", "https://original.com")
        page.click("[data-testid=dynamic-toggle]")
        page.click("[data-testid=generate-btn]")
        
        # Get short URL
        short_url = page.locator("[data-testid=short-url]").text_content()
        
        # Update URL
        page.click("[data-testid=edit-btn]")
        page.fill("[name=destination_url]", "https://updated.com")
        page.click("[data-testid=save-btn]")
        
        # Verify redirect
        new_page = browser.new_page()
        new_page.goto(short_url)
        assert "updated.com" in new_page.url
```

### 3.5 Performance Tests

**Tools:** Locust, k6

#### Load Test Scenarios

```python
# Locust Load Test
from locust import HttpUser, task, between

class QRGeneratorUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["data"]["tokens"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def generate_qr(self):
        """Generate QR code."""
        self.client.post(
            "/api/v1/qr/generate/url",
            json={"url": "https://example.com"},
            headers=self.headers
        )
    
    @task(1)
    def list_qr_codes(self):
        """List QR codes."""
        self.client.get("/api/v1/qr", headers=self.headers)
    
    @task(5)
    def redirect_scan(self):
        """Simulate QR scan redirect."""
        self.client.get("/abc123", allow_redirects=False)

# Performance Targets
"""
Performance Test Targets:

1. QR Generation
   - P50: < 200ms
   - P95: < 500ms
   - P99: < 1000ms
   - Throughput: 100 req/s

2. Dynamic Redirect
   - P50: < 20ms
   - P95: < 50ms
   - P99: < 100ms
   - Throughput: 10,000 req/s

3. API List/Read
   - P50: < 50ms
   - P95: < 200ms
   - P99: < 500ms
   - Throughput: 500 req/s

4. Concurrent Users
   - Sustained: 1,000 users
   - Peak: 5,000 users
"""
```

### 3.6 Security Tests

**Tools:** OWASP ZAP, Bandit, Safety

#### Security Test Checklist

```markdown
## Authentication Security
- [ ] Password brute force protection
- [ ] JWT token expiration
- [ ] Refresh token rotation
- [ ] Session invalidation on password change
- [ ] API key revocation

## Input Validation
- [ ] SQL injection attempts
- [ ] XSS payloads in inputs
- [ ] Path traversal in file paths
- [ ] Command injection attempts
- [ ] XML/JSON injection

## Authorization
- [ ] Accessing other users' QR codes
- [ ] Modifying other users' data
- [ ] Privilege escalation
- [ ] IDOR vulnerabilities

## File Upload
- [ ] Malicious file upload
- [ ] File type bypass
- [ ] Oversized files
- [ ] Path traversal in filenames

## Rate Limiting
- [ ] Rate limit bypass attempts
- [ ] Distributed attack simulation
```

---

## 4. Test Data Management

### 4.1 Test Fixtures

```python
# conftest.py - Shared Fixtures
import pytest

@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_client(client, test_user):
    """Client with authentication."""
    token = create_access_token(test_user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture
def dynamic_qr(db_session, test_user):
    """Create test dynamic QR code."""
    qr = QRCode(
        user_id=test_user.id,
        type="url",
        content="https://example.com",
        is_dynamic=True,
        short_code="test123"
    )
    db_session.add(qr)
    db_session.commit()
    return qr

@pytest.fixture
def test_image():
    """Create test image for uploads."""
    from PIL import Image
    import io
    
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
```

### 4.2 Test Database

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: qr_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
  
  test-redis:
    image: redis:7
    ports:
      - "6380:6379"
  
  test-minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9001:9000"
```

---

## 5. CI/CD Test Pipeline

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/integration -v

  api-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run API tests
        run: pytest tests/api -v
      - name: Stop services
        run: docker-compose -f docker-compose.test.yml down

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json
      - name: Run Safety
        run: safety check -r requirements.txt
```

---

## 6. Quality Gates

### Pre-Merge Requirements

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Unit test pass rate | 100% | Yes |
| Integration test pass rate | 100% | Yes |
| Code coverage | ≥ 80% | Yes |
| New code coverage | ≥ 90% | Yes |
| Security scan | No high/critical | Yes |
| Linting | No errors | Yes |
| Performance regression | < 10% | Warning |

### Pre-Release Requirements

| Gate | Threshold | Blocking |
|------|-----------|----------|
| All test suites pass | 100% | Yes |
| E2E tests pass | 100% | Yes |
| Performance tests pass | Meet targets | Yes |
| Security audit | No critical findings | Yes |
| Load test | Handle expected load | Yes |

---

*Document Owner: QA Team*  
*Last Updated: January 2026*
