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

## Using Example Files

### Basic Detection
```python
from firmaforge.detector import FirmwareDetector

detector = FirmwareDetector()
result = detector.detect_firmware_type('examples/demo_squashfs_firmware.bin')
print(f"Type: {result['filesystem_type']}")
```

### Fuzzing Examples
```python
from firmaforge.fuzzer import FirmwareFuzzer

fuzzer = FirmwareFuzzer()
result = fuzzer.fuzz_firmware_file('examples/demo_squashfs_firmware.bin', 'output', 'random', 10)
```

### Analysis Examples
```python
from firmaforge.detector import FirmwareDetector

detector = FirmwareDetector()
info = detector.get_firmware_info('examples/demo_router_firmware.bin')
print(f"Size: {info['file_size']} bytes")
print(f"Signatures: {info['signatures_found']}")
```

## Creating New Examples

### Mock Firmware Creation
To create new example firmware files:

1. **SquashFS**: Use `mksquashfs` to create from directory
2. **TRX**: Use custom TRX header creation
3. **JFFS2**: Use `mkfs.jffs2` to create from directory
4. **Headers**: Create with specific magic signatures

### Example Creation Script
```python
# Create mock SquashFS firmware
import subprocess
subprocess.run(['mksquashfs', 'source_dir', 'output.squashfs', '-comp', 'gzip'])

# Create mock JFFS2 firmware
subprocess.run(['mkfs.jffs2', '-d', 'source_dir', '-o', 'output.jffs2'])
```

## File Validation

All example files are validated to ensure:
- ✅ Correct magic signatures
- ✅ Proper file structure
- ✅ Valid headers and metadata
- ✅ Compatible with FirmaForge tools

## Security Considerations

⚠️ **Important**: These are example files for testing and demonstration purposes only. They do not contain real firmware or sensitive data.

- Files are intentionally small and simple
- No real system binaries or sensitive information
- Safe for public distribution and testing
- Do not use in production environments

## File Maintenance

### Updating Examples
When updating example files:
1. Ensure compatibility with current FirmaForge version
2. Update file size and signature information
3. Test with all demo scripts
4. Update this documentation

### Adding New Formats
To add new firmware format examples:
1. Create the example file
2. Add format documentation
3. Update detection tests
4. Add to demo scripts
5. Update this README

## Troubleshooting

### Common Issues
1. **File not found**: Ensure you're running from project root
2. **Invalid format**: Check file integrity and magic signatures
3. **Permission errors**: Ensure read permissions for example files
4. **Detection failures**: Verify magic signatures are correct

### File Verification
```bash
# Check file types
file examples/*.bin

# Check magic signatures
hexdump -C examples/demo_squashfs_firmware.bin | head -1
hexdump -C examples/demo_router_firmware.bin | head -1
```

---

**Note**: These example files are designed for testing and demonstration. For real firmware analysis, use actual firmware files from your target devices.