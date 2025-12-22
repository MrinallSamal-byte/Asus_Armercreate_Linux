# Supported Models

This document lists ASUS laptop models and their compatibility with ASUS Armoury Crate Linux.

## Compatibility Levels

- ✅ **Full Support**: All features work
- ⚠️ **Partial Support**: Some features may not work
- ❌ **Not Supported**: Hardware not compatible

## ROG (Republic of Gamers) Series

### ROG Zephyrus

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| G14 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| G15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| G16 (2023-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| M16 (2021-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| S17 (2021-2023) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Duo 15/16 | ⚠️ | ✅ | ✅ | ✅ | ✅ |

### ROG Strix

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| G15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| G17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| G18 (2023-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| SCAR 15/17/18 | ✅ | ✅ | ✅ | ✅ | ✅ |

### ROG Flow

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| X13 | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| Z13 | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ |
| X16 | ✅ | ✅ | ✅ | ✅ | ✅ |

## TUF Gaming Series

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| A15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| A17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| F15 (2021-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| F17 (2021-2024) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dash F15 | ✅ | ✅ | ⚠️ | ✅ | ✅ |

## VivoBook Series

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| Pro 14/15/16 OLED | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |
| Pro 14X/16X | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |
| S14/S15 | ⚠️ | ❌ | ❌ | ✅ | ❌ |

## ZenBook Series

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| Pro 14/15/16 | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |
| Duo | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |
| Flip | ⚠️ | ⚠️ | ❌ | ✅ | ❌ |

## ProArt Series

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| StudioBook Pro | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |
| ProArt P16 | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ |

## ExpertBook Series

| Model | Performance Modes | Fan Control | RGB | Battery Limit | GPU Switch |
|-------|------------------|-------------|-----|---------------|------------|
| B9/B9400 | ⚠️ | ⚠️ | ❌ | ✅ | ❌ |
| B5 | ⚠️ | ⚠️ | ❌ | ✅ | ❌ |

## Special Features by Model

### Anime Matrix Support

Models with Anime Matrix LED panel:
- ROG Zephyrus G14 (all years)
- ROG Zephyrus M16 (2022+)

### Per-Key RGB Support

Models with per-key RGB keyboard:
- ROG Strix SCAR series
- ROG Strix G15/G17 (2021+)
- Some TUF Gaming models

### GPU MUX Switch

Models with hardware GPU MUX:
- Most ROG models (2022+)
- TUF Gaming (2022+)

## Checking Your Model

Run hardware detection to see what's supported on your device:

```bash
asus-armoury-daemon --detect
```

This will show:
- Detected model name
- Available features
- Hardware capabilities

## Reporting Compatibility

If your model isn't listed or has different compatibility than shown:

1. Run `asus-armoury-daemon --detect`
2. Open an issue on GitHub with:
   - Your model name (from `cat /sys/class/dmi/id/product_name`)
   - Detection output
   - Which features work/don't work

We'll update this list based on user reports.
