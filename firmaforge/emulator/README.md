# FirmaForge QEMU Emulator Module

This module provides QEMU-based emulation and dynamic analysis capabilities for FirmaForge, enabling firmware rehosting and real-time vulnerability discovery.

- Automatic firmware architecture detection
- Virtual hardware creation using QEMU emulation
- Firmware execution in controlled virtual environments
- Dynamic fuzzing during execution
- Automatic crash detection and vulnerability discovery
- Multi-architecture support (ARM, MIPS, x86, RISC-V, etc.)

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
