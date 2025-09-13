"""
Tests for firmware builder
"""

import pytest
import tempfile
import os
from firmaforge.builder import FirmwareBuilder, FirmwareBuilderError
from firmaforge.detector import FirmwareType


class TestFirmwareBuilder:
    """Test cases for FirmwareBuilder"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.builder = FirmwareBuilder()
        self.temp_dir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.temp_dir, "filesystem")
        os.makedirs(self.filesystem_dir, exist_ok=True)
        
        # Create a minimal filesystem structure
        os.makedirs(os.path.join(self.filesystem_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.filesystem_dir, "etc"), exist_ok=True)
        
        with open(os.path.join(self.filesystem_dir, "bin", "sh"), 'w') as f:
            f.write("#!/bin/sh\necho 'Hello World'")
        os.chmod(os.path.join(self.filesystem_dir, "bin", "sh"), 0o755)
        
        with open(os.path.join(self.filesystem_dir, "etc", "passwd"), 'w') as f:
            f.write("root:x:0:0:root:/root:/bin/sh")
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_supported_containers(self):
        """Test getting supported container formats"""
        containers = self.builder.get_supported_containers()
        
        assert len(containers) >= 3  # raw, uboot, trx
        assert any(c['format'] == 'raw' for c in containers)
        assert any(c['format'] == 'uboot' for c in containers)
        assert any(c['format'] == 'trx' for c in containers)
        
        # Raw should always be supported
        raw_container = next(c for c in containers if c['format'] == 'raw')
        assert raw_container['supported'] is True
    
    def test_calculate_checksums(self):
        """Test checksum calculation"""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.bin")
        test_data = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_data)
        
        checksums = self.builder._calculate_checksums(test_file)
        
        assert 'md5' in checksums
        assert 'sha1' in checksums
        assert 'sha256' in checksums
        assert 'size' in checksums
        assert checksums['size'] == len(test_data)
    
    def test_calculate_checksums_nonexistent(self):
        """Test checksum calculation with nonexistent file"""
        checksums = self.builder._calculate_checksums("/nonexistent/file")
        
        assert 'error' in checksums
    
    def test_extract_firmware_metadata_nonexistent(self):
        """Test metadata extraction with nonexistent file"""
        result = self.builder.extract_firmware_metadata("/nonexistent/firmware.bin")
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_extract_firmware_metadata_valid(self):
        """Test metadata extraction with valid file"""
        # Create a mock firmware file
        firmware_file = os.path.join(self.temp_dir, "firmware.bin")
        with open(firmware_file, 'wb') as f:
            f.write(b'HDR0' + b'\x00' * 100)  # TRX header + data
        
        result = self.builder.extract_firmware_metadata(firmware_file)
        
        assert result['success'] is True
        assert result['file_size'] == 104
        assert result['container_format'] == 'trx'
    
    def test_extract_firmware_metadata_uboot(self):
        """Test metadata extraction with U-Boot image"""
        firmware_file = os.path.join(self.temp_dir, "uboot.bin")
        with open(firmware_file, 'wb') as f:
            f.write(b'\x27\x05\x19\x56' + b'\x00' * 100)  # U-Boot magic + data
        
        result = self.builder.extract_firmware_metadata(firmware_file)
        
        assert result['success'] is True
        assert result['container_format'] == 'uboot'
    
    def test_build_firmware_nonexistent_dir(self):
        """Test building firmware with nonexistent directory"""
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        result = self.builder.build_firmware("/nonexistent/dir", output_file)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_build_firmware_raw_container(self):
        """Test building firmware with raw container"""
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        result = self.builder.build_firmware(
            self.filesystem_dir, 
            output_file, 
            container_format='raw'
        )
        
        # Should fail due to missing repacking tools, but test the logic
        assert result['success'] is False
        assert 'error' in result
        assert 'repacking failed' in result['error']
    
    def test_build_firmware_trx_container(self):
        """Test building firmware with TRX container"""
        output_file = os.path.join(self.temp_dir, "output.trx")
        
        result = self.builder.build_firmware(
            self.filesystem_dir, 
            output_file, 
            container_format='trx'
        )
        
        # Should fail due to missing repacking tools, but test the logic
        assert result['success'] is False
        assert 'error' in result
        assert 'repacking failed' in result['error']
    
    def test_create_trx_header(self):
        """Test TRX header creation"""
        filesystem_size = 1024
        header = self.builder._create_trx_header(filesystem_size)
        
        assert len(header) == 32  # TRX header is 32 bytes
        assert header.startswith(b'HDR0')  # TRX magic
        assert len(header) == 32
    
    def test_check_tool_available(self):
        """Test tool availability checking"""
        # Test with a tool that should exist (ls on Unix systems)
        assert self.builder._check_tool_available('ls') is True
        
        # Test with a tool that shouldn't exist
        assert self.builder._check_tool_available('nonexistent_tool_12345') is False
    
    def test_build_trx_container(self):
        """Test TRX container building"""
        # Create a mock filesystem file
        filesystem_file = os.path.join(self.temp_dir, "filesystem.bin")
        with open(filesystem_file, 'wb') as f:
            f.write(b'test filesystem data')
        
        output_file = os.path.join(self.temp_dir, "output.trx")
        
        result = self.builder._build_trx_container(filesystem_file, output_file, None)
        
        assert result['success'] is True
        assert result['container_format'] == 'trx'
        assert os.path.exists(output_file)
        
        # Check that the output file has TRX header
        with open(output_file, 'rb') as f:
            header = f.read(32)
            assert header.startswith(b'HDR0')
    
    def test_build_uboot_container_tool_not_available(self):
        """Test U-Boot container building without mkimage tool"""
        # This test assumes mkimage is not available (common in test environments)
        filesystem_file = os.path.join(self.temp_dir, "filesystem.bin")
        with open(filesystem_file, 'wb') as f:
            f.write(b'test filesystem data')
        
        output_file = os.path.join(self.temp_dir, "output.uboot")
        
        result = self.builder._build_uboot_container(filesystem_file, output_file, None)
        
        # Should fail due to missing tool
        assert result['success'] is False
        assert 'error' in result
        assert "mkimage tool not found" in result['error']
