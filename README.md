# FirmaForge: A Firmware Reverse Engineering Toolkit
A powerful firmware modification and analysis tool for routers, IoT devices, and embedded systems.

## ⚙️ Features

- **Firmware Detection**: Automatically detects filesystem types (SquashFS, JFFS2, ext2/3/4, CramFS, UBIFS)
- **Extraction**: Extracts firmware filesystems to working directories
- **File Modification**: Insert, remove, and replace files in extracted filesystems
- **Repacking**: Rebuild modified filesystems into bootable firmware images
- **Analysis**: Detailed firmware analysis without extraction
- **CLI Interface**: Easy-to-use command-line interface

## 📁 Supported Filesystems

- **SquashFS**: Compressed read-only filesystem (common in routers)
- **JFFS2**: Journaling Flash File System version 2
- **ext2/3/4**: Extended filesystem family
- **CramFS**: Compressed ROM filesystem
- **UBIFS**: Unsorted Block Image File System

## 📥 Installation

```bash
sudo apt install squashfs-tools jefferson p7zip-full e2fsprogs cramfsprogs ubi-utils

# Clone the repository
git clone <repository-url>
cd firmaforge

# Run the installation script (creates conda environment)
./install_linux.sh

# Or manually create conda environment
conda env create -f ffenv.yml
conda activate ffenv
pip install -e .
```

## 🚀 Usage

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

### Check Tools

```bash
# Activate the conda environment first
conda activate ffenv

# Check which extraction and repacking tools are available
firmaforge tools
```

### Complete Workflow Example

```bash
# Activate the conda environment first
conda activate ffenv

# 1. Extract a router firmware
firmaforge extract router_firmware.bin
# This creates a directory called 'router_firmware_extracted' with all files

# 2. Modify the filesystem
firmaforge insert router_firmware_extracted new_busybox /bin/busybox
firmaforge remove router_firmware_extracted /usr/bin/unwanted_tool
firmaforge replace router_firmware_extracted updated_config /etc/config

# 3. Validate the modifications
firmaforge validate router_firmware_extracted

# 4. Build complete firmware with container support
firmaforge build router_firmware_extracted modified_firmware.bin --original-firmware router_firmware.bin

# 5. Verify the new firmware
firmaforge analyze modified_firmware.bin
```
