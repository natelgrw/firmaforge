"""
Tests for firmware repacker
"""

import pytest
import tempfile
import os
from firmaforge.repacker import FirmwareRepacker, RepackingError
from firmaforge.detector import FirmwareType


class TestFirmwareRepacker:
    """Test cases for FirmwareRepacker"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.repacker = FirmwareRepacker()
        self.temp_dir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.temp_dir, "filesystem")
        os.makedirs(self.filesystem_dir, exist_ok=True)
        
        # Create a minimal filesystem structure
        os.makedirs(os.path.join(self.filesystem_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.filesystem_dir, "etc"), exist_ok=True)
        os.makedirs(os.path.join(self.filesystem_dir, "usr"), exist_ok=True)
        
        with open(os.path.join(self.filesystem_dir, "bin", "sh"), 'w') as f:
            f.write("#!/bin/sh\necho 'Hello World'")
        os.chmod(os.path.join(self.filesystem_dir, "bin", "sh"), 0o755)
        
        with open(os.path.join(self.filesystem_dir, "etc", "passwd"), 'w') as f:
            f.write("root:x:0:0:root:/root:/bin/sh")
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_detect_filesystem_type_from_dir(self):
        """Test filesystem type detection from directory"""
        # Test with SquashFS hint
        squashfs_dir = os.path.join(self.temp_dir, "squashfs_extracted")
        os.makedirs(squashfs_dir, exist_ok=True)
        
        fs_type = self.repacker._detect_filesystem_type_from_dir(squashfs_dir)
        assert fs_type == FirmwareType.SQUASHFS
        
        # Test with JFFS2 hint
        jffs2_dir = os.path.join(self.temp_dir, "jffs2_extracted")
        os.makedirs(jffs2_dir, exist_ok=True)
        
        fs_type = self.repacker._detect_filesystem_type_from_dir(jffs2_dir)
        assert fs_type == FirmwareType.JFFS2
    
    def test_get_repacking_info_squashfs(self):
        """Test repacking info for SquashFS"""
        info = self.repacker.get_repacking_info(FirmwareType.SQUASHFS)
        
        assert info['type'] == FirmwareType.SQUASHFS
        assert info['repackable'] is True
        assert 'mksquashfs' in info['tools_required']
        assert len(info['notes']) > 0
    
    def test_get_repacking_info_unknown(self):
        """Test repacking info for unknown filesystem"""
        info = self.repacker.get_repacking_info(FirmwareType.UNKNOWN)
        
        assert info['type'] == FirmwareType.UNKNOWN
        assert info['repackable'] is False
        assert len(info['notes']) > 0
    
    def test_validate_filesystem_valid(self):
        """Test filesystem validation with valid filesystem"""
        result = self.repacker.validate_filesystem(self.filesystem_dir)
        
        assert result['valid'] is True
        assert result['file_count'] >= 2  # At least sh and passwd
        assert result['total_size'] > 0
        assert len(result['errors']) == 0
    
    def test_validate_filesystem_nonexistent(self):
        """Test filesystem validation with nonexistent directory"""
        result = self.repacker.validate_filesystem("/nonexistent/directory")
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert "does not exist" in result['errors'][0]
    
    def test_validate_filesystem_not_directory(self):
        """Test filesystem validation with file instead of directory"""
        test_file = os.path.join(self.temp_dir, "test_file")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = self.repacker.validate_filesystem(test_file)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert "not a directory" in result['errors'][0]
    
    def test_validate_filesystem_empty(self):
        """Test filesystem validation with empty directory"""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        
        result = self.repacker.validate_filesystem(empty_dir)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert "No files found" in result['errors'][0]
    
    def test_check_tool_available(self):
        """Test tool availability checking"""
        # Test with a tool that should exist (ls on Unix systems)
        assert self.repacker._check_tool_available('ls') is True
        
        # Test with a tool that shouldn't exist
        assert self.repacker._check_tool_available('nonexistent_tool_12345') is False
    
    def test_repack_firmware_nonexistent_dir(self):
        """Test repacking with nonexistent directory"""
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        result = self.repacker.repack_firmware("/nonexistent/dir", output_file)
        
        assert result['success'] is False
        assert 'error' in result
        assert "does not exist" in result['error']
    
    def test_repack_firmware_unknown_type(self):
        """Test repacking with unknown filesystem type"""
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        result = self.repacker.repack_firmware(self.filesystem_dir, output_file, FirmwareType.UNKNOWN)
        
        assert result['success'] is False
        assert 'error' in result
        assert "Cannot determine filesystem type" in result['error']
    
    def test_repack_firmware_unsupported_type(self):
        """Test repacking with unsupported filesystem type"""
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        result = self.repacker.repack_firmware(self.filesystem_dir, output_file, FirmwareType.UBIFS)
        
        assert result['success'] is False
        assert 'error' in result
        assert "not yet implemented" in result['error']
    
    def test_repack_squashfs_tool_not_available(self):
        """Test SquashFS repacking without mksquashfs tool"""
        # This test assumes mksquashfs is not available (common in test environments)
        output_file = os.path.join(self.temp_dir, "output.squashfs")
        
        result = self.repacker._repack_squashfs(self.filesystem_dir, output_file, {'success': False})
        
        # Should fail due to missing tool
        assert result['success'] is False
        assert 'error' in result
        assert "mksquashfs tool not found" in result['error']
    
    def test_repack_jffs2_tool_not_available(self):
        """Test JFFS2 repacking without mkfs.jffs2 tool"""
        output_file = os.path.join(self.temp_dir, "output.jffs2")
        
        result = self.repacker._repack_jffs2(self.filesystem_dir, output_file, {'success': False})
        
        # Should fail due to missing tool
        assert result['success'] is False
        assert 'error' in result
        assert "mkfs.jffs2 tool not found" in result['error']
    
    def test_repack_ext_tool_not_available(self):
        """Test ext filesystem repacking without tools"""
        output_file = os.path.join(self.temp_dir, "output.ext2")
        
        # Mock the tool availability check to return False
        original_check = self.repacker._check_tool_available
        self.repacker._check_tool_available = lambda x: False
        
        try:
            result = self.repacker._repack_ext(self.filesystem_dir, output_file, {'success': False})
            
            # Should fail due to missing tools
            assert result['success'] is False
            assert 'error' in result
            assert "Neither mkfs.ext2 nor tar available" in result['error']
        finally:
            # Restore original method
            self.repacker._check_tool_available = original_check
    
    def test_repack_cramfs_tool_not_available(self):
        """Test CramFS repacking without mkcramfs tool"""
        output_file = os.path.join(self.temp_dir, "output.cramfs")
        
        result = self.repacker._repack_cramfs(self.filesystem_dir, output_file, {'success': False})
        
        # Should fail due to missing tool
        assert result['success'] is False
        assert 'error' in result
        assert "mkcramfs tool not found" in result['error']
