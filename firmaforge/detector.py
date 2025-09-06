"""
Firmware format detection module
"""

import struct
from typing import Optional, Dict, Any
from enum import Enum

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class FirmwareType(Enum):
    """Supported firmware types"""
    SQUASHFS = "squashfs"
    JFFS2 = "jffs2"
    EXT2 = "ext2"
    EXT3 = "ext3"
    EXT4 = "ext4"
    CRAMFS = "cramfs"
    UBIFS = "ubifs"
    UNKNOWN = "unknown"


class FirmwareDetector:
    """Detects firmware format and filesystem type"""
    
    # Magic signatures for different filesystem types
    SIGNATURES = {
        b'hsqs': FirmwareType.SQUASHFS,  # SquashFS magic
        b'\x85\x19\x03\x20': FirmwareType.JFFS2,  # JFFS2 magic
        b'\x53\xef': FirmwareType.EXT2,  # ext2/3/4 magic
        b'Compressed ROMFS': FirmwareType.CRAMFS,  # CramFS magic
        b'UBI#': FirmwareType.UBIFS,  # UBIFS magic
    }
    
    def __init__(self):
        if MAGIC_AVAILABLE:
            self.mime_detector = magic.Magic(mime=True)
        else:
            self.mime_detector = None
    
    def detect_firmware_type(self, firmware_path: str) -> Dict[str, Any]:
        """
        Detect the firmware format and filesystem type
        
        Args:
            firmware_path: Path to the firmware file
            
        Returns:
            Dictionary containing detection results
        """
        result = {
            'firmware_type': FirmwareType.UNKNOWN,
            'filesystem_type': FirmwareType.UNKNOWN,
            'mime_type': None,
            'file_size': 0,
            'signatures_found': [],
            'confidence': 0.0
        }
        
        try:
            with open(firmware_path, 'rb') as f:
                # Get file size
                f.seek(0, 2)
                result['file_size'] = f.tell()
                f.seek(0)
                
                # Read first 1MB for analysis
                header_data = f.read(1024 * 1024)
                
                # Get MIME type
                if self.mime_detector:
                    result['mime_type'] = self.mime_detector.from_file(firmware_path)
                else:
                    result['mime_type'] = 'application/octet-stream'
                
                # Check for filesystem signatures
                signatures_found = self._find_signatures(header_data)
                result['signatures_found'] = signatures_found
                
                # Determine firmware type based on signatures
                if signatures_found:
                    # Use the first (most likely) signature
                    result['filesystem_type'] = signatures_found[0]['type']
                    result['confidence'] = signatures_found[0]['confidence']
                
                # Check for common firmware containers
                firmware_type = self._detect_firmware_container(header_data)
                result['firmware_type'] = firmware_type
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _find_signatures(self, data: bytes) -> list:
        """Find filesystem signatures in the data"""
        signatures_found = []
        
        for signature, fs_type in self.SIGNATURES.items():
            offset = data.find(signature)
            if offset != -1:
                # Calculate confidence based on position (earlier = higher confidence)
                confidence = max(0.1, 1.0 - (offset / len(data)))
                signatures_found.append({
                    'type': fs_type,
                    'offset': offset,
                    'signature': signature.hex(),
                    'confidence': confidence
                })
        
        # Sort by confidence (highest first)
        signatures_found.sort(key=lambda x: x['confidence'], reverse=True)
        return signatures_found
    
    def _detect_firmware_container(self, data: bytes) -> FirmwareType:
        """Detect if this is a firmware container format"""
        # Check for common firmware container formats
        
        # U-Boot UImage
        if data.startswith(b'\x27\x05\x19\x56'):
            return FirmwareType.UNKNOWN  # U-Boot image, need to extract kernel
        
        # TRX header (Linksys, etc.)
        if data.startswith(b'HDR0'):
            return FirmwareType.UNKNOWN  # TRX format
        
        # Check for embedded filesystems
        signatures = self._find_signatures(data)
        if signatures:
            return signatures[0]['type']
        
        return FirmwareType.UNKNOWN
    
    def get_filesystem_info(self, firmware_path: str, filesystem_type: FirmwareType) -> Dict[str, Any]:
        """
        Get detailed information about the filesystem
        
        Args:
            firmware_path: Path to the firmware file
            filesystem_type: Detected filesystem type
            
        Returns:
            Dictionary with filesystem-specific information
        """
        info = {
            'type': filesystem_type,
            'extractable': False,
            'tools_required': [],
            'notes': []
        }
        
        if filesystem_type == FirmwareType.SQUASHFS:
            info['extractable'] = True
            info['tools_required'] = ['unsquashfs']
            info['notes'].append('SquashFS filesystem detected')
            
        elif filesystem_type == FirmwareType.JFFS2:
            info['extractable'] = True
            info['tools_required'] = ['jefferson']
            info['notes'].append('JFFS2 filesystem detected')
            
        elif filesystem_type in [FirmwareType.EXT2, FirmwareType.EXT3, FirmwareType.EXT4]:
            info['extractable'] = True
            info['tools_required'] = ['7z', 'debugfs']
            info['notes'].append('ext2/3/4 filesystem detected')
            
        elif filesystem_type == FirmwareType.CRAMFS:
            info['extractable'] = True
            info['tools_required'] = ['cramfsck']
            info['notes'].append('CramFS filesystem detected')
            
        elif filesystem_type == FirmwareType.UBIFS:
            info['extractable'] = True
            info['tools_required'] = ['ubireader']
            info['notes'].append('UBIFS filesystem detected')
            
        else:
            info['notes'].append('Unknown or unsupported filesystem type')
        
        return info
