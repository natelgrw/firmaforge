# FirmaForge

A powerful firmware modification and analysis tool for routers, IoT devices, and embedded systems. FirmaForge provides a complete 8-step pipeline for firmware security analysis, modification, and vulnerability discovery.

## 🚀 Features

- **🔍 Firmware Detection**: Automatically detects filesystem types (SquashFS, JFFS2, ext2/3/4, CramFS, UBIFS)
- **📁 Extraction**: Extracts firmware filesystems to working directories
- **✏️ File Modification**: Insert, remove, and replace files in extracted filesystems
- **🔒 Security & Patching**: Apply security patches and hardening measures
- **🎯 Fuzzing**: Comprehensive fuzzing for vulnerability discovery
- **✅ Validation**: Validate modified filesystems and test for crashes
- **📦 Repacking**: Rebuild modified filesystems into bootable firmware images
- **🔧 Analysis**: Detailed firmware analysis without extraction
- **🖥️ CLI Interface**: Easy-to-use command-line interface

## 📁 Repository Structure

```
firmaforge/
├── firmaforge/              # Core Python package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── detector.py         # Firmware detection
│   ├── extractor.py        # Extraction engine
│   ├── modifier.py         # File modification operations
│   ├── repacker.py         # Filesystem repacking
│   ├── builder.py          # Advanced firmware building
│   └── fuzzer.py           # Fuzzing capabilities
├── demos/                   # Demonstration scripts and results
│   ├── demo_complete_pipeline.py    # ⭐ Main 8-step pipeline demo
│   ├── demo_fuzzing.py             # Fuzzing capabilities demo
│   ├── demo.py                     # Basic functionality demo
│   ├── demo_firmware_fs/           # Mock embedded Linux filesystem
│   └── test_pipeline_results/      # Demo test results and documentation
├── examples/                # Example firmware files
│   ├── demo_squashfs_firmware.bin  # SquashFS firmware example
│   ├── demo_router_firmware.bin    # TRX container example
│   ├── demo_jffs2_firmware.bin     # JFFS2 filesystem example
│   └── demo_firmware_header.bin    # Generic firmware header
├── tests/                   # Unit tests
│   ├── test_detector.py
│   ├── test_extractor.py
│   ├── test_modifier.py
│   ├── test_repacker.py
│   ├── test_builder.py
│   └── test_fuzzer.py
├── docs/                    # Documentation
├── ffenv.yml               # Conda environment
├── setup.py
└── README.md
```

## 🛠️ Installation

### Prerequisites

Install the required extraction tools:

**macOS:**
```bash
brew install squashfs-tools jefferson p7zip e2fsprogs cramfsprogs ubi_reader
```

**Ubuntu/Debian:**
```bash
sudo apt install squashfs-tools jefferson p7zip-full e2fsprogs cramfsprogs ubi-utils
```

### Install FirmaForge

```bash
# Clone the repository
git clone <repository-url>
cd firmaforge

# Run the installation script (creates conda environment)
./install.sh

# Or manually create conda environment
conda env create -f ffenv.yml
conda activate ffenv
pip install -e .
```

## 🚀 Quick Start

### Complete Pipeline Demo
```bash
# Activate the conda environment first
conda activate ffenv

# Run the complete 8-step pipeline demonstration
python demos/demo_complete_pipeline.py
```

### Individual Capability Demos
```bash
# Fuzzing capabilities
python demos/demo_fuzzing.py

# Extraction and analysis
python demos/demo_extraction_analysis.py

# File modification workflow
python demos/demo_complete_workflow.py
```

## 📖 Usage

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

### Fuzzing for Vulnerability Discovery

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

### Check Tools

```bash
# Activate the conda environment first
conda activate ffenv

# Check which extraction and repacking tools are available
firmaforge tools
```

## 🔧 Complete 8-Step Pipeline

FirmaForge implements a comprehensive 8-step pipeline for firmware security analysis:

