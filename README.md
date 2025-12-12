# FirmaForge: Automated Firmware Analysis

FirmaForge is a Python package for automated firmware analysis of embedded Linux devices. 
The current version provides support for detecting architecture, endianness, container formats, 
filesystems, and bootloaders without manual inspection, generating detailed JSON reports.

Additionally, FirmaForge extracts kernel and root filesystem images for common decrypted
firmware (OpenWrt, Netgear, etc.) 

The result is a streamlined workflow for firmware security research.

**Current Version: 1.0.1**

## 📖 Installation & Usage

FirmaForge is designed to run in a Docker container with all dependencies pre-installed.

### Docker Setup

```bash
# build the Docker image
docker build -t firmaforge:latest .

# analyze a single firmware file
docker run --rm -v $(pwd):/workspace firmaforge:latest \
  python3 -c "
from firmaforge.summarize_results import analyze_firmware

analyze_firmware(
    '/workspace/demo_firmware/your_firmware.bin',
    '/workspace/results/your_firmware_analysis.json',
    extract_first=True,
    results_dir='/workspace/results'
)
"

# analyze all firmware files in demo_firmware/
bash analyze_all_firmware_docker.sh
```

### Interactive Shell

```bash
# start an interactive container
docker run -it --rm -v $(pwd):/workspace firmaforge:latest /bin/bash

cd /workspace
python3 -c "from firmaforge.summarize_results import analyze_firmware; \
            analyze_firmware('/workspace/demo_firmware/firmware.bin')"
```

## ⚙️ About FirmaForge

### Supported Firmware Formats

FirmaForge v1.0.0 focuses on standard firmware formats:

- **Netgear CHK**: TRX-based container format with SquashFS rootfs
- **OpenWrt TRX/SquashFS**: Standard OpenWrt sysupgrade images
- **Generic SquashFS**: Direct SquashFS images

Custom formats are not fully supported in v1.0 and are excluded from automated analysis.

### Firmware Detection

FirmaForge uses multi-layered detection to identify firmware components:

**Container Formats:**
- TRX (Linksys/Netgear routers)
- CHK (Netgear firmware format)
- FIT (U-Boot Flattened Image Tree)
- LZMA, GZIP, BZIP2, XZ compression

**Filesystem Types:**
- SquashFS (compressed read-only filesystem)
- ext2/3/4 (extended filesystem family)
- TAR archives

**Architecture Detection:**
Priority-based detection using:
1. Kernel image magic headers
2. Device Tree Blob (DTB) compatible strings
3. U-Boot image headers
4. ELF binary inspection
5. ELF header fallback detection

Supported architectures: ARM, AArch64, MIPS, PowerPC, x86, x86_64, RISC-V

**Endianness Detection:**
- ELF header analysis from extracted binaries
- Firmware-wide ELF scanning
- Architecture-based inference
- Strings analysis for endianness indicators

### Extraction

FirmaForge extracts firmware components to a structured directory:

```
results/
  <firmware_name>/
    raw_extracts/
      kernel/          # Extracted kernel images
      rootfs/          # Extracted root filesystem
    <firmware_name>_analysis.json
```

### Analysis Output

The `analyze_firmware()` function in `sumarize_results.py` generates a comprehensive JSON report with detection data.

## 📝 Citation

If you use FirmaForge in your research, please cite:

```
@software{firmaforge1.0.0,
  title={FirmaForge: Automated Firmware Analysis},
  author={Leung, Nathan},
  year={2025},
  url={https://github.com/natelgrw/firmaforge}
}
```
