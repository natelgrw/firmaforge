"""
Tests for firmware extractor
"""

import pytest
import tempfile
import os
import subprocess
from firmaforge.extractor import FirmwareExtractor, ExtractionError
from firmaforge.detector import FirmwareType


class TestFirmwareExtractor:
    """Test cases for FirmwareExtractor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = FirmwareExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_tool_availability_check(self):
        """Test tool availability checking"""
        # Test with a tool that should exist (ls on Unix systems)
        assert self.extractor._check_tool_available('ls') is True
        
        # Test with a tool that shouldn't exist
        assert self.extractor._check_tool_available('nonexistent_tool_12345') is False
    
    def test_list_extracted_files(self):
        """Test listing extracted files"""
        # Create a test directory structure
        test_dir = os.path.join(self.temp_dir, "test_extraction")
        os.makedirs(test_dir, exist_ok=True)
        
        # Create some test files
        os.makedirs(os.path.join(test_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(test_dir, "etc"), exist_ok=True)
        
        with open(os.path.join(test_dir, "bin", "busybox"), 'w') as f:
            f.write("test")
        
        with open(os.path.join(test_dir, "etc", "passwd"), 'w') as f:
            f.write("test")
        
        with open(os.path.join(test_dir, "README"), 'w') as f:
            f.write("test")
        
        # List files
        files = self.extractor._list_extracted_files(test_dir)
        
        # Should find all files
        assert len(files) == 3
        assert "bin/busybox" in files
        assert "etc/passwd" in files
        assert "README" in files
    
    def test_extract_unknown_filesystem(self):
        """Test extraction of unknown filesystem"""
        # Create a mock firmware file
        firmware_file = os.path.join(self.temp_dir, "unknown.bin")
        with open(firmware_file, 'wb') as f:
            f.write(b'\x00' * 100)
        
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.extractor.extract_firmware(firmware_file, output_dir)
        
        assert result['success'] is False
        assert 'error' in result
        assert "Unknown or unsupported filesystem type" in result['error']
    
    def test_extract_nonexistent_file(self):
        """Test extraction of nonexistent file"""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.extractor.extract_firmware("/nonexistent/file.bin", output_dir)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_cleanup(self):
        """Test cleanup functionality"""
        # This is a simple test to ensure cleanup doesn't crash
        self.extractor.cleanup()
        # If we get here without exception, the test passes
