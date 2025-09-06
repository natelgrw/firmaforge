"""
Tests for firmware detector
"""

import pytest
import tempfile
import os
from firmaforge.detector import FirmwareDetector, FirmwareType


class TestFirmwareDetector:
    """Test cases for FirmwareDetector"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = FirmwareDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_squashfs_detection(self):
        """Test SquashFS detection"""
        # Create a mock SquashFS file with magic signature
        squashfs_file = os.path.join(self.temp_dir, "test.squashfs")
        with open(squashfs_file, 'wb') as f:
            f.write(b'hsqs' + b'\x00' * 100)  # SquashFS magic + padding
        
        result = self.detector.detect_firmware_type(squashfs_file)
        
        assert result['filesystem_type'] == FirmwareType.SQUASHFS
        assert len(result['signatures_found']) > 0
        assert result['signatures_found'][0]['type'] == FirmwareType.SQUASHFS
    
    def test_jffs2_detection(self):
        """Test JFFS2 detection"""
        jffs2_file = os.path.join(self.temp_dir, "test.jffs2")
        with open(jffs2_file, 'wb') as f:
            f.write(b'\x85\x19\x03\x20' + b'\x00' * 100)  # JFFS2 magic + padding
        
        result = self.detector.detect_firmware_type(jffs2_file)
        
        assert result['filesystem_type'] == FirmwareType.JFFS2
        assert len(result['signatures_found']) > 0
        assert result['signatures_found'][0]['type'] == FirmwareType.JFFS2
    
    def test_ext2_detection(self):
        """Test ext2 detection"""
        ext2_file = os.path.join(self.temp_dir, "test.ext2")
        with open(ext2_file, 'wb') as f:
            f.write(b'\x53\xef' + b'\x00' * 100)  # ext2 magic + padding
        
        result = self.detector.detect_firmware_type(ext2_file)
        
        assert result['filesystem_type'] == FirmwareType.EXT2
        assert len(result['signatures_found']) > 0
        assert result['signatures_found'][0]['type'] == FirmwareType.EXT2
    
    def test_unknown_detection(self):
        """Test unknown filesystem detection"""
        unknown_file = os.path.join(self.temp_dir, "test.unknown")
        with open(unknown_file, 'wb') as f:
            f.write(b'\x00' * 100)  # No known magic signatures
        
        result = self.detector.detect_firmware_type(unknown_file)
        
        assert result['filesystem_type'] == FirmwareType.UNKNOWN
        assert len(result['signatures_found']) == 0
    
    def test_get_filesystem_info(self):
        """Test filesystem info retrieval"""
        # Test SquashFS info
        squashfs_info = self.detector.get_filesystem_info("dummy", FirmwareType.SQUASHFS)
        assert squashfs_info['type'] == FirmwareType.SQUASHFS
        assert squashfs_info['extractable'] is True
        assert 'unsquashfs' in squashfs_info['tools_required']
        
        # Test unknown filesystem info
        unknown_info = self.detector.get_filesystem_info("dummy", FirmwareType.UNKNOWN)
        assert unknown_info['type'] == FirmwareType.UNKNOWN
        assert unknown_info['extractable'] is False
    
    def test_file_size_detection(self):
        """Test file size detection"""
        test_file = os.path.join(self.temp_dir, "test.bin")
        test_data = b'\x00' * 1024  # 1KB of data
        
        with open(test_file, 'wb') as f:
            f.write(test_data)
        
        result = self.detector.detect_firmware_type(test_file)
        assert result['file_size'] == 1024
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file"""
        result = self.detector.detect_firmware_type("/nonexistent/file.bin")
        assert 'error' in result
        assert result['filesystem_type'] == FirmwareType.UNKNOWN
