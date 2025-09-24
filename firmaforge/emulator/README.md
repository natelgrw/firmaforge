# FirmaForge QEMU Emulator Module

This module provides QEMU-based emulation and dynamic analysis capabilities for FirmaForge, enabling firmware rehosting and real-time vulnerability discovery.

## Overview

The emulator module provides:

- Automatic firmware architecture detection
- Virtual hardware creation using QEMU emulation
- Firmware execution in controlled virtual environments
- Dynamic fuzzing during execution
- Automatic crash detection and vulnerability discovery
- Multi-architecture support (ARM, MIPS, x86, RISC-V, etc.)

## Architecture

```
firmaforge/emulator/
├── __init__.py          # Module initialization
├── qemu_runner.py       # Core QEMU process management
├── cli.py              # Command-line interface
└── README.md           # This documentation
```

## Core Components

### QEMUEmulator Class (`qemu_runner.py`)

The main class that handles QEMU emulation operations:

```python
from firmaforge.emulator.qemu_runner import QEMUEmulator

emulator = QEMUEmulator()

# Detect firmware architecture
arch_info = emulator.detect_architecture('firmware.bin')

# Create emulation environment
config = emulator.create_emulation_environment('firmware.bin')

# Run emulation
result = emulator.emulate_firmware('firmware.bin', timeout=60)

# Fuzz during emulation
fuzz_result = emulator.fuzz_emulated_firmware('firmware.bin', 'output_dir', iterations=50)
```

### CLI Interface (`cli.py`)

Command-line interface for emulation operations:

```bash
# Analyze firmware for emulation
firmaforge emulator analyze firmware.bin

# Emulate firmware
firmaforge emulator emulate firmware.bin --architecture arm --memory 512M

# Fuzz during emulation
firmaforge emulator fuzz firmware.bin output_dir --iterations 100

# List supported architectures
firmaforge emulator architectures
```

## Supported Architectures

| Architecture | QEMU Command | Description |
|-------------|--------------|-------------|
| ARM | `qemu-system-arm` | ARM processors (common in IoT devices) |
| MIPS | `qemu-system-mips` | MIPS processors (routers, embedded) |
| x86_64 | `qemu-system-x86_64` | x86-64 processors |
| AArch64 | `qemu-system-aarch64` | 64-bit ARM processors |
| RISC-V | `qemu-system-riscv64` | RISC-V processors |
| PowerPC | `qemu-system-ppc` | PowerPC processors |
| SPARC | `qemu-system-sparc` | SPARC processors |
| Alpha | `qemu-system-alpha` | Alpha processors |
| S390X | `qemu-system-s390x` | IBM Z processors |

## Features

### Architecture Detection
- Automatic detection of firmware architecture requirements
- Magic signature analysis for architecture identification
- QEMU compatibility checking for detected architectures

### Emulation Environment Setup
- Memory configuration (default 256M, configurable)
- Network setup (user-mode networking by default)
- Monitor and serial interfaces for debugging
- Custom QEMU arguments support

### Dynamic Fuzzing
- Real-time fuzzing during firmware execution
- Multiple fuzzing strategies:
  - Random byte mutation
  - Bit flipping attacks
  - Magic number fuzzing
  - Boundary value testing
  - Memory corruption patterns
- Crash detection and analysis
- Performance monitoring and logging

### Process Management
- QEMU process lifecycle management
- Timeout handling and cleanup
- Resource monitoring (CPU, memory usage)
- Graceful shutdown procedures

### Crash Analysis
- Automatic crash detection from QEMU output
- Crash classification by type and severity
- Stack trace analysis (when available)
- Memory dump analysis (when available)

## Usage Examples

### Basic Emulation

```python
from firmaforge.emulator.qemu_runner import QEMUEmulator

emulator = QEMUEmulator()

# Analyze firmware
arch_info = emulator.detect_architecture('router_firmware.bin')
print(f"Architecture: {arch_info['architecture']}")
print(f"QEMU Command: {arch_info['qemu_command']}")

# Run emulation
result = emulator.emulate_firmware('router_firmware.bin', timeout=30)
print(f"Emulation result: {result['status']}")
```

### Dynamic Fuzzing

```python
# Fuzz firmware during emulation
fuzz_result = emulator.fuzz_emulated_firmware(
    firmware_path='router_firmware.bin',
    output_dir='fuzz_results',
    iterations=100,
    fuzz_type='random'
)

print(f"Fuzzing completed: {fuzz_result['status']}")
print(f"Crashes found: {len(fuzz_result['crashes'])}")
print(f"Unique crash types: {fuzz_result['unique_crashes']}")
```

### Custom QEMU Configuration

```python
# Create custom emulation environment
config = emulator.create_emulation_environment('firmware.bin')
config['memory_size'] = '1G'
config['network_enabled'] = True
config['custom_args'] = ['-netdev', 'user,id=net0', '-device', 'rtl8139,netdev=net0']

# Run with custom configuration
result = emulator.emulate_firmware('firmware.bin', config=config)
```

## Configuration

### Memory Configuration
- Default: 256M
- Range: 64M - 4G

### Network Configuration
- Default: User-mode networking
- Options: User-mode, TAP, or disabled

### Timeout Configuration
- Default: 60 seconds
- Range: 5 - 3600 seconds

### Fuzzing Configuration
- Iterations: Number of fuzzing attempts (default: 10)
- Strategies: Available fuzzing strategies
- Output: Directory for fuzzing results

## Dependencies

### Required
- QEMU: Virtual machine emulator
- psutil: Process monitoring and management
- firmaforge.detector: Firmware detection capabilities

### Installation

QEMU must be installed separately:

**macOS:**
```bash
brew install qemu
```

**Ubuntu/Debian:**
```bash
sudo apt install qemu-system qemu-system-arm qemu-system-mips qemu-system-x86
```

## Troubleshooting

### Common Issues

1. **QEMU not found**
   - Install QEMU using package manager
   - Ensure QEMU binaries are in PATH

2. **Architecture not supported**
   - Install additional QEMU system emulators
   - Check firmware architecture detection

3. **Emulation failures**
   - Check firmware compatibility
   - Verify memory requirements

4. **Permission errors**
   - Check file permissions
   - Ensure write access to output directories

## License

MIT License - See main project license for details.
