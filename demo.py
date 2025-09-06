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
        tools = ['unsquashfs', 'jefferson', '7z', 'debugfs', 'cramfsck', 'ubireader']
        for tool in tools:
            available = extractor._check_tool_available(tool)
            status = "✅" if available else "❌"
            print(f"   {status} {tool}")
        
        print()
        print("🎉 Demo completed!")
        print()
        print("Next steps:")
        print("1. Activate conda environment: conda activate ffenv")
        print("2. Install missing extraction tools")
        print("3. Try with real firmware files:")
        print("   firmaforge extract your_firmware.bin")
        print("4. Analyze firmware without extracting:")
        print("   firmaforge analyze your_firmware.bin")


if __name__ == '__main__':
    main()
