# ADR-007: Image Processing Pipeline

## Status

**Accepted**

## Date

January 2026

## Context

The QR Code Generator needs robust image processing capabilities for:

1. **Logo Embedding**: Placing user logos in the center of QR codes
2. **Image Upload Handling**: Validating and processing uploaded logos
3. **Format Conversion**: Generating PNG, SVG, JPG, EPS outputs
4. **Resizing**: Creating different sizes and thumbnails
5. **Color Processing**: Applying custom colors to QR codes

Requirements:
- Process images quickly (<500ms for typical operations)
- Handle various input formats (PNG, JPG, GIF, SVG, WebP)
- Maintain image quality
- Prevent malicious file uploads
- Scale horizontally for high volume

## Decision

**Selected: Pillow for raster processing + CairoSVG for vector, with async worker queue for heavy operations**

We will use **Pillow (PIL)** as the primary image processing library, supplemented by **CairoSVG** for SVG operations. Heavy processing tasks will be offloaded to **Celery workers**.

## Alternatives Considered

### Option 1: Pillow Only

| Aspect | Assessment |
|--------|------------|
| Raster Processing | Excellent |
| SVG Support | Poor (rasterization only) |
| Performance | Good |
| Memory Usage | Moderate |
| Ecosystem | Excellent |

### Option 2: OpenCV

| Aspect | Assessment |
|--------|------------|
| Raster Processing | Excellent |
| SVG Support | None |
| Performance | Excellent |
| Memory Usage | High |
| Ecosystem | Good |

### Option 3: ImageMagick (Wand)

| Aspect | Assessment |
|--------|------------|
| Raster Processing | Excellent |
| SVG Support | Good |
| Performance | Good |
| Memory Usage | High |
| Ecosystem | Good |

### Option 4: Pillow + CairoSVG (Hybrid)

| Aspect | Assessment |
|--------|------------|
| Raster Processing | Excellent |
| SVG Support | Excellent |
| Performance | Good |
| Memory Usage | Moderate |
| Ecosystem | Excellent |

## Comparison Matrix

| Criteria | Weight | Pillow | OpenCV | ImageMagick | Hybrid |
|----------|--------|--------|--------|-------------|--------|
| Raster Quality | 25% | 9 | 10 | 9 | 9 |
| SVG Support | 20% | 3 | 1 | 7 | 10 |
| Performance | 20% | 8 | 10 | 7 | 8 |
| Memory Efficiency | 15% | 8 | 5 | 5 | 8 |
| Ease of Use | 20% | 9 | 6 | 7 | 8 |
| **Weighted Score** | | **7.55** | **6.7** | **7.1** | **8.6** |

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Image Processing Pipeline                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT VALIDATION                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. Check file size (max 10MB)                                      │ │
│  │ 2. Validate magic bytes (file signature)                           │ │
│  │ 3. Check extension matches content                                  │ │
│  │ 4. Scan for embedded malware (optional)                            │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  IMAGE NORMALIZATION                                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. Convert to standard format (PNG for processing)                 │ │
│  │ 2. Strip EXIF/metadata (privacy + security)                        │ │
│  │ 3. Convert color space to RGB/RGBA                                 │ │
│  │ 4. Resize if oversized (max 4096x4096)                            │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  QR CODE GENERATION                                                      │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. Generate QR matrix from data                                    │ │
│  │ 2. Apply colors (foreground/background)                            │ │
│  │ 3. Apply style (squares, dots, rounded)                           │ │
│  │ 4. Render to target size                                           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  LOGO EMBEDDING (if requested)                                           │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. Load and validate logo image                                    │ │
│  │ 2. Resize logo to 20-30% of QR size                               │ │
│  │ 3. Add padding/border around logo                                  │ │
│  │ 4. Composite logo onto QR center                                   │ │
│  │ 5. Verify scannability                                             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  OUTPUT GENERATION                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PNG: Pillow save with optimization                                 │ │
│  │ JPG: Pillow save with quality=95                                   │ │
│  │ SVG: Segno native SVG generation                                   │ │
│  │ EPS: CairoSVG conversion                                           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Logo Embedding Algorithm