1. **🔍 Firmware Detection & Analysis** - Identify filesystem types and container formats
2. **📁 Filesystem Extraction** - Extract embedded Linux filesystems
3. **🔍 Detailed Filesystem Analysis** - Analyze file types, permissions, and structure
4. **✏️ File Modification Operations** - Insert, replace, and remove files
5. **🔒 Security & Patching** - Apply security hardening measures
6. **🎯 Fuzzing for Vulnerability Discovery** - Test for crashes and vulnerabilities
7. **✅ Validation & Testing** - Validate modified filesystems and test fuzzed files
8. **📦 Repacking & Rebuilding** - Rebuild firmware images in various formats

## 📊 Test Results

Comprehensive test results are available in `test_pipeline_results/`:

- **Test Coverage**: 88.5% overall success rate
- **Fuzzing Results**: 300+ fuzzed files generated across 4 strategies
- **Crash Detection**: 4 distinct crash types identified
- **Validation**: 100% pass rate for filesystem validation
- **Integration**: All 8 pipeline steps validated

See `test_pipeline_results/pipeline_test_report.md` for detailed results.

## 🗂️ Supported Filesystems

- **SquashFS**: Compressed read-only filesystem (common in routers)
- **JFFS2**: Journaling Flash File System version 2
- **ext2/3/4**: Extended filesystem family
- **CramFS**: Compressed ROM filesystem
- **UBIFS**: Unsorted Block Image File System

## 📚 Documentation

- **Demos**: See `demos/README.md` for demonstration scripts
- **Examples**: See `examples/README.md` for sample firmware files
- **Test Results**: See `test_pipeline_results/README.md` for comprehensive test documentation
- **API Reference**: See individual module docstrings for detailed API documentation

## 🔬 Examples

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

# 3. Fuzz for vulnerabilities
firmaforge fuzz router_firmware_extracted --iterations 20 --strategy random

# 4. Validate the modifications
firmaforge validate router_firmware_extracted

# 5. Build complete firmware with container support
firmaforge build router_firmware_extracted modified_firmware.bin --original-firmware router_firmware.bin

# 6. Verify the new firmware
firmaforge analyze modified_firmware.bin
```

### Analysis Only

```bash
# Activate the conda environment first
conda activate ffenv

# Get detailed information about firmware
firmaforge analyze firmware.bin --format json
```

## 🧪 Development

### Running Tests

```bash
# Activate the conda environment first
conda activate ffenv

# Run all tests
pytest

# Run specific test files
pytest tests/test_detector.py
pytest tests/test_fuzzer.py

# Run with verbose output
pytest -v
```

### Adding New Filesystem Support

1. Add the filesystem type to `FirmwareType` enum in `detector.py`
2. Add magic signature to `SIGNATURES` dictionary
3. Implement extraction method in `extractor.py`
4. Implement repacking method in `repacker.py`
5. Update `get_filesystem_info()` and `get_repacking_info()` methods
6. Add tests in the appropriate test files

## 📈 Roadmap

- [x] Firmware detection and analysis
- [x] Basic extraction functionality
- [x] File modification capabilities (insert, remove, replace)
- [x] Firmware repacking
- [x] Advanced firmware building with container support
- [x] Checksum calculation and validation
- [x] Filesystem validation
- [x] Comprehensive fuzzing capabilities
- [x] Complete 8-step pipeline integration
- [ ] GUI interface
- [ ] Batch processing
- [ ] Advanced filesystem support (UBIFS repacking)
- [ ] Firmware signing and verification
- [ ] Machine learning-based vulnerability detection

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🎯 Perfect for UROP Applications

FirmaForge is ideal for demonstrating capabilities in:
- **Firmware Security Analysis**
- **Vulnerability Discovery**
- **Embedded Systems Security**
- **Python Development**
- **System Programming**
- **Security Research**

The comprehensive test suite and documentation make it perfect for academic and research applications.