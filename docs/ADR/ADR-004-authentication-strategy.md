# ADR-004: Authentication Strategy

## Status

**Accepted**

## Date

January 2026

## Context

We need to establish an authentication strategy for the QR Code Generator API. The system has two primary authentication needs:

1. **User Authentication**: For web dashboard access and user management
2. **API Authentication**: For programmatic access to QR generation endpoints

Requirements:
- Secure authentication for user accounts
- Long-lived API keys for integrations
- Rate limiting per authentication method
- Support for future OAuth providers
- Stateless where possible for scalability

## Decision

**Selected: JWT for user sessions + API Keys for programmatic access**

We will implement a **dual authentication strategy**:
- **JWT (JSON Web Tokens)** for user session management
- **API Keys** for programmatic/integration access

## Alternatives Considered

### Option 1: Session-based Authentication Only

| Aspect | Assessment |
|--------|------------|
| Security | Good (server-controlled) |
| Scalability | Poor (session storage required) |
| API Integration | Poor (not suited for APIs) |
| Implementation | Simple |

### Option 2: JWT Only

| Aspect | Assessment |
|--------|------------|
| Security | Good (with proper implementation) |
| Scalability | Excellent (stateless) |
| API Integration | Moderate (token refresh needed) |
| Implementation | Moderate |

### Option 3: API Keys Only

| Aspect | Assessment |
|--------|------------|
| Security | Moderate (no expiration by default) |
| Scalability | Excellent |
| API Integration | Excellent |
| Implementation | Simple |

### Option 4: JWT + API Keys (Hybrid)

| Aspect | Assessment |
|--------|------------|
| Security | Excellent (best of both) |
| Scalability | Excellent |
| API Integration | Excellent |
| Implementation | Moderate-Complex |

## Comparison Matrix

| Criteria | Weight | Session | JWT | API Keys | Hybrid |
|----------|--------|---------|-----|----------|--------|
| Security | 25% | 8 | 8 | 6 | 9 |
| Scalability | 20% | 4 | 10 | 10 | 10 |
| API Suitability | 25% | 3 | 7 | 10 | 9 |
| User Experience | 15% | 9 | 7 | 5 | 8 |
| Implementation | 15% | 9 | 7 | 8 | 6 |
| **Weighted Score** | | **6.1** | **7.9** | **7.85** | **8.65** |

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flows                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USER AUTHENTICATION (Web Dashboard)                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Login   │───▶│ Validate │───▶│  Issue   │───▶│  Store   │ │
│  │  Form    │    │ Creds    │    │   JWT    │    │ (Cookie) │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                  │
│  JWT Structure:                                                  │
│  {                                                               │
│    "sub": "user_id",                                            │
│    "email": "user@example.com",                                 │
│    "plan": "pro",                                               │
│    "exp": 1234567890,                                           │
│    "iat": 1234567800                                            │
│  }                                                               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API AUTHENTICATION (Programmatic Access)                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  API     │───▶│ Validate │───▶│  Load    │───▶│ Process  │ │
│  │ Request  │    │ API Key  │    │  User    │    │ Request  │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                  │
│  Header: Authorization: Bearer qrg_live_xxxxxxxxxxxx            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## JWT Specification

### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "uuid-user-id",
    "email": "user@example.com",
    "plan": "pro",
    "permissions": ["qr:create", "qr:read", "qr:update", "qr:delete"],
    "iat": 1704067200,
    "exp": 1704153600
  }
}
```

### Token Lifecycle

| Token Type | Duration | Refresh |
|------------|----------|---------|
| Access Token | 15 minutes | Via refresh token |
| Refresh Token | 7 days | On use (rotation) |
| Remember Me | 30 days | Extended refresh |

## API Key Specification

### Key Format

```
Format: qrg_{environment}_{random_string}

Examples:
- qrg_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
- qrg_test_x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4

Components:
- Prefix: "qrg" (QR Generator)
- Environment: "live" or "test"
- Random: 32 character alphanumeric
```

### Key Properties

| Property | Value |
|----------|-------|
| Length | 40 characters total |
| Character Set | a-z, 0-9 |
| Storage | Hashed (SHA-256) in database |
| Prefix Storage | Plain text for identification |
| Revocation | Immediate effect |

### Key Management

```
┌─────────────────────────────────────────────────────────────┐
│                    API Key Lifecycle                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CREATE          ACTIVE           REVOKED          DELETED  │
│  ──────▶  Key  ──────────▶ Key  ──────────▶ Key  ────────▶ │
│  (shown   used    (daily)   flagged  (grace)   removed      │
│   once)                                                      │
│                                                              │
│  Features:                                                   │
│  - Multiple keys per user                                    │
│  - Key naming/labeling                                       │
│  - Last used timestamp                                       │
│  - Usage statistics                                          │
│  - IP allowlist (optional)                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Security Measures

### JWT Security

| Measure | Implementation |
|---------|----------------|
| Algorithm | HS256 (HMAC-SHA256) |
| Secret Rotation | Quarterly, with grace period |
| Token Storage | HttpOnly, Secure, SameSite cookies |
| Refresh Rotation | New refresh token on each use |
| Blacklisting | Redis set for revoked tokens |

### API Key Security

| Measure | Implementation |
|---------|----------------|
| Storage | SHA-256 hash only |
| Transmission | HTTPS only, in header |
| Rate Limiting | Per-key limits |
| IP Restriction | Optional allowlist |
| Audit Logging | All requests logged |

## Consequences

### Positive

- **Flexibility**: Different auth methods for different use cases
- **Scalability**: Stateless JWT enables horizontal scaling
- **Security**: Proper separation of concerns
- **Developer Experience**: API keys are simple to use
- **Auditability**: Full tracking of API key usage

### Negative

- **Complexity**: Two systems to maintain
- **Token Management**: JWT refresh adds complexity
- **Key Exposure Risk**: API keys if leaked, need immediate revocation

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Complexity | Clear separation, shared auth middleware |
| Token refresh | Automatic refresh in SDK/client |
| Key exposure | Prefix identification, quick revocation, alerts |

## Rate Limiting by Auth Type

| Auth Type | Tier | Limit |
|-----------|------|-------|
| API Key (Free) | Free | 100 requests/hour |
| API Key (Pro) | Pro | 1,000 requests/hour |
| API Key (Business) | Business | 10,000 requests/hour |
| JWT (Dashboard) | All | 300 requests/hour |
| Unauthenticated | N/A | 10 requests/hour |

## References

- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [API Key Best Practices](https://cloud.google.com/docs/authentication/api-keys)

---