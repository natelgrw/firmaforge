"""
Firmware fuzzing module for FirmaForge
=====================================

This module provides basic fuzzing capabilities for firmware files
and embedded Linux filesystems, useful for vulnerability discovery
and security testing.
"""

import os
import random
import string
import struct
import hashlib
from typing import Dict, Any, List, Optional
from .detector import FirmwareType, FirmwareDetector
from .modifier import FirmwareModifier


class FuzzingError(Exception):
    """Raised when fuzzing operations fail"""
    pass


class FirmwareFuzzer:
    """Handles fuzzing of firmware files and filesystems"""
    
    def __init__(self):
        self.detector = FirmwareDetector()
        self.modifier = FirmwareModifier()
        self.fuzz_count = 0
        self.crashes_found = 0
        self.unique_crashes = set()
    
    def fuzz_firmware_file(self, firmware_path: str, output_dir: str, 
                          fuzz_type: str = 'random', iterations: int = 100) -> Dict[str, Any]:
        """
        Fuzz a firmware file with various techniques
        
        Args:
            firmware_path: Path to original firmware file
            output_dir: Directory to save fuzzed files
            fuzz_type: Type of fuzzing ('random', 'bitflip', 'magic', 'boundary')
            iterations: Number of fuzzing iterations
            
        Returns:
            Dictionary with fuzzing results
        """
        result = {
            'success': False,
            'fuzz_type': fuzz_type,
            'iterations': iterations,
            'fuzzed_files': [],
            'crashes': [],
            'unique_crashes': 0,
            'error': None
        }
        
        try:
            if not os.path.exists(firmware_path):
                raise FuzzingError(f"Firmware file does not exist: {firmware_path}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Read original firmware
            with open(firmware_path, 'rb') as f:
                original_data = f.read()
            
            print(f"🔍 Fuzzing {firmware_path} with {fuzz_type} fuzzing...")
            print(f"   Original size: {len(original_data)} bytes")
            print(f"   Iterations: {iterations}")
            
            # Perform fuzzing
            for i in range(iterations):
                fuzzed_data = self._apply_fuzzing(original_data, fuzz_type, i)
                
                # Save fuzzed file
                fuzzed_filename = f"fuzzed_{fuzz_type}_{i:04d}.bin"
                fuzzed_path = os.path.join(output_dir, fuzzed_filename)
                
                with open(fuzzed_path, 'wb') as f:
                    f.write(fuzzed_data)
                
                result['fuzzed_files'].append(fuzzed_path)
                
                # Analyze fuzzed file
                analysis = self._analyze_fuzzed_file(fuzzed_path, fuzzed_data)
                if analysis['crashed']:
                    result['crashes'].append(analysis)
                    self.crashes_found += 1
                
                # Progress update
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i + 1}/{iterations} (crashes: {self.crashes_found})")
            
            # Calculate unique crashes
            for crash in result['crashes']:
                crash_hash = crash.get('crash_hash', '')
                if crash_hash:
                    self.unique_crashes.add(crash_hash)
            
            result['unique_crashes'] = len(self.unique_crashes)
            result['success'] = True
            
            print(f"✅ Fuzzing complete!")
            print(f"   Fuzzed files: {len(result['fuzzed_files'])}")
            print(f"   Crashes found: {len(result['crashes'])}")
            print(f"   Unique crashes: {result['unique_crashes']}")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def fuzz_filesystem(self, filesystem_dir: str, output_dir: str,
                       fuzz_type: str = 'file_content', iterations: int = 50) -> Dict[str, Any]:
        """
        Fuzz files in an extracted filesystem
        
        Args:
            filesystem_dir: Path to extracted filesystem
            output_dir: Directory to save fuzzed filesystem
            fuzz_type: Type of fuzzing ('file_content', 'permissions', 'names')
            iterations: Number of fuzzing iterations
            
        Returns:
            Dictionary with fuzzing results
        """
        result = {
            'success': False,
            'fuzz_type': fuzz_type,
            'iterations': iterations,
            'fuzzed_files': [],
            'crashes': [],
            'error': None
        }
        
        try:
            if not os.path.exists(filesystem_dir):
                raise FuzzingError(f"Filesystem directory does not exist: {filesystem_dir}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Get all files in filesystem
            files = self.modifier.list_files(filesystem_dir)
            print(f"🔍 Fuzzing filesystem with {len(files)} files...")
            
            for i in range(iterations):
                # Create fuzzed filesystem copy
                fuzzed_fs_dir = os.path.join(output_dir, f"fuzzed_fs_{i:04d}")
                self._copy_filesystem(filesystem_dir, fuzzed_fs_dir)
                
                # Apply fuzzing to random files
                fuzzed_files = self._fuzz_filesystem_files(fuzzed_fs_dir, files, fuzz_type)
                result['fuzzed_files'].extend(fuzzed_files)
                
                # Analyze fuzzed filesystem
                analysis = self._analyze_fuzzed_filesystem(fuzzed_fs_dir)
                if analysis['crashed']:
                    result['crashes'].append(analysis)
                
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i + 1}/{iterations}")
            
            result['success'] = True
            print(f"✅ Filesystem fuzzing complete!")
            print(f"   Fuzzed filesystems: {iterations}")
            print(f"   Crashes found: {len(result['crashes'])}")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _apply_fuzzing(self, data: bytes, fuzz_type: str, iteration: int) -> bytes:
        """Apply specific fuzzing technique to data"""
        fuzzed_data = bytearray(data)
        
        if fuzz_type == 'random':
            # Random byte changes
            num_changes = random.randint(1, min(10, len(data) // 100))
            for _ in range(num_changes):
                pos = random.randint(0, len(fuzzed_data) - 1)
                fuzzed_data[pos] = random.randint(0, 255)
        
        elif fuzz_type == 'bitflip':
            # Bit flipping
            num_flips = random.randint(1, min(5, len(data) // 200))
            for _ in range(num_flips):
                pos = random.randint(0, len(fuzzed_data) - 1)
                bit = random.randint(0, 7)
                fuzzed_data[pos] ^= (1 << bit)
        
        elif fuzz_type == 'magic':
            # Magic number fuzzing
            if len(fuzzed_data) >= 4:
                # Fuzz first 4 bytes (common magic number location)
                for i in range(4):
                    fuzzed_data[i] = random.randint(0, 255)
        
        elif fuzz_type == 'boundary':
            # Boundary value fuzzing
            if len(fuzzed_data) > 0:
                # Fuzz with boundary values
                boundary_values = [0x00, 0xFF, 0x7F, 0x80, 0x01, 0xFE]
                for i in range(min(10, len(fuzzed_data))):
                    fuzzed_data[i] = random.choice(boundary_values)
        
        return bytes(fuzzed_data)
    
    def _fuzz_filesystem_files(self, fs_dir: str, files: List[str], fuzz_type: str) -> List[str]:
        """Fuzz files in filesystem"""
        fuzzed_files = []
        
        # Select random files to fuzz
        files_to_fuzz = random.sample(files, min(3, len(files)))
        
        for file_path in files_to_fuzz:
            full_path = os.path.join(fs_dir, file_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                try:
                    # Read original file
                    with open(full_path, 'rb') as f:
                        original_data = f.read()
                    
                    # Apply fuzzing
                    fuzzed_data = self._apply_fuzzing(original_data, fuzz_type, 0)
                    
                    # Write fuzzed file
                    with open(full_path, 'wb') as f:
                        f.write(fuzzed_data)
                    
                    fuzzed_files.append(full_path)
                    
                except Exception:
                    # Skip files that can't be fuzzed
                    pass
        
        return fuzzed_files
    
    def _analyze_fuzzed_file(self, file_path: str, data: bytes) -> Dict[str, Any]:
        """Analyze a fuzzed file for potential crashes"""
        analysis = {
            'file_path': file_path,
            'crashed': False,
            'crash_type': None,
            'crash_hash': None,
            'file_size': len(data)
        }
        
        try:
            # Check for common crash indicators
            if len(data) == 0:
                analysis['crashed'] = True
                analysis['crash_type'] = 'empty_file'
            elif len(data) > 100 * 1024 * 1024:  # 100MB
                analysis['crashed'] = True
                analysis['crash_type'] = 'oversized_file'
            elif b'\x00' * 100 in data:
                analysis['crashed'] = True
                analysis['crash_type'] = 'null_overflow'
            
            # Generate crash hash for uniqueness
            if analysis['crashed']:
                crash_signature = f"{analysis['crash_type']}_{len(data)}_{data[:10].hex()}"
                analysis['crash_hash'] = hashlib.md5(crash_signature.encode()).hexdigest()[:8]
            
        except Exception:
            analysis['crashed'] = True
            analysis['crash_type'] = 'analysis_error'
        
        return analysis
    
    def _analyze_fuzzed_filesystem(self, fs_dir: str) -> Dict[str, Any]:
        """Analyze a fuzzed filesystem for issues"""
        analysis = {
            'fs_dir': fs_dir,
            'crashed': False,
            'issues': [],
            'file_count': 0
        }
        
        try:
            # Count files
            files = self.modifier.list_files(fs_dir)
            analysis['file_count'] = len(files)
            
            # Check for filesystem corruption
            if len(files) == 0:
                analysis['crashed'] = True
                analysis['issues'].append('empty_filesystem')
            
            # Check for oversized files
            for file_path in files:
                full_path = os.path.join(fs_dir, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    if size > 10 * 1024 * 1024:  # 10MB
                        analysis['crashed'] = True
                        analysis['issues'].append(f'oversized_file: {file_path}')
            
        except Exception as e:
            analysis['crashed'] = True
            analysis['issues'].append(f'analysis_error: {str(e)}')
        
        return analysis
    
    def _copy_filesystem(self, src_dir: str, dst_dir: str):
        """Copy filesystem directory"""
        import shutil
        shutil.copytree(src_dir, dst_dir)
    
    def get_fuzzing_stats(self) -> Dict[str, Any]:
        """Get fuzzing statistics"""
        return {
            'total_fuzz_count': self.fuzz_count,
            'crashes_found': self.crashes_found,
            'unique_crashes': len(self.unique_crashes),
            'crash_rate': self.crashes_found / max(1, self.fuzz_count)
        }
