# FirmaForge Demos

This directory contains demonstration scripts that showcase FirmaForge's capabilities across different use cases and scenarios.

## 📕 Demo Scripts

### 1. `demo_complete_pipeline.py` - Main Demo
**Complete 8-step integrated pipeline demonstration**

This demo showcases all of FirmaForge's capabilities in one cohesive workflow:

- **Step 1**: Firmware Detection & Analysis
- **Step 2**: Filesystem Extraction  
- **Step 3**: Detailed Filesystem Analysis
- **Step 4**: File Modification Operations
- **Step 5**: Security & Patching
- **Step 6**: Fuzzing for Vulnerability Discovery
- **Step 7**: QEMU Emulation & Dynamic Analysis
- **Step 8**: Repacking & Rebuilding

**Usage**: `python demo_complete_pipeline.py`

### 2. `demo_qemu_integration.py` - QEMU Demo
**QEMU emulation and dynamic analysis demonstration**

Shows FirmaForge's QEMU integration capabilities:

- Architecture detection and analysis
- QEMU emulation setup and configuration
- Dynamic fuzzing during emulation
- Crash detection and analysis
- Multi-architecture support (ARM, MIPS, x86, RISC-V)
- Real-time monitoring and logging

**Usage**: `python demo_qemu_integration.py`

### 3. `demo_fuzzing.py`
**Fuzzing capabilities demonstration**

Shows FirmaForge's fuzzing capabilities across different strategies:

- Random byte mutation
- Bit flipping attacks
- Magic number fuzzing
- Boundary value testing
- Filesystem content fuzzing

**Usage**: `python demo_fuzzing.py`

### 4. `demo.py`
**Basic functionality demonstration**

Simple demonstration of core FirmaForge features:

- Basic firmware detection
- Tool availability checking
- Simple file operations

**Usage**: `python demo.py`