```
Logo Embedding Process:

1. CALCULATE SAFE LOGO SIZE
   - Maximum logo area: 30% of QR code area
   - With H error correction: up to 30% damage recovery
   - Safe logo size: 20-25% for best scannability
   
2. PREPARE LOGO
   - Resize to calculated size
   - Add white padding (5% of logo size)
   - Round corners (optional)
   - Apply transparency mask if needed

3. CALCULATE POSITION
   - Center of QR code
   - Account for quiet zone
   - Position = (qr_size - logo_size) / 2

4. COMPOSITE
   - Paste logo onto QR code
   - Use alpha channel for transparency
   - Blend if semi-transparent logo

5. VERIFY
   - Test scan the generated QR code
   - Retry with smaller logo if scan fails
```

## Async Processing

### When to Use Async Workers

| Operation | Sync/Async | Reason |
|-----------|------------|--------|
| Simple QR (no logo) | Sync | <200ms |
| QR with logo | Async | 200-500ms |
| Bulk generation | Async | Multiple QR codes |
| Format conversion | Async | CPU intensive |
| Large exports | Async | File I/O intensive |

### Celery Task Queue

```
┌─────────────────────────────────────────────────────────────┐
│                    Async Processing                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   API Server                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │  Request    │───▶│   Celery    │───▶│   Redis     │   │
│   │  Handler    │    │   .delay()  │    │   Queue     │   │
│   └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                                      │            │
│         │ Returns task_id                      │            │
│         ▼                                      ▼            │
│   ┌─────────────┐                       ┌─────────────┐   │
│   │  Client     │                       │   Celery    │   │
│   │  Polls      │◀──────────────────────│   Worker    │   │
│   │  Status     │   Result ready        │  (Process)  │   │
│   └─────────────┘                       └─────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## File Validation

### Magic Bytes Validation

| Format | Magic Bytes (hex) | Description |
|--------|-------------------|-------------|
| PNG | 89 50 4E 47 0D 0A 1A 0A | PNG signature |
| JPEG | FF D8 FF | JPEG SOI marker |
| GIF | 47 49 46 38 | "GIF8" |
| WebP | 52 49 46 46 ... 57 45 42 50 | RIFF...WEBP |
| SVG | 3C 3F 78 6D 6C or 3C 73 76 67 | <?xml or <svg |

### Validation Code Pattern

```python
MAGIC_BYTES = {
    'png': b'\x89PNG\r\n\x1a\n',
    'jpeg': b'\xff\xd8\xff',
    'gif': b'GIF8',
    'webp': b'RIFF',  # followed by WEBP
}

def validate_image_type(file_bytes: bytes, claimed_type: str) -> bool:
    """Validate that file content matches claimed type."""
    if claimed_type not in MAGIC_BYTES:
        return False
    return file_bytes.startswith(MAGIC_BYTES[claimed_type])
```

## Memory Management

### Strategies

1. **Stream Processing**: Process large files in chunks
2. **Temporary Files**: Use tempfile for intermediate results
3. **Cleanup Hooks**: Ensure cleanup even on errors
4. **Memory Limits**: Set per-process memory limits
5. **Image Size Limits**: Reject oversized images early

### Memory Limits

| Operation | Max Memory | Action if Exceeded |
|-----------|------------|-------------------|
| Logo upload | 50MB | Reject request |
| QR generation | 100MB | Return error |
| Batch processing | 500MB/worker | Queue remaining |

## Consequences

### Positive

- **High quality output**: Pillow produces excellent raster images
- **Full format support**: PNG, JPG, SVG, EPS all covered
- **Scalable**: Async workers handle heavy loads
- **Secure**: Proper validation prevents malicious uploads
- **Maintainable**: Well-known libraries with good documentation

### Negative

- **Complexity**: Multiple libraries to maintain
- **Worker overhead**: Celery adds infrastructure complexity
- **Memory usage**: Image processing is memory intensive

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Library complexity | Clear abstraction layer |
| Worker overhead | Use existing Redis for queue |
| Memory usage | Limits, streaming, cleanup |

## Performance Targets

| Operation | Target Latency | Method |
|-----------|---------------|--------|
| Simple QR generation | <200ms | Sync |
| QR with logo | <500ms | Sync or async |
| Format conversion | <1s | Async |
| Bulk generation (10) | <5s | Async |

## References

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [CairoSVG Documentation](https://cairosvg.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Image Security Best Practices](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)

---
