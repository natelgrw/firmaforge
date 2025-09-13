"""
Firmware builder module for creating complete firmware images
"""

import os
import struct
import subprocess
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from .detector import FirmwareType, FirmwareDetector
from .repacker import FirmwareRepacker, RepackingError


class FirmwareBuilderError(Exception):
    """Raised when firmware building fails"""
    pass


class FirmwareBuilder:
    """Handles building of complete firmware images with container support"""
    
    def __init__(self):
        self.detector = FirmwareDetector()
        self.repacker = FirmwareRepacker()
    
    def extract_firmware_metadata(self, firmware_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a firmware file
        
        Args:
            firmware_path: Path to firmware file
            
        Returns:
            Dictionary with firmware metadata
        """
        result = {
            'success': False,
            'file_size': 0,
            'container_format': 'unknown',
            'detected_type': None,
            'error': None
        }
        
        try:
            if not os.path.exists(firmware_path):
                raise FirmwareBuilderError(f"Firmware file does not exist: {firmware_path}")
            
            # Get file size
            result['file_size'] = os.path.getsize(firmware_path)
            
            # Detect filesystem type
            detection = self.detector.detect_firmware_type(firmware_path)
            result['detected_type'] = detection.get('filesystem_type', FirmwareType.UNKNOWN)
            
            # Detect container format
            container_format = self._detect_container_format(firmware_path)
            result['container_format'] = container_format
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def build_firmware(self, filesystem_path: str, output_file: str, 
                      original_firmware: Optional[str] = None,
                      filesystem_type: Optional[FirmwareType] = None,
                      preserve_headers: bool = True,
                      container_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Build a complete firmware image
        
        Args:
            filesystem_path: Path to modified filesystem directory
            output_file: Path for output firmware file
            original_firmware: Original firmware file for metadata extraction
            filesystem_type: Type of filesystem to create
            preserve_headers: Whether to preserve original headers
            container_format: Container format (raw, uboot, trx)
            
        Returns:
            Dictionary with build results
        """
        result = {
            'success': False,
            'filesystem_type': None,
            'container_format': None,
            'output_file': output_file,
            'checksums': {},
            'validation': {},
            'error': None
        }
        
        try:
            # Validate inputs
            if not os.path.exists(filesystem_path):
                raise FirmwareBuilderError(f"Filesystem directory does not exist: {filesystem_path}")
            
            # Auto-detect filesystem type if not provided
            if filesystem_type is None:
                filesystem_type = self.repacker._detect_filesystem_type_from_dir(filesystem_path)
            
            result['filesystem_type'] = filesystem_type
            
            # Auto-detect container format if not provided
            if container_format is None:
                if original_firmware and os.path.exists(original_firmware):
                    metadata = self.extract_firmware_metadata(original_firmware)
                    if metadata['success']:
                        container_format = metadata['container_format']
                    else:
                        container_format = 'raw'
                else:
                    container_format = 'raw'
            
            result['container_format'] = container_format
            
            # First, repack the filesystem
            temp_filesystem_file = tempfile.mktemp(suffix='.fs')
            try:
                repack_result = self.repacker.repack_firmware(
                    filesystem_path, 
                    temp_filesystem_file, 
                    filesystem_type
                )
                
                if not repack_result['success']:
                    raise FirmwareBuilderError(f"repacking failed: {repack_result['error']}")
                
                # Build the container
                if container_format == 'raw':
                    # For raw format, just copy the filesystem
                    shutil.copy2(temp_filesystem_file, output_file)
                    result['message'] = f"Successfully built raw firmware: {output_file}"
                
                elif container_format == 'trx':
                    container_result = self._build_trx_container(
                        temp_filesystem_file, 
                        output_file, 
                        original_firmware
                    )
                    if not container_result['success']:
                        raise FirmwareBuilderError(f"TRX container build failed: {container_result['error']}")
                    result['message'] = container_result['message']
                
                elif container_format == 'uboot':
                    container_result = self._build_uboot_container(
                        temp_filesystem_file, 
                        output_file, 
                        original_firmware
                    )
                    if not container_result['success']:
                        raise FirmwareBuilderError(f"U-Boot container build failed: {container_result['error']}")
                    result['message'] = container_result['message']
                
                else:
                    raise FirmwareBuilderError(f"Unsupported container format: {container_format}")
                
                # Calculate checksums
                result['checksums'] = self._calculate_checksums(output_file)
                
                # Validate the result
                result['validation'] = self._validate_built_firmware(output_file, filesystem_type)
                
                result['success'] = True
                
            finally:
                # Clean up temporary filesystem file
                if os.path.exists(temp_filesystem_file):
                    os.unlink(temp_filesystem_file)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_supported_containers(self) -> List[Dict[str, Any]]:
        """
        Get list of supported container formats
        
        Returns:
            List of container format information
        """
        containers = [
            {
                'format': 'raw',
                'description': 'Raw filesystem image (no container)',
                'supported': True,
                'tools_required': []
            },
            {
                'format': 'trx',
                'description': 'TRX container format (Linksys, etc.)',
                'supported': True,
                'tools_required': []
            },
            {
                'format': 'uboot',
                'description': 'U-Boot image format',
                'supported': self._check_tool_available('mkimage'),
                'tools_required': ['mkimage']
            }
        ]
        
        return containers
    
    def _detect_container_format(self, firmware_path: str) -> str:
        """Detect container format from firmware file"""
        try:
            with open(firmware_path, 'rb') as f:
                header = f.read(32)
                
                # Check for TRX header
                if header.startswith(b'HDR0'):
                    return 'trx'
                
                # Check for U-Boot image
                if header.startswith(b'\x27\x05\x19\x56'):
                    return 'uboot'
                
                # Default to raw
                return 'raw'
                
        except Exception:
            return 'unknown'
    
    def _build_trx_container(self, filesystem_file: str, output_file: str, 
                           original_firmware: Optional[str] = None) -> Dict[str, Any]:
        """Build TRX container"""
        result = {
            'success': False,
            'container_format': 'trx',
            'error': None
        }
        
        try:
            filesystem_size = os.path.getsize(filesystem_file)
            
            # Create TRX header
            trx_header = self._create_trx_header(filesystem_size)
            
            # Write output file
            with open(output_file, 'wb') as out_f:
                out_f.write(trx_header)
                
                # Append filesystem data
                with open(filesystem_file, 'rb') as fs_f:
                    shutil.copyfileobj(fs_f, out_f)
            
            result['success'] = True
            result['message'] = f"Successfully built TRX container: {output_file}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _build_uboot_container(self, filesystem_file: str, output_file: str,
                             original_firmware: Optional[str] = None) -> Dict[str, Any]:
        """Build U-Boot container"""
        result = {
            'success': False,
            'container_format': 'uboot',
            'error': None
        }
        
        try:
            # Check if mkimage is available
            if not self._check_tool_available('mkimage'):
                raise FirmwareBuilderError("mkimage tool not found. Install u-boot-tools.")
            
            # Build U-Boot image
            cmd = [
                'mkimage',
                '-A', 'mips',  # Architecture
                '-O', 'linux',  # OS
                '-T', 'filesystem',  # Type
                '-C', 'none',  # Compression
                '-a', '0x80000000',  # Load address
                '-e', '0x80000000',  # Entry point
                '-n', 'Firmware',  # Name
                '-d', filesystem_file,  # Data file
                output_file
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise FirmwareBuilderError(f"mkimage failed: {process.stderr}")
            
            result['success'] = True
            result['message'] = f"Successfully built U-Boot image: {output_file}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _create_trx_header(self, filesystem_size: int) -> bytes:
        """Create TRX header"""
        # TRX header structure (32 bytes)
        # Magic: 4 bytes (HDR0)
        # Length: 4 bytes (total size)
        # CRC32: 4 bytes
        # Flags: 4 bytes
        # Version: 4 bytes
        # Reserved: 12 bytes
        
        magic = b'HDR0'
        length = struct.pack('<I', 32 + filesystem_size)  # Header + filesystem size
        crc32 = struct.pack('<I', 0)  # CRC32 (calculated later if needed)
        flags = struct.pack('<I', 0)  # Flags
        version = struct.pack('<I', 0)  # Version
        reserved = b'\x00' * 12  # Reserved bytes
        
        return magic + length + crc32 + flags + version + reserved
    
    def _calculate_checksums(self, file_path: str) -> Dict[str, Any]:
        """Calculate checksums for a file"""
        result = {
            'md5': None,
            'sha1': None,
            'sha256': None,
            'size': 0,
            'error': None
        }
        
        try:
            if not os.path.exists(file_path):
                result['error'] = f"File does not exist: {file_path}"
                return result
            
            result['size'] = os.path.getsize(file_path)
            
            # Calculate checksums
            md5_hash = hashlib.md5()
            sha1_hash = hashlib.sha1()
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha1_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            result['md5'] = md5_hash.hexdigest()
            result['sha1'] = sha1_hash.hexdigest()
            result['sha256'] = sha256_hash.hexdigest()
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _validate_built_firmware(self, firmware_path: str, filesystem_type: FirmwareType) -> Dict[str, Any]:
        """Validate the built firmware"""
        result = {
            'valid': False,
            'filesystem_type': filesystem_type.value,
            'error': None
        }
        
        try:
            if not os.path.exists(firmware_path):
                result['error'] = "Firmware file does not exist"
                return result
            
            # Basic validation - check file size
            file_size = os.path.getsize(firmware_path)
            if file_size == 0:
                result['error'] = "Firmware file is empty"
                return result
            
            result['valid'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a command-line tool is available"""
        try:
            subprocess.run(['which', tool_name], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
