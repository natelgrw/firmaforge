"""
Firmware extraction engine
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from .detector import FirmwareType, FirmwareDetector


class ExtractionError(Exception):
    """Raised when firmware extraction fails"""
    pass


class FirmwareExtractor:
    """Handles extraction of different firmware filesystem types"""
    
    def __init__(self):
        self.detector = FirmwareDetector()
        self.temp_dir = None
    
    def extract_firmware(self, firmware_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Extract firmware to a directory
        
        Args:
            firmware_path: Path to the firmware file
            output_dir: Directory to extract files to
            
        Returns:
            Dictionary with extraction results
        """
        result = {
            'success': False,
            'extracted_files': [],
            'filesystem_type': None,
            'extraction_method': None,
            'error': None
        }
        
        try:
            # Detect firmware type
            detection = self.detector.detect_firmware_type(firmware_path)
            filesystem_type = detection.get('filesystem_type', FirmwareType.UNKNOWN)
            result['filesystem_type'] = filesystem_type
            
            if filesystem_type == FirmwareType.UNKNOWN:
                raise ExtractionError("Unknown or unsupported filesystem type")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract based on filesystem type
            if filesystem_type == FirmwareType.SQUASHFS:
                result = self._extract_squashfs(firmware_path, output_dir, result)
            elif filesystem_type == FirmwareType.JFFS2:
                result = self._extract_jffs2(firmware_path, output_dir, result)
            elif filesystem_type in [FirmwareType.EXT2, FirmwareType.EXT3, FirmwareType.EXT4]:
                result = self._extract_ext(firmware_path, output_dir, result)
            elif filesystem_type == FirmwareType.CRAMFS:
                result = self._extract_cramfs(firmware_path, output_dir, result)
            elif filesystem_type == FirmwareType.UBIFS:
                result = self._extract_ubifs(firmware_path, output_dir, result)
            else:
                raise ExtractionError(f"Extraction not implemented for {filesystem_type}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def _extract_squashfs(self, firmware_path: str, output_dir: str, result: Dict) -> Dict:
        """Extract SquashFS filesystem"""
        try:
            # Check if unsquashfs is available
            if not self._check_tool_available('unsquashfs'):
                raise ExtractionError("unsquashfs tool not found. Install squashfs-tools.")
            
            # Run unsquashfs
            cmd = ['unsquashfs', '-f', '-d', output_dir, firmware_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise ExtractionError(f"unsquashfs failed: {process.stderr}")
            
            result['success'] = True
            result['extraction_method'] = 'unsquashfs'
            result['extracted_files'] = self._list_extracted_files(output_dir)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_jffs2(self, firmware_path: str, output_dir: str, result: Dict) -> Dict:
        """Extract JFFS2 filesystem"""
        try:
            # Check if jefferson is available
            if not self._check_tool_available('jefferson'):
                raise ExtractionError("jefferson tool not found. Install jefferson.")
            
            # Run jefferson
            cmd = ['jefferson', firmware_path, '-d', output_dir]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise ExtractionError(f"jefferson failed: {process.stderr}")
            
            result['success'] = True
            result['extraction_method'] = 'jefferson'
            result['extracted_files'] = self._list_extracted_files(output_dir)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_ext(self, firmware_path: str, output_dir: str, result: Dict) -> Dict:
        """Extract ext2/3/4 filesystem"""
        try:
            # Try 7z first (more reliable)
            if self._check_tool_available('7z'):
                cmd = ['7z', 'x', firmware_path, f'-o{output_dir}', '-y']
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    result['success'] = True
                    result['extraction_method'] = '7z'
                    result['extracted_files'] = self._list_extracted_files(output_dir)
                    return result
            
            # Fallback to debugfs
            if self._check_tool_available('debugfs'):
                # Create a temporary file for debugfs output
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    f.write('ls /\n')
                    temp_file = f.name
                
                try:
                    cmd = ['debugfs', '-R', f'cat < {temp_file}', firmware_path]
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode == 0:
                        result['success'] = True
                        result['extraction_method'] = 'debugfs'
                        result['extracted_files'] = self._list_extracted_files(output_dir)
                    else:
                        raise ExtractionError(f"debugfs failed: {process.stderr}")
                        
                finally:
                    os.unlink(temp_file)
            else:
                raise ExtractionError("Neither 7z nor debugfs tools found")
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_cramfs(self, firmware_path: str, output_dir: str, result: Dict) -> Dict:
        """Extract CramFS filesystem"""
        try:
            # Check if cramfsck is available
            if not self._check_tool_available('cramfsck'):
                raise ExtractionError("cramfsck tool not found. Install cramfsprogs.")
            
            # Run cramfsck
            cmd = ['cramfsck', '-x', output_dir, firmware_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise ExtractionError(f"cramfsck failed: {process.stderr}")
            
            result['success'] = True
            result['extraction_method'] = 'cramfsck'
            result['extracted_files'] = self._list_extracted_files(output_dir)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_ubifs(self, firmware_path: str, output_dir: str, result: Dict) -> Dict:
        """Extract UBIFS filesystem"""
        try:
            # Check if ubireader is available
            if not self._check_tool_available('ubireader'):
                raise ExtractionError("ubireader tool not found. Install ubi_reader.")
            
            # Run ubireader
            cmd = ['ubireader', '-o', output_dir, firmware_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise ExtractionError(f"ubireader failed: {process.stderr}")
            
            result['success'] = True
            result['extraction_method'] = 'ubireader'
            result['extracted_files'] = self._list_extracted_files(output_dir)
            
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
    
    def _list_extracted_files(self, directory: str) -> List[str]:
        """List all extracted files"""
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), directory)
                files.append(rel_path)
        return sorted(files)
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
