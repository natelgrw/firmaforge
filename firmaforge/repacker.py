"""
Firmware repacking module
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from .detector import FirmwareType, FirmwareDetector


class RepackingError(Exception):
    """Raised when firmware repacking fails"""
    pass


class FirmwareRepacker:
    """Handles repacking of modified firmware filesystems"""
    
    def __init__(self):
        self.detector = FirmwareDetector()
    
    def repack_firmware(self, filesystem_dir: str, output_file: str, 
                       filesystem_type: Optional[FirmwareType] = None,
                       preserve_headers: bool = True) -> Dict[str, Any]:
        """
        Repack a modified filesystem into a firmware image
        
        Args:
            filesystem_dir: Path to modified filesystem directory
            output_file: Path for output firmware file
            filesystem_type: Type of filesystem to create (auto-detected if None)
            preserve_headers: Whether to preserve original headers/checksums
            
        Returns:
            Dictionary with repacking results
        """
        result = {
            'success': False,
            'filesystem_type': None,
            'output_file': output_file,
            'method': None,
            'error': None
        }
        
        try:
            # Validate inputs
            if not os.path.exists(filesystem_dir):
                raise RepackingError(f"Filesystem directory does not exist: {filesystem_dir}")
            
            # Auto-detect filesystem type if not provided
            if filesystem_type is None:
                # Try to detect from directory name or look for clues
                filesystem_type = self._detect_filesystem_type_from_dir(filesystem_dir)
            
            if filesystem_type == FirmwareType.UNKNOWN:
                raise RepackingError("Cannot determine filesystem type for repacking")
            
            result['filesystem_type'] = filesystem_type
            
            # Repack based on filesystem type
            if filesystem_type == FirmwareType.SQUASHFS:
                result = self._repack_squashfs(filesystem_dir, output_file, result)
            elif filesystem_type == FirmwareType.JFFS2:
                result = self._repack_jffs2(filesystem_dir, output_file, result)
            elif filesystem_type in [FirmwareType.EXT2, FirmwareType.EXT3, FirmwareType.EXT4]:
                result = self._repack_ext(filesystem_dir, output_file, result)
            elif filesystem_type == FirmwareType.CRAMFS:
                result = self._repack_cramfs(filesystem_dir, output_file, result)
            elif filesystem_type == FirmwareType.UBIFS:
                raise RepackingError(f"UBIFS repacking not yet implemented")
            else:
                raise RepackingError(f"Repacking not implemented for {filesystem_type}")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_filesystem_type_from_dir(self, filesystem_dir: str) -> FirmwareType:
        """Try to detect filesystem type from directory contents or name"""
        dir_name = os.path.basename(filesystem_dir).lower()
        
        # Check directory name for hints
        if 'squashfs' in dir_name:
            return FirmwareType.SQUASHFS
        elif 'jffs2' in dir_name:
            return FirmwareType.JFFS2
        elif 'ext' in dir_name:
            return FirmwareType.EXT2
        elif 'cramfs' in dir_name:
            return FirmwareType.CRAMFS
        
        # Default to SquashFS for most embedded systems
        return FirmwareType.SQUASHFS
    
    def _repack_squashfs(self, filesystem_dir: str, output_file: str, result: Dict) -> Dict:
        """Repack SquashFS filesystem"""
        try:
            # Check if mksquashfs is available
            if not self._check_tool_available('mksquashfs'):
                raise RepackingError("mksquashfs tool not found. Install squashfs-tools.")
            
            # Build mksquashfs command
            cmd = [
                'mksquashfs',
                filesystem_dir,
                output_file,
                '-comp', 'gzip',  # Use gzip compression (most common)
                '-all-root',       # Set all files to root ownership
                '-noappend'        # Don't append to existing file
            ]
            
            # Run mksquashfs
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise RepackingError(f"mksquashfs failed: {process.stderr}")
            
            result['success'] = True
            result['method'] = 'mksquashfs'
            result['message'] = f"Successfully repacked SquashFS filesystem to {output_file}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _repack_jffs2(self, filesystem_dir: str, output_file: str, result: Dict) -> Dict:
        """Repack JFFS2 filesystem"""
        try:
            # Check if mkfs.jffs2 is available
            if not self._check_tool_available('mkfs.jffs2'):
                raise RepackingError("mkfs.jffs2 tool not found. Install mtd-utils.")
            
            # Build mkfs.jffs2 command
            cmd = [
                'mkfs.jffs2',
                '-d', filesystem_dir,  # Directory to pack
                '-o', output_file,     # Output file
                '-e', '0x20000',       # Erase block size (128KB, common default)
                '-l'                   # Little-endian
            ]
            
            # Run mkfs.jffs2
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise RepackingError(f"mkfs.jffs2 failed: {process.stderr}")
            
            result['success'] = True
            result['method'] = 'mkfs.jffs2'
            result['message'] = f"Successfully repacked JFFS2 filesystem to {output_file}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _repack_ext(self, filesystem_dir: str, output_file: str, result: Dict) -> Dict:
        """Repack ext2/3/4 filesystem"""
        try:
            # Try to use mkfs.ext2 first
            if self._check_tool_available('mkfs.ext2'):
                cmd = [
                    'mkfs.ext2',
                    '-d', filesystem_dir,  # Copy directory contents
                    output_file,
                    '-F'  # Force creation
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    result['success'] = True
                    result['method'] = 'mkfs.ext2'
                    result['message'] = f"Successfully repacked ext2 filesystem to {output_file}"
                    return result
            
            # Fallback: create a tar archive (not a true filesystem, but useful)
            if self._check_tool_available('tar'):
                cmd = [
                    'tar',
                    '-czf',
                    output_file.replace('.ext2', '.tar.gz').replace('.ext3', '.tar.gz').replace('.ext4', '.tar.gz'),
                    '-C', filesystem_dir,
                    '.'
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    result['success'] = True
                    result['method'] = 'tar'
                    result['message'] = f"Successfully created tar archive from filesystem"
                    return result
            
            raise RepackingError("Neither mkfs.ext2 nor tar available for repacking")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _repack_cramfs(self, filesystem_dir: str, output_file: str, result: Dict) -> Dict:
        """Repack CramFS filesystem"""
        try:
            # Check if mkcramfs is available
            if not self._check_tool_available('mkcramfs'):
                raise RepackingError("mkcramfs tool not found. Install cramfsprogs.")
            
            # Build mkcramfs command
            cmd = [
                'mkcramfs',
                filesystem_dir,
                output_file
            ]
            
            # Run mkcramfs
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise RepackingError(f"mkcramfs failed: {process.stderr}")
            
            result['success'] = True
            result['method'] = 'mkcramfs'
            result['message'] = f"Successfully repacked CramFS filesystem to {output_file}"
            
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
    
    def get_repacking_info(self, filesystem_type: FirmwareType) -> Dict[str, Any]:
        """
        Get information about repacking capabilities for a filesystem type
        
        Args:
            filesystem_type: Type of filesystem
            
        Returns:
            Dictionary with repacking information
        """
        info = {
            'type': filesystem_type,
            'repackable': False,
            'tools_required': [],
            'notes': []
        }
        
        if filesystem_type == FirmwareType.SQUASHFS:
            info['repackable'] = True
            info['tools_required'] = ['mksquashfs']
            info['notes'].append('SquashFS repacking supported')
            
        elif filesystem_type == FirmwareType.JFFS2:
            info['repackable'] = True
            info['tools_required'] = ['mkfs.jffs2']
            info['notes'].append('JFFS2 repacking supported')
            
        elif filesystem_type in [FirmwareType.EXT2, FirmwareType.EXT3, FirmwareType.EXT4]:
            info['repackable'] = True
            info['tools_required'] = ['mkfs.ext2', 'tar']  # tar as fallback
            info['notes'].append('ext2/3/4 repacking supported (with fallback to tar)')
            
        elif filesystem_type == FirmwareType.CRAMFS:
            info['repackable'] = True
            info['tools_required'] = ['mkcramfs']
            info['notes'].append('CramFS repacking supported')
            
        elif filesystem_type == FirmwareType.UBIFS:
            info['repackable'] = False
            info['notes'].append('UBIFS repacking not yet implemented')
            
        else:
            info['notes'].append('Unknown or unsupported filesystem type for repacking')
        
        return info
    
    def validate_filesystem(self, filesystem_dir: str) -> Dict[str, Any]:
        """
        Validate a filesystem directory before repacking
        
        Args:
            filesystem_dir: Path to filesystem directory
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'total_size': 0
        }
        
        try:
            if not os.path.exists(filesystem_dir):
                result['errors'].append(f"Directory does not exist: {filesystem_dir}")
                return result
            
            if not os.path.isdir(filesystem_dir):
                result['errors'].append(f"Path is not a directory: {filesystem_dir}")
                return result
            
            # Check for essential directories
            essential_dirs = ['bin', 'sbin', 'etc', 'usr']
            missing_dirs = []
            for dir_name in essential_dirs:
                if not os.path.exists(os.path.join(filesystem_dir, dir_name)):
                    missing_dirs.append(dir_name)
            
            if missing_dirs:
                result['warnings'].append(f"Missing common directories: {', '.join(missing_dirs)}")
            
            # Count files and calculate size
            file_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(filesystem_dir):
                file_count += len(files)
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        # Skip files we can't access
                        pass
            
            result['file_count'] = file_count
            result['total_size'] = total_size
            
            if file_count == 0:
                result['errors'].append("No files found in filesystem directory")
            else:
                result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
