# FirmaForge: Automated Firmware Extraction & Analysis

A firmware modification and analysis tool for routers, IoT devices, and embedded systems. FirmaForge provides a complete pipeline for firmware security analysis, modification, and vulnerability discovery, enhanced with QEMU emulation for dynamic analysis and rehosting.

Current Version: **0.2.0**

## ⚙️ Features

- **Firmware Detection**: Automatically detects filesystem types (SquashFS, JFFS2, ext2/3/4, CramFS, UBIFS)
- **Extraction**: Extracts firmware filesystems to working directories
- **File Modification**: Insert, remove, and replace files in extracted filesystems
- **Security & Patching**: Apply security patches and hardening measures
- **Fuzzing**: Comprehensive fuzzing for vulnerability discovery
- **Validation**: Validate modified filesystems and test for crashes
- **Repacking**: Rebuild modified filesystems into bootable firmware images
- **Analysis**: Detailed firmware analysis without extraction
- **CLI Interface**: Command-line interface
- **QEMU Emulation**: Dynamic analysis and rehosting with QEMU virtual machines
- **Dynamic Fuzzing**: Real-time fuzzing during firmware execution
- **Crash Detection**: Automatic crash detection and analysis

## 📁 Supported Filesystems

- **SquashFS**: Compressed read-only filesystem (common in routers)
- **JFFS2**: Journaling Flash File System version 2
- **ext2/3/4**: Extended filesystem family
- **CramFS**: Compressed ROM filesystem
- **UBIFS**: Unsorted Block Image File System

## 📈 Installation

Install the required extraction tools and QEMU:

```bash
# Extraction tools
sudo apt install squashfs-tools jefferson p7zip-full e2fsprogs cramfsprogs ubi-utils

# QEMU for emulation
sudo apt install qemu-system qemu-system-arm qemu-system-mips qemu-system-x86
```

Install FirmaForge:

```bash
# Clone the repository
git clone <repository-url>
cd firmaforge

# Create conda environment
conda env create -f ffenv.yml
conda activate ffenv
pip install -e .
```

## 🛠️ Usage

### Extract Firmware

```bash
# Activate the conda environment first
conda activate ffenv

# Extract firmware to a directory
firmaforge extract firmware.bin

# Extract to specific directory
firmaforge extract firmware.bin -o /path/to/output

# Show firmware info without extracting
firmaforge extract firmware.bin --info-only

# Verbose output
firmaforge extract firmware.bin -v
```

### Analyze Firmware

```bash
# Activate the conda environment first
conda activate ffenv

# Analyze firmware (text output)
firmaforge analyze firmware.bin

# JSON output
firmaforge analyze firmware.bin --format json

# YAML output
firmaforge analyze firmware.bin --format yaml
```

### File Modification

```bash
# Activate the conda environment first
conda activate ffenv

# Insert a new file into the filesystem
firmaforge insert filesystem_dir new_binary /usr/bin/new_binary

# Replace an existing file
firmaforge replace filesystem_dir updated_busybox /bin/busybox

# Remove a file
firmaforge remove filesystem_dir /usr/bin/old_binary

# List files in the filesystem
firmaforge list-files filesystem_dir

# Get information about a specific file
firmaforge info filesystem_dir /bin/busybox
```

### Fuzzing for Vulnerability

```bash
# Activate the conda environment first
conda activate ffenv

# Fuzz a firmware file
firmaforge fuzz firmware.bin --iterations 20 --strategy random

# Fuzz with different strategies
firmaforge fuzz firmware.bin --strategy bitflip --iterations 10
firmaforge fuzz firmware.bin --strategy magic --iterations 15
firmaforge fuzz firmware.bin --strategy boundary --iterations 10

# Fuzz an extracted filesystem
firmaforge fuzz filesystem_dir --iterations 10 --strategy file_content
```

### Repacking

```bash
# Repack the modified filesystem
firmaforge repack filesystem_dir modified_firmware.bin

# Repack with specific filesystem type
firmaforge repack filesystem_dir output.squashfs --filesystem-type squashfs

# Validate filesystem before repacking
firmaforge validate filesystem_dir
```

### Advanced Firmware Building

```bash
# Build complete firmware with container support
firmaforge build filesystem_dir firmware.bin --original-firmware original.bin

# Build with specific container format
firmaforge build filesystem_dir firmware.trx --container-format trx

# Build U-Boot image
firmaforge build filesystem_dir firmware.uboot --container-format uboot

# Extract metadata from original firmware
firmaforge metadata original_firmware.bin

# Show supported container formats
firmaforge containers
```

### QEMU Emulation & Dynamic Analysis

```bash
# Activate the conda environment first
conda activate ffenv

# Analyze firmware for emulation compatibility
firmaforge emulator analyze firmware.bin

# Emulate firmware with QEMU
firmaforge emulator emulate firmware.bin --architecture arm --memory 512M

# Fuzz firmware during emulation
firmaforge emulator fuzz firmware.bin output_dir --iterations 50 --strategy random

# List supported QEMU architectures
firmaforge emulator architectures

# Emulate with custom QEMU options
firmaforge emulator emulate firmware.bin --qemu-args "-netdev user,id=net0 -device rtl8139,netdev=net0"
```
