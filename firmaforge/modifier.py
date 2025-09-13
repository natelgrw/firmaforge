"""
File modification module for firmware filesystems
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from .detector import FirmwareType, FirmwareDetector
from .extractor import FirmwareExtractor


class FileModificationError(Exception):
    """Raised when file modification operations fail"""
    pass


class FirmwareModifier:
    """Handles file modifications in extracted firmware filesystems"""
    
    def __init__(self):
        self.detector = FirmwareDetector()
        self.extractor = FirmwareExtractor()
    
    def insert_file(self, filesystem_path: str, source_file: str, target_path: str, 
                   preserve_permissions: bool = True) -> Dict[str, Any]:
        """
        Insert a file into the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            source_file: Path to file to insert
            target_path: Destination path within filesystem
            preserve_permissions: Whether to preserve file permissions
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'operation': 'insert',
            'source_file': source_file,
            'target_path': target_path,
            'error': None
        }
        
        try:
            # Validate inputs
            if not os.path.exists(source_file):
                raise FileModificationError(f"Source file does not exist: {source_file}")
            
            if not os.path.exists(filesystem_path):
                raise FileModificationError(f"Filesystem directory does not exist: {filesystem_path}")
            
            # Create target directory if needed
            # Remove leading slash from target_path to make it relative
            relative_target_path = target_path.lstrip('/')
            target_full_path = os.path.join(filesystem_path, relative_target_path)
            target_dir = os.path.dirname(target_full_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_file, target_full_path)
            
            # Preserve permissions if requested
            if preserve_permissions:
                source_stat = os.stat(source_file)
                os.chmod(target_full_path, source_stat.st_mode)
            
            result['success'] = True
            result['message'] = f"Successfully inserted {source_file} to {target_path}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def remove_file(self, filesystem_path: str, target_path: str) -> Dict[str, Any]:
        """
        Remove a file from the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            target_path: Path to file to remove (relative to filesystem root)
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'operation': 'remove',
            'target_path': target_path,
            'error': None
        }
        
        try:
            relative_target_path = target_path.lstrip('/')
            target_full_path = os.path.join(filesystem_path, relative_target_path)
            
            if not os.path.exists(target_full_path):
                raise FileModificationError(f"Target file does not exist: {target_path}")
            
            if os.path.isfile(target_full_path):
                os.remove(target_full_path)
                result['message'] = f"Successfully removed file: {target_path}"
            elif os.path.isdir(target_full_path):
                shutil.rmtree(target_full_path)
                result['message'] = f"Successfully removed directory: {target_path}"
            else:
                raise FileModificationError(f"Unknown file type: {target_path}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def replace_file(self, filesystem_path: str, source_file: str, target_path: str,
                    preserve_permissions: bool = True) -> Dict[str, Any]:
        """
        Replace a file in the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            source_file: Path to replacement file
            target_path: Path to file to replace (relative to filesystem root)
            preserve_permissions: Whether to preserve original file permissions
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'operation': 'replace',
            'source_file': source_file,
            'target_path': target_path,
            'error': None
        }
        
        try:
            if not os.path.exists(source_file):
                raise FileModificationError(f"Source file does not exist: {source_file}")
            
            relative_target_path = target_path.lstrip('/')
            target_full_path = os.path.join(filesystem_path, relative_target_path)
            
            # Check if target exists
            if not os.path.exists(target_full_path):
                raise FileModificationError(f"Target file does not exist: {target_path}")
            
            # Preserve original permissions if requested
            original_permissions = None
            if preserve_permissions and os.path.exists(target_full_path):
                original_permissions = os.stat(target_full_path).st_mode
            
            # Remove original file
            os.remove(target_full_path)
            
            # Copy new file
            shutil.copy2(source_file, target_full_path)
            
            # Restore permissions
            if preserve_permissions and original_permissions:
                os.chmod(target_full_path, original_permissions)
            elif preserve_permissions:
                # If no original permissions, use source file permissions
                source_stat = os.stat(source_file)
                os.chmod(target_full_path, source_stat.st_mode)
            
            result['success'] = True
            result['message'] = f"Successfully replaced {target_path} with {source_file}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def list_files(self, filesystem_path: str, pattern: Optional[str] = None) -> List[str]:
        """
        List files in the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            pattern: Optional pattern to filter files (e.g., "*.bin", "/bin/*")
            
        Returns:
            List of file paths relative to filesystem root
        """
        files = []
        
        try:
            for root, dirs, filenames in os.walk(filesystem_path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, filesystem_path)
                    
                    if pattern:
                        # Simple pattern matching
                        if pattern.startswith('*'):
                            if rel_path.endswith(pattern[1:]):
                                files.append(rel_path)
                        elif pattern.endswith('*'):
                            if rel_path.startswith(pattern[:-1]):
                                files.append(rel_path)
                        elif '*' in pattern:
                            # More complex pattern matching could be added here
                            if pattern.replace('*', '') in rel_path:
                                files.append(rel_path)
                        else:
                            if pattern in rel_path:
                                files.append(rel_path)
                    else:
                        files.append(rel_path)
            
        except Exception as e:
            raise FileModificationError(f"Error listing files: {str(e)}")
        
        return sorted(files)
    
    def get_file_info(self, filesystem_path: str, target_path: str) -> Dict[str, Any]:
        """
        Get information about a file in the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            target_path: Path to file (relative to filesystem root)
            
        Returns:
            Dictionary with file information
        """
        result = {
            'success': False,
            'target_path': target_path,
            'error': None
        }
        
        try:
            relative_target_path = target_path.lstrip('/')
            target_full_path = os.path.join(filesystem_path, relative_target_path)
            
            if not os.path.exists(target_full_path):
                raise FileModificationError(f"File does not exist: {target_path}")
            
            stat_info = os.stat(target_full_path)
            
            result.update({
                'success': True,
                'exists': True,
                'size': stat_info.st_size,
                'permissions': oct(stat_info.st_mode)[-3:],
                'is_file': os.path.isfile(target_full_path),
                'is_directory': os.path.isdir(target_full_path),
                'is_executable': os.access(target_full_path, os.X_OK),
                'is_readable': os.access(target_full_path, os.R_OK),
                'is_writable': os.access(target_full_path, os.W_OK),
            })
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def create_directory(self, filesystem_path: str, target_path: str, 
                        permissions: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a directory in the filesystem
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            target_path: Path to directory to create (relative to filesystem root)
            permissions: Optional permissions (e.g., 0o755)
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'operation': 'create_directory',
            'target_path': target_path,
            'error': None
        }
        
        try:
            relative_target_path = target_path.lstrip('/')
            target_full_path = os.path.join(filesystem_path, relative_target_path)
            
            if os.path.exists(target_full_path):
                raise FileModificationError(f"Directory already exists: {target_path}")
            
            os.makedirs(target_full_path, exist_ok=True)
            
            if permissions:
                os.chmod(target_full_path, permissions)
            
            result['success'] = True
            result['message'] = f"Successfully created directory: {target_path}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def batch_operations(self, filesystem_path: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform multiple file operations in sequence
        
        Args:
            filesystem_path: Path to extracted filesystem directory
            operations: List of operation dictionaries
            
        Returns:
            Dictionary with batch operation results
        """
        result = {
            'success': True,
            'total_operations': len(operations),
            'successful_operations': 0,
            'failed_operations': 0,
            'results': []
        }
        
        for i, operation in enumerate(operations):
            op_type = operation.get('type')
            op_result = {'operation_index': i, 'type': op_type}
            
            try:
                if op_type == 'insert':
                    op_result.update(self.insert_file(
                        filesystem_path,
                        operation['source_file'],
                        operation['target_path'],
                        operation.get('preserve_permissions', True)
                    ))
                elif op_type == 'remove':
                    op_result.update(self.remove_file(
                        filesystem_path,
                        operation['target_path']
                    ))
                elif op_type == 'replace':
                    op_result.update(self.replace_file(
                        filesystem_path,
                        operation['source_file'],
                        operation['target_path'],
                        operation.get('preserve_permissions', True)
                    ))
                elif op_type == 'create_directory':
                    op_result.update(self.create_directory(
                        filesystem_path,
                        operation['target_path'],
                        operation.get('permissions')
                    ))
                else:
                    op_result.update({
                        'success': False,
                        'error': f"Unknown operation type: {op_type}"
                    })
                
                if op_result['success']:
                    result['successful_operations'] += 1
                else:
                    result['failed_operations'] += 1
                    result['success'] = False
                
            except Exception as e:
                op_result.update({
                    'success': False,
                    'error': str(e)
                })
                result['failed_operations'] += 1
                result['success'] = False
            
            result['results'].append(op_result)
        
        return result
