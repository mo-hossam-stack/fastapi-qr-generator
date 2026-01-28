# ADR-003: QR Code Generation Library

## Status

**Accepted**

## Date

January 2026

## Context

We need to select a QR code generation library for the Python/FastAPI backend. The library must support:

- Standard QR code generation (URL, text, vCard, WiFi, etc.)
- Customizable colors (foreground/background)
- Multiple error correction levels (L, M, Q, H)
- High-resolution output
- Multiple output formats (PNG, SVG, at minimum)
- Logo/image embedding capability
- Good performance for high-volume generation

## Decision

**Selected: `qrcode` library with Pillow, supplemented by `segno` for SVG**

We will use the **`qrcode`** Python library (python-qrcode) as the primary generator with **Pillow** for image manipulation and logo embedding. **`segno`** will be used for high-quality SVG output.

## Alternatives Considered

### Option 1: qrcode (python-qrcode)

| Aspect | Assessment |
|--------|------------|
| Maturity | Excellent (10+ years, widely used) |
| Documentation | Good |
| PNG Support | Excellent (via Pillow) |
| SVG Support | Basic |
| Customization | Good (colors, box size, border) |
| Logo Embedding | Manual (via Pillow) |
| Performance | Good |
| Maintenance | Active |

### Option 2: segno

| Aspect | Assessment |
|--------|------------|
| Maturity | Good (6+ years) |
| Documentation | Excellent |
| PNG Support | Good |
| SVG Support | Excellent (native, optimized) |
| Customization | Excellent (colors, styles) |
| Logo Embedding | Not built-in |
| Performance | Excellent |
| Maintenance | Active |

### Option 3: PyQRCode

| Aspect | Assessment |
|--------|------------|
| Maturity | Moderate |
| Documentation | Good |
| PNG Support | Via pypng |
| SVG Support | Basic |
| Customization | Limited |
| Logo Embedding | Not supported |
| Performance | Good |
| Maintenance | Limited |

### Option 4: qrcode-artistic

| Aspect | Assessment |
|--------|------------|
| Maturity | New |
| Documentation | Limited |
| PNG Support | Good |
| SVG Support | Limited |
| Customization | Excellent (artistic styles) |
| Logo Embedding | Built-in |
| Performance | Moderate |
| Maintenance | Active |

## Comparison Matrix

| Criteria | Weight | qrcode | segno | PyQRCode | qrcode-artistic |
|----------|--------|--------|-------|----------|-----------------|
| Maturity/Stability | 20% | 10 | 8 | 6 | 5 |
| PNG Quality | 20% | 10 | 8 | 7 | 8 |
| SVG Quality | 15% | 6 | 10 | 6 | 5 |
| Customization | 20% | 8 | 9 | 5 | 10 |
| Performance | 15% | 8 | 9 | 8 | 6 |
| Documentation | 10% | 8 | 9 | 7 | 5 |
| **Weighted Score** | | **8.5** | **8.7** | **6.35** | **6.85** |

## Hybrid Approach

Given the strengths of each library, we will use a **hybrid approach**:

```
┌─────────────────────────────────────────────────────────────┐
│                QR Generation Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   qrcode    │───▶│   Pillow    │───▶│  PNG/JPG    │     │
│  │  (matrix)   │    │ (rendering) │    │  Output     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                                    │
│         │           ┌─────────────┐    ┌─────────────┐     │
│         └──────────▶│   segno     │───▶│    SVG      │     │
│                     │ (SVG render)│    │  Output     │     │
│                     └─────────────┘    └─────────────┘     │
│                                                              │
│  Logo Embedding: Pillow composite on generated QR           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Responsibilities

| Library | Use Case |
|---------|----------|
| `qrcode` | Generate QR matrix, PNG base rendering |
| `Pillow` | Logo embedding, color manipulation, resizing, format conversion |
| `segno` | High-quality SVG output, EPS output |

## Consequences

### Positive

- **Best of both worlds**: qrcode's maturity + segno's SVG quality
- **Full format support**: PNG, SVG, JPG, EPS all covered
- **Flexible customization**: Pillow enables any image manipulation
- **Logo embedding**: Full control via Pillow composite operations
- **Battle-tested**: Both libraries are widely used in production
- **Good performance**: Both libraries are optimized

### Negative

- **Two dependencies**: Slightly more complexity
- **Logo embedding is manual**: Need to implement composite logic
- **SVG logo embedding**: Requires different approach than PNG

### Implementation Details

```python
# PNG Generation with Logo
from qrcode import QRCode, constants
from PIL import Image

def generate_png_with_logo(data, logo_path, size, colors):
    qr = QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_H,  # High for logo
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=colors['fg'], back_color=colors['bg'])
    
    if logo_path:
        logo = Image.open(logo_path)
        # Resize logo to 20-30% of QR size
        # Paste in center
        img.paste(logo, position, logo)
    
    return img

# SVG Generation
import segno

def generate_svg(data, colors, scale):
    qr = segno.make(data, error='H')
    return qr.svg_inline(
        scale=scale,
        dark=colors['fg'],
        light=colors['bg']
    )
```

## Error Correction Recommendations

| Use Case | Level | Recovery | Recommendation |
|----------|-------|----------|----------------|
| No logo | M (15%) | 15% damage | Default for most |
| Small logo | Q (25%) | 25% damage | Logo < 15% area |
| Large logo | H (30%) | 30% damage | Logo 15-25% area |
| Harsh environment | H (30%) | 30% damage | Outdoor, industrial |

## References

- [python-qrcode Documentation](https://github.com/lincolnloop/python-qrcode)
- [Segno Documentation](https://segno.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [QR Code Error Correction](https://www.qrcode.com/en/about/error_correction.html)

---