"""
Tests for firmware modifier
"""

import pytest
import tempfile
import os
from firmaforge.modifier import FirmwareModifier, FileModificationError


class TestFirmwareModifier:
    """Test cases for FirmwareModifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.modifier = FirmwareModifier()
        self.temp_dir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.temp_dir, "filesystem")
        os.makedirs(self.filesystem_dir, exist_ok=True)
        
        # Create some test files and directories
        os.makedirs(os.path.join(self.filesystem_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.filesystem_dir, "etc"), exist_ok=True)
        
        with open(os.path.join(self.filesystem_dir, "bin", "busybox"), 'w') as f:
            f.write("#!/bin/sh\necho 'Hello World'")
        os.chmod(os.path.join(self.filesystem_dir, "bin", "busybox"), 0o755)
        
        with open(os.path.join(self.filesystem_dir, "etc", "passwd"), 'w') as f:
            f.write("root:x:0:0:root:/root:/bin/sh")
        
        with open(os.path.join(self.temp_dir, "new_binary"), 'w') as f:
            f.write("#!/bin/sh\necho 'Modified binary'")
        os.chmod(os.path.join(self.temp_dir, "new_binary"), 0o755)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_insert_file(self):
        """Test file insertion"""
        source_file = os.path.join(self.temp_dir, "new_binary")
        target_path = "/usr/bin/new_binary"
        
        result = self.modifier.insert_file(self.filesystem_dir, source_file, target_path)
        
        assert result['success'] is True
        assert result['operation'] == 'insert'
        assert result['source_file'] == source_file
        assert result['target_path'] == target_path
        
        # Check if file was actually inserted
        target_full_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        assert os.path.exists(target_full_path)
        
        # Check if permissions were preserved
        source_stat = os.stat(source_file)
        target_stat = os.stat(target_full_path)
        assert source_stat.st_mode == target_stat.st_mode
    
    def test_insert_file_nonexistent_source(self):
        """Test file insertion with nonexistent source"""
        source_file = "/nonexistent/file"
        target_path = "/usr/bin/test"
        
        result = self.modifier.insert_file(self.filesystem_dir, source_file, target_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert "does not exist" in result['error']
    
    def test_remove_file(self):
        """Test file removal"""
        target_path = "/bin/busybox"
        
        result = self.modifier.remove_file(self.filesystem_dir, target_path)
        
        assert result['success'] is True
        assert result['operation'] == 'remove'
        assert result['target_path'] == target_path
        
        # Check if file was actually removed
        target_full_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        assert not os.path.exists(target_full_path)
    
    def test_remove_directory(self):
        """Test directory removal"""
        target_path = "/etc"
        
        result = self.modifier.remove_file(self.filesystem_dir, target_path)
        
        assert result['success'] is True
        assert result['operation'] == 'remove'
        
        # Check if directory was actually removed
        target_full_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        assert not os.path.exists(target_full_path)
    
    def test_remove_nonexistent_file(self):
        """Test removal of nonexistent file"""
        target_path = "/nonexistent/file"
        
        result = self.modifier.remove_file(self.filesystem_dir, target_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert "does not exist" in result['error']
    
    def test_replace_file(self):
        """Test file replacement"""
        source_file = os.path.join(self.temp_dir, "new_binary")
        target_path = "/bin/busybox"
        
        # Get original file info
        original_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        original_size = os.path.getsize(original_path)
        original_permissions = os.stat(original_path).st_mode
        
        result = self.modifier.replace_file(self.filesystem_dir, source_file, target_path)
        
        assert result['success'] is True
        assert result['operation'] == 'replace'
        assert result['source_file'] == source_file
        assert result['target_path'] == target_path
        
        # Check if file was actually replaced
        target_full_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        assert os.path.exists(target_full_path)
        
        # Check if content changed
        new_size = os.path.getsize(target_full_path)
        assert new_size != original_size
        
        # Check if permissions were preserved
        new_permissions = os.stat(target_full_path).st_mode
        assert new_permissions == original_permissions
    
    def test_replace_nonexistent_target(self):
        """Test replacement of nonexistent target"""
        source_file = os.path.join(self.temp_dir, "new_binary")
        target_path = "/nonexistent/file"
        
        result = self.modifier.replace_file(self.filesystem_dir, source_file, target_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert "does not exist" in result['error']
    
    def test_list_files(self):
        """Test file listing"""
        files = self.modifier.list_files(self.filesystem_dir)
        
        assert len(files) >= 2  # At least busybox and passwd
        assert "bin/busybox" in files
        assert "etc/passwd" in files
    
    def test_list_files_with_pattern(self):
        """Test file listing with pattern"""
        # Test with wildcard pattern
        files = self.modifier.list_files(self.filesystem_dir, "*.sh")
        assert len(files) == 0  # No .sh files in our test setup
        
        # Test with directory pattern
        files = self.modifier.list_files(self.filesystem_dir, "bin/*")
        assert "bin/busybox" in files
        assert "etc/passwd" not in files
    
    def test_get_file_info(self):
        """Test file information retrieval"""
        target_path = "/bin/busybox"
        
        result = self.modifier.get_file_info(self.filesystem_dir, target_path)
        
        assert result['success'] is True
        assert result['target_path'] == target_path
        assert result['exists'] is True
        assert result['is_file'] is True
        assert result['is_directory'] is False
        assert result['size'] > 0
        assert result['is_executable'] is True
        assert result['is_readable'] is True
    
    def test_get_file_info_nonexistent(self):
        """Test file information for nonexistent file"""
        target_path = "/nonexistent/file"
        
        result = self.modifier.get_file_info(self.filesystem_dir, target_path)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_create_directory(self):
        """Test directory creation"""
        target_path = "/usr/local/bin"
        
        result = self.modifier.create_directory(self.filesystem_dir, target_path)
        
        assert result['success'] is True
        assert result['operation'] == 'create_directory'
        assert result['target_path'] == target_path
        
        # Check if directory was actually created
        target_full_path = os.path.join(self.filesystem_dir, target_path.lstrip('/'))
        assert os.path.exists(target_full_path)
        assert os.path.isdir(target_full_path)
    
    def test_batch_operations(self):
        """Test batch operations"""
        operations = [
            {
                'type': 'create_directory',
                'target_path': '/usr/local/bin'
            },
            {
                'type': 'insert',
                'source_file': os.path.join(self.temp_dir, "new_binary"),
                'target_path': '/usr/local/bin/new_binary'
            },
            {
                'type': 'remove',
                'target_path': '/etc/passwd'
            }
        ]
        
        result = self.modifier.batch_operations(self.filesystem_dir, operations)
        
        assert result['success'] is True
        assert result['total_operations'] == 3
        assert result['successful_operations'] == 3
        assert result['failed_operations'] == 0
        
        # Check if operations were actually performed
        assert os.path.exists(os.path.join(self.filesystem_dir, "usr/local/bin/new_binary"))
        assert not os.path.exists(os.path.join(self.filesystem_dir, "etc/passwd"))
    
    def test_batch_operations_with_failure(self):
        """Test batch operations with some failures"""
        operations = [
            {
                'type': 'insert',
                'source_file': os.path.join(self.temp_dir, "new_binary"),
                'target_path': '/usr/bin/valid'
            },
            {
                'type': 'insert',
                'source_file': '/nonexistent/file',
                'target_path': '/usr/bin/invalid'
            }
        ]
        
        result = self.modifier.batch_operations(self.filesystem_dir, operations)
        
        assert result['success'] is False  # Should fail due to one failed operation
        assert result['total_operations'] == 2
        assert result['successful_operations'] == 1
        assert result['failed_operations'] == 1
        
        # Check that successful operation was performed
        assert os.path.exists(os.path.join(self.filesystem_dir, "usr/bin/valid"))
        assert not os.path.exists(os.path.join(self.filesystem_dir, "usr/bin/invalid"))
