# FirmaForge Demos

This directory contains demonstration scripts that showcase FirmaForge's capabilities across different use cases and scenarios.

## Demo Scripts

### 1. `demo_complete_pipeline.py` ⭐ **MAIN DEMO**
**Complete 8-step integrated pipeline demonstration**

This is the flagship demo that showcases all of FirmaForge's capabilities in one cohesive workflow:

- **Step 1**: Firmware Detection & Analysis
- **Step 2**: Filesystem Extraction  
- **Step 3**: Detailed Filesystem Analysis
- **Step 4**: File Modification Operations
- **Step 5**: Security & Patching
- **Step 6**: Fuzzing for Vulnerability Discovery
- **Step 7**: Validation & Testing
- **Step 8**: Repacking & Rebuilding

**Usage**: `python demo_complete_pipeline.py`

**Best for**: UROP presentations, comprehensive demonstrations, showing complete workflow

### 2. `demo_fuzzing.py`
**Fuzzing capabilities demonstration**

Shows FirmaForge's fuzzing capabilities across different strategies:

- Random byte mutation
- Bit flipping attacks
- Magic number fuzzing
- Boundary value testing
- Filesystem content fuzzing

**Usage**: `python demo_fuzzing.py`

**Best for**: Security researchers, vulnerability discovery demonstrations

### 3. `demo.py`
**Basic functionality demonstration**

Simple demonstration of core FirmaForge features:

- Basic firmware detection
- Tool availability checking
- Simple file operations

**Usage**: `python demo.py`

**Best for**: Quick overview, basic functionality

## Demo Data

### `demo_firmware_fs/`
**Mock embedded Linux filesystem**

A realistic embedded Linux filesystem structure containing:

- `/bin/` - System binaries (busybox, cat, echo, ls, sh)
- `/etc/` - Configuration files (passwd, security.conf)
- `/lib/` - Library files
- `/proc/` - Process information
- `/sbin/` - System administration binaries
- `/usr/` - User programs and data
- `/var/` - Variable data

**Used by**: All demo scripts for filesystem operations

### `test_pipeline_results/`
**Demo test results and documentation**

Contains comprehensive test results and documentation from running the demos:

- `README.md` - Test pipeline documentation
- `pipeline_test_report.md` - Detailed test report with statistics

**Test Results Include:**
- 88.5% overall success rate
- 300+ fuzzed files generated across 4 strategies
- 4 distinct crash types identified
- Complete 8-step pipeline validation
- Performance metrics and recommendations

**Used by**: Documentation and validation of demo capabilities

## Running the Demos

### Prerequisites
```bash
# Install dependencies
pip install -e .

# Ensure external tools are available
# (unsquashfs, jefferson, mkimage, etc.)
```

### Quick Start
```bash
# Run the main comprehensive demo
python demos/demo_complete_pipeline.py

# Run specific capability demos
python demos/demo_fuzzing.py
python demos/demo.py

# Or run from within the demos directory
cd demos
python demo_complete_pipeline.py
python demo_fuzzing.py
python demo.py
```

### Demo Output
All demos provide:
- ✅ Success indicators for completed operations
- ❌ Error indicators for failed operations
- 📊 Statistics and metrics
- 🔍 Detailed analysis results
- 📋 Summary reports

## Demo Customization

### Modifying Demo Parameters
Most demos accept parameters that can be modified:

- **Fuzzing iterations**: Change number of fuzzed files generated
- **File operations**: Modify which files are inserted/replaced/removed
- **Output directories**: Customize where results are saved
- **Verbose output**: Enable detailed logging

### Adding New Demos
To create a new demo:

1. Copy an existing demo as a template
2. Modify the functionality as needed
3. Update the documentation
4. Test thoroughly
5. Add to this README

## Demo Results

Demo results are typically saved to:
- `demos/test_pipeline_results/` - Fuzzing and test results
- `demos/test_pipeline_results/fuzz_output_*/` - Individual fuzzing outputs
- Console output - Real-time progress and results

## Troubleshooting

### Common Issues
1. **Missing dependencies**: Install with `pip install -e .`
2. **External tools not found**: Install required system tools
3. **Permission errors**: Ensure write permissions for output directories
4. **File not found**: Run demos from the project root directory

### Getting Help
- Check the main README.md for installation instructions
- Review the test results in `test_pipeline_results/`
- Examine the source code in `firmaforge/` for implementation details

---

**Note**: These demos are designed to showcase FirmaForge's capabilities and may use simulated data or simplified operations for demonstration purposes. For production use, refer to the main CLI interface and API documentation.