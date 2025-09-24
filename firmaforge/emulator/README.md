# QEMU Integration for FirmaForge

This document describes FirmaForge's QEMU emulation capabilities, designed to address IGLOO's core challenge of automated rehosting and dynamic analysis of embedded firmware.

## 🎯 Overview

FirmaForge now includes comprehensive QEMU integration that enables:
- **Automated rehosting** of embedded firmware
- **Multi-architecture emulation** (ARM, MIPS, x86, RISC-V)
- **Dynamic fuzzing** with crash detection
- **Real-time monitoring** and introspection
- **Integration** with existing FirmaForge pipeline

### Supported Architectures

| Architecture | QEMU Command | Use Case |
|--------------|--------------|----------|
| **ARM** | `qemu-system-arm` | IoT devices, embedded systems |
| **AArch64** | `qemu-system-aarch64` | Modern ARM64 devices |
| **MIPS** | `qemu-system-mips` | Routers, network equipment |
| **MIPSel** | `qemu-system-mipsel` | Little-endian MIPS devices |
| **MIPS64** | `qemu-system-mips64` | 64-bit MIPS systems |
| **x86** | `qemu-system-i386` | Legacy embedded x86 |
| **x86_64** | `qemu-system-x86_64` | Modern x86_64 systems |
| **RISC-V32** | `qemu-system-riscv32` | RISC-V 32-bit systems |
| **RISC-V64** | `qemu-system-riscv64` | RISC-V 64-bit systems |

## 🚀 Usage

### Basic Emulation

```bash
# Emulate firmware with auto-detected architecture
firmaforge emulator emulate firmware.bin

# Specify architecture
firmaforge emulator emulate firmware.bin --architecture arm

# Enable verbose output
firmaforge emulator emulate firmware.bin --verbose

# Set memory and timeout
firmaforge emulator emulate firmware.bin --memory 512M --timeout 60
```

### Dynamic Fuzzing

```bash
# Fuzz emulated firmware
firmaforge emulator fuzz firmware.bin output_dir --iterations 100

# Fuzz with specific architecture
firmaforge emulator fuzz firmware.bin output_dir --architecture mips --iterations 50

# Verbose fuzzing with custom timeout
firmaforge emulator fuzz firmware.bin output_dir --iterations 200 --timeout 5 --verbose
```

### Analysis and Detection

```bash
# Analyze firmware for emulation compatibility
firmaforge emulator analyze firmware.bin

# List supported architectures
firmaforge emulator architectures

# JSON output for analysis
firmaforge emulator analyze firmware.bin --format json
```

## 🔧 Installation

### Prerequisites

```bash
# Install QEMU with multi-architecture support
# Ubuntu/Debian
sudo apt install qemu-system qemu-user

# macOS
brew install qemu

# Verify installation
qemu-system-x86_64 --version
```

### Python Dependencies

```bash
# Install FirmaForge with QEMU support
pip install -e .

# Additional dependencies are automatically installed
```

## 📋 Features

### 1. Automated Architecture Detection

```python
from firmaforge.emulator.qemu_runner import QEMUEmulator

emulator = QEMUEmulator()
architecture = emulator.detect_architecture('firmware.bin')
print(f"Detected architecture: {architecture}")
```

### 2. Emulation Environment Setup

```python
config = emulator.create_emulation_environment('firmware.bin')
print(f"QEMU command: {config['qemu_command']}")
print(f"Memory: {config['memory_size']}")
print(f"Network: {config['network_enabled']}")
```

### 3. Dynamic Fuzzing

```python
# Generate fuzz inputs
fuzz_inputs = [generate_random_data() for _ in range(100)]

# Run fuzzing
results = emulator.fuzz_emulated_firmware(config, fuzz_inputs, 100)
print(f"Crashes found: {results['crashes_found']}")
print(f"Crash rate: {results['crash_rate']:.2%}")
```

### 4. Crash Analysis

```python
# Analyze emulation results
crashes = results['crashes']
for crash in crashes:
    print(f"Crash type: {crash['type']}")
    print(f"Severity: {crash['severity']}")
    print(f"Timestamp: {crash['timestamp']}")
```
