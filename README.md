# FirmaForge

A powerful firmware modification and analysis tool for routers, IoT devices, and embedded systems.

## Features

- **Firmware Detection**: Automatically detects filesystem types (SquashFS, JFFS2, ext2/3/4, CramFS, UBIFS)
- **Extraction**: Extracts firmware filesystems to working directories
- **Analysis**: Detailed firmware analysis without extraction
- **CLI Interface**: Easy-to-use command-line interface

## Installation

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

## Usage

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

### Check Tools

```bash
# Activate the conda environment first
conda activate ffenv

# Check which extraction tools are available
firmaforge tools
```

## Supported Filesystems

- **SquashFS**: Compressed read-only filesystem (common in routers)
- **JFFS2**: Journaling Flash File System version 2
- **ext2/3/4**: Extended filesystem family
- **CramFS**: Compressed ROM filesystem
- **UBIFS**: Unsorted Block Image File System

## Examples

### Basic Extraction

```bash
# Activate the conda environment first
conda activate ffenv

# Extract a router firmware
firmaforge extract router_firmware.bin

# This creates a directory called 'router_firmware_extracted' with all files
```

### Analysis Only

```bash
# Activate the conda environment first
conda activate ffenv

# Get detailed information about firmware
firmaforge analyze firmware.bin --format json
```

## Development

### Project Structure

```
firmaforge/
├── firmaforge/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── detector.py     # Firmware detection
│   └── extractor.py    # Extraction engine
├── requirements.txt
├── setup.py
└── README.md
```

### Adding New Filesystem Support

1. Add the filesystem type to `FirmwareType` enum in `detector.py`
2. Add magic signature to `SIGNATURES` dictionary
3. Implement extraction method in `extractor.py`
4. Update `get_filesystem_info()` method

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Roadmap

- [x] Firmware detection and analysis
- [x] Basic extraction functionality
- [ ] File modification capabilities
- [ ] Firmware repacking
- [ ] Checksum validation
- [ ] GUI interface
- [ ] Batch processing
