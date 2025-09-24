#!/usr/bin/env python3
"""
FirmaForge Fuzzing Demonstration
===============================

This script demonstrates FirmaForge's fuzzing capabilities for
vulnerability discovery in firmware files and embedded systems.
"""

import os
import sys
import tempfile
from firmaforge.detector import FirmwareDetector
from firmaforge.fuzzer import FirmwareFuzzer

def main():
    print("🔧 FirmaForge Fuzzing Demonstration")
    print("=" * 40)
    
    # Initialize components
    detector = FirmwareDetector()
    fuzzer = FirmwareFuzzer()
    
    # Test firmware files
    # Try different paths depending on where the script is run from
    firmware_files = []
    for base_path in ['examples/', '../examples/']:
        for filename in ['demo_squashfs_firmware.bin', 'demo_router_firmware.bin']:
            path = base_path + filename
            if os.path.exists(path):
                firmware_files.append(path)
    
    print("\n📄 PART 1: FIRMWARE FUZZING")
    print("=" * 30)
    
    for firmware_file in firmware_files:
        if not os.path.exists(firmware_file):
            print(f"❌ {firmware_file} not found")
            continue
        
        print(f"\n🔍 Fuzzing {firmware_file}:")
        print("-" * 25)
        
        # Detect firmware type first
        detection = detector.detect_firmware_type(firmware_file)
        print(f"   Type: {detection['filesystem_type']}")
        print(f"   Size: {detection['file_size']} bytes")
        
        # Create output directory - ensure it's relative to the demos directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "test_pipeline_results", f"fuzz_output_{firmware_file.replace('.bin', '').replace('../examples/', '').replace('examples/', '')}")
        
        # Test different fuzzing types
        fuzz_types = ['random', 'bitflip', 'magic', 'boundary']
        
        for fuzz_type in fuzz_types:
            print(f"\n   🎯 {fuzz_type.upper()} fuzzing (10 iterations):")
            
            try:
                result = fuzzer.fuzz_firmware_file(
                    firmware_file, 
                    f"{output_dir}_{fuzz_type}", 
                    fuzz_type, 
                    10
                )
                
                if result['success']:
                    print(f"     ✅ Generated: {len(result['fuzzed_files'])} files")
                    print(f"     🚨 Crashes: {len(result['crashes'])}")
                    print(f"     🔍 Unique: {result['unique_crashes']}")
                    
                    # Show sample crashes
                    if result['crashes']:
                        print("     Sample crashes:")
                        for crash in result['crashes'][:3]:
                            print(f"       - {crash['crash_type']}: {os.path.basename(crash['file_path'])}")
                else:
                    print(f"     ❌ Failed: {result['error']}")
                    
            except Exception as e:
                print(f"     ❌ Error: {str(e)}")
    
    print("\n📁 PART 2: FILESYSTEM FUZZING")
    print("=" * 30)
    
    # Try different paths for filesystem directory
    filesystem_paths = ['demo_firmware_fs', '../demos/demo_firmware_fs']
    filesystem_dir = None
    for path in filesystem_paths:
        if os.path.exists(path):
            filesystem_dir = path
            break
    
    if filesystem_dir:
        print(f"🔍 Fuzzing filesystem: {filesystem_dir}")
        
        # Test filesystem fuzzing
        try:
            # Ensure filesystem fuzzing output goes to demos directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            fs_output_dir = os.path.join(script_dir, "test_pipeline_results", "fuzz_output_filesystem")
            
            result = fuzzer.fuzz_filesystem(
                filesystem_dir,
                fs_output_dir,
                "file_content",
                20
            )
            
            if result['success']:
                print(f"   ✅ Generated: {len(result['fuzzed_files'])} fuzzed filesystems")
                print(f"   🚨 Crashes: {len(result['crashes'])}")
                
                # Show sample crashes
                if result['crashes']:
                    print("   Sample filesystem crashes:")
                    for crash in result['crashes'][:3]:
                        print(f"     - {os.path.basename(crash['fs_dir'])}: {', '.join(crash['issues'])}")
            else:
                print(f"   ❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    else:
        print(f"❌ Filesystem directory not found: {filesystem_dir}")
    
    print("\n📊 PART 3: FUZZING STATISTICS")
    print("=" * 30)
    
    stats = fuzzer.get_fuzzing_stats()
    print(f"   Total fuzz operations: {stats['total_fuzz_count']}")
    print(f"   Crashes found: {stats['crashes_found']}")
    print(f"   Unique crashes: {stats['unique_crashes']}")
    print(f"   Crash rate: {stats['crash_rate']:.2%}")
    
    print("\n🎯 PART 4: FUZZING CAPABILITIES SUMMARY")
    print("=" * 30)
    
    print("FirmaForge fuzzing supports:")
    print("  ✅ Random byte mutation")
    print("  ✅ Bit flipping attacks")
    print("  ✅ Magic number fuzzing")
    print("  ✅ Boundary value testing")
    print("  ✅ Filesystem content fuzzing")
    print("  ✅ Crash detection and analysis")
    print("  ✅ Unique crash identification")
    print("  ✅ Statistical reporting")
    
    print("\n🎉 FUZZING DEMONSTRATION COMPLETE!")
    print("=" * 40)
    print("This shows FirmaForge can:")
    print("  ✅ Fuzz firmware files for vulnerabilities")
    print("  ✅ Test embedded filesystems")
    print("  ✅ Detect crashes and anomalies")
    print("  ✅ Generate security test cases")
    print("  ✅ Provide detailed crash analysis")
    print("")
    print("Perfect for security research and vulnerability discovery!")

if __name__ == '__main__':
    main()
