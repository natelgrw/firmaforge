# FirmaForge Examples

This directory contains example firmware files and sample data for testing and demonstration purposes.

## Example Files

### Firmware Files

#### `demo_squashfs_firmware.bin`
**SquashFS firmware image**
- **Size**: 2,040 bytes
- **Type**: SquashFS filesystem
- **Magic Signature**: `hsqs`
- **Purpose**: Demonstrates SquashFS detection and extraction
- **Used by**: All demo scripts for SquashFS operations

#### `demo_router_firmware.bin`
**TRX container firmware image**
- **Size**: 989 bytes
- **Type**: TRX container format
- **Magic Signature**: `HDR0`
- **Purpose**: Demonstrates TRX container detection and analysis
- **Used by**: Container format demos and fuzzing tests

#### `demo_jffs2_firmware.bin`
**JFFS2 filesystem image**
- **Size**: 2,062 bytes
- **Type**: JFFS2 filesystem
- **Magic Signature**: `\x85\x19\x03\x20`
- **Purpose**: Demonstrates JFFS2 detection and extraction
- **Used by**: JFFS2-specific demos and tests


### Firmware Headers

#### `demo_firmware_header.bin`
**Generic firmware header**
- **Size**: 32 bytes
- **Type**: Generic firmware header
- **Purpose**: Header analysis and detection testing
- **Used by**: Header analysis demos

## File Format Details

### SquashFS Format
- **Compression**: LZMA, LZ4, ZSTD, XZ
- **Block Size**: 4KB to 1MB
- **Features**: Read-only, compressed, embedded-friendly
- **Use Cases**: Router firmware, embedded Linux distributions

### TRX Container Format
- **Header**: 28-byte TRX header
- **Compression**: Optional
- **Features**: Checksum validation, partition support
- **Use Cases**: Linksys routers, Broadcom devices

### JFFS2 Format
- **Compression**: Zlib, LZMA, RTIME
- **Features**: Journaling, wear leveling, compression
- **Use Cases**: Flash storage, embedded systems
