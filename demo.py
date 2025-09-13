#!/usr/bin/env python3
"""
FirmaForge Demo Script

This script demonstrates the basic functionality of FirmaForge
for firmware detection and analysis.
"""

import os
import tempfile
from firmaforge.detector import FirmwareDetector, FirmwareType
from firmaforge.extractor import FirmwareExtractor
from firmaforge.modifier import FirmwareModifier
from firmaforge.repacker import FirmwareRepacker


def create_mock_firmware(firmware_type: FirmwareType, output_path: str):
    """Create a mock firmware file for testing"""
    with open(output_path, 'wb') as f:
        if firmware_type == FirmwareType.SQUASHFS:
            f.write(b'hsqs' + b'\x00' * 100)  # SquashFS magic
        elif firmware_type == FirmwareType.JFFS2:
            f.write(b'\x85\x19\x03\x20' + b'\x00' * 100)  # JFFS2 magic
        elif firmware_type == FirmwareType.EXT2:
            f.write(b'\x53\xef' + b'\x00' * 100)  # ext2 magic
        elif firmware_type == FirmwareType.CRAMFS:
            f.write(b'Compressed ROMFS' + b'\x00' * 100)  # CramFS magic
        else:
            f.write(b'\x00' * 100)  # Unknown


def main():
    """Run the demo"""
    print("🔧 FirmaForge Demo")
    print("=" * 50)
    
    # Initialize components
    detector = FirmwareDetector()
    extractor = FirmwareExtractor()
    modifier = FirmwareModifier()
    repacker = FirmwareRepacker()
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        print()
        
        # Test different firmware types
        test_types = [
            FirmwareType.SQUASHFS,
            FirmwareType.JFFS2,
            FirmwareType.EXT2,
            FirmwareType.CRAMFS,
            FirmwareType.UNKNOWN
        ]
        
        for firmware_type in test_types:
            print(f"🧪 Testing {firmware_type.value} detection:")
            
            # Create mock firmware
            firmware_path = os.path.join(temp_dir, f"test_{firmware_type.value}.bin")
            create_mock_firmware(firmware_type, firmware_path)
            
            # Detect firmware type
            result = detector.detect_firmware_type(firmware_path)
            
            print(f"   Detected: {result['filesystem_type'].value}")
            print(f"   File Size: {result['file_size']} bytes")
            print(f"   MIME Type: {result['mime_type']}")
            
            if result['signatures_found']:
                print(f"   Signatures: {len(result['signatures_found'])} found")
                for sig in result['signatures_found']:
                    print(f"     - {sig['type'].value} (confidence: {sig['confidence']:.2f})")
            
            # Get filesystem info
            fs_info = detector.get_filesystem_info(firmware_path, result['filesystem_type'])
            print(f"   Extractable: {'Yes' if fs_info['extractable'] else 'No'}")
            
            if fs_info['tools_required']:
                print(f"   Tools Required: {', '.join(fs_info['tools_required'])}")
            
            print()
        
        # Test tool availability
        print("🔧 Checking extraction tools:")
        extraction_tools = ['unsquashfs', 'jefferson', '7z', 'debugfs', 'cramfsck', 'ubireader']
        for tool in extraction_tools:
            available = extractor._check_tool_available(tool)
            status = "✅" if available else "❌"
            print(f"   {status} {tool}")
        
        print()
        print("🔨 Checking repacking tools:")
        repacking_tools = ['mksquashfs', 'mkfs.jffs2', 'mkfs.ext2', 'mkcramfs', 'tar']
        for tool in repacking_tools:
            available = repacker._check_tool_available(tool)
            status = "✅" if available else "❌"
            print(f"   {status} {tool}")
        
        # Demonstrate file modification capabilities
        print()
        print("📝 Demonstrating file modification capabilities:")
        
        # Create a mock filesystem directory
        mock_filesystem = os.path.join(temp_dir, "mock_filesystem")
        os.makedirs(mock_filesystem, exist_ok=True)
        os.makedirs(os.path.join(mock_filesystem, "bin"), exist_ok=True)
        os.makedirs(os.path.join(mock_filesystem, "etc"), exist_ok=True)
        
        # Create some test files
        with open(os.path.join(mock_filesystem, "bin", "busybox"), 'w') as f:
            f.write("#!/bin/sh\necho 'Hello World'")
        
        with open(os.path.join(mock_filesystem, "etc", "passwd"), 'w') as f:
            f.write("root:x:0:0:root:/root:/bin/sh")
        
        # Create a test file to insert
        test_file = os.path.join(temp_dir, "new_binary")
        with open(test_file, 'w') as f:
            f.write("#!/bin/sh\necho 'New binary'")
        
        # Test file operations
        print("   📄 Original files:")
        files = modifier.list_files(mock_filesystem)
        for file_path in files:
            print(f"     - {file_path}")
        
        # Test file insertion
        result = modifier.insert_file(mock_filesystem, test_file, "/usr/bin/new_binary")
        if result['success']:
            print(f"   ✅ Inserted new file: {result['message']}")
        else:
            print(f"   ❌ Insert failed: {result['error']}")
        
        # Test file replacement
        result = modifier.replace_file(mock_filesystem, test_file, "/bin/busybox")
        if result['success']:
            print(f"   ✅ Replaced file: {result['message']}")
        else:
            print(f"   ❌ Replace failed: {result['error']}")
        
        # Test file removal
        result = modifier.remove_file(mock_filesystem, "/etc/passwd")
        if result['success']:
            print(f"   ✅ Removed file: {result['message']}")
        else:
            print(f"   ❌ Remove failed: {result['error']}")
        
        # Test filesystem validation
        print("   🔍 Validating modified filesystem:")
        validation = repacker.validate_filesystem(mock_filesystem)
        if validation['valid']:
            print(f"   ✅ Validation passed: {validation['file_count']} files")
        else:
            print(f"   ❌ Validation failed: {validation['errors']}")
        
        print()
        print("🎉 Demo completed!")
        print()
        print("Next steps:")
        print("1. Activate conda environment: conda activate ffenv")
        print("2. Install missing tools for full functionality")
        print("3. Try the complete workflow:")
        print("   firmaforge extract your_firmware.bin")
        print("   firmaforge insert extracted_dir new_file /path/to/file")
        print("   firmaforge repack extracted_dir modified_firmware.bin")
        print("4. See README.md for complete documentation")


if __name__ == '__main__':
    main()
