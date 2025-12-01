"""
extractor.py

Author: @natelgrw
Last Edited: 11/30/2025

A firmware extractor module that automatically 
extracts kernel and rootfs from firmware files.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import re


class FirmwareExtractor:
    """
    Fast and efficient module containing functions for firmware extraction.
    """
    
    def __init__(self, firmware_path: str, output_dir: str = None):
        """
        Initializes the extractor with the firmware file path and 
        optional output directory.
        
        Args:
            firmware_path: Path to firmware file
            output_dir: Optional path to output directory
        """
        self.firmware_path = Path(firmware_path)
        if not self.firmware_path.exists():
            raise FileNotFoundError(f"Firmware file not found: {firmware_path}")
        if not self.firmware_path.is_file():
            raise ValueError(f"Path is not a file: {firmware_path}")

        self.firmware_name = self.firmware_path.stem
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("results") / f"{self.firmware_name}_extracted"
        
        # initializing directoies for extraction
        self.raw_dir = self.output_dir / "raw_extracts"
        self.kernel_dir = self.raw_dir / "kernel"
        self.rootfs_dir = self.raw_dir / "rootfs"
        self.extraction_log: List[str] = []
        self.temp_dir = None

        # create directories
        self.kernel_dir.mkdir(parents=True, exist_ok=True)
        self.rootfs_dir.mkdir(parents=True, exist_ok=True)

    def extract_all(self) -> Dict[str, Any]:
        """
        Main extraction method that extracts kernel and the 
        root filesystem from the firmware file.
        
        Returns:
            Dictionary containing extraction results
        """
        results = {
            'output_directory': str(self.output_dir),
            'extraction_log': []
        }
        
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="firmaforge_"))
            
            # 1: run binwalk to extract everything
            self.extraction_log.append("Running binwalk extraction...")
            self._run_binwalk()
            
            # 2: find and extract kernel
            self.extraction_log.append("Searching for kernel...")
            self._extract_kernel()
            
            # 3: find and extract rootfs
            self.extraction_log.append("Searching for rootfs...")
            self._extract_rootfs()
            
        finally:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        results['extraction_log'] = self.extraction_log
        return results

    def _run_binwalk(self) -> None:
        """
        Runs binwalk to extract all embedded files.
        """
        try:
            result = subprocess.run(
                ['binwalk', '-e', '--run-as=root', '-C', str(self.temp_dir), str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                self.extraction_log.append("Binwalk extraction completed")
            else:
                self.extraction_log.append("Binwalk completed with warnings")
        except Exception as e:
            self.extraction_log.append(f"Binwalk error: {str(e)}")

    def _extract_kernel(self) -> None:
        """
        Finds and extracts kernel from binwalk extracts and firmware.
        """
        kernel_found = False
        
        # 1: search in binwalk extracts for kernel files
        for kernel_file in self.temp_dir.rglob('kernel'):
            if kernel_file.is_file() and kernel_file.stat().st_size > 10000:
                name_lower = kernel_file.name.lower()
                if 'list' not in name_lower and 'control' not in name_lower:
                    self._copy_kernel_file(kernel_file)
                    kernel_found = True
                    break
        
        # 2: search for kernel by name patterns
        if not kernel_found:
            patterns = ['*kernel*', '*zImage*', '*uImage*', '*Image*']
            for pattern in patterns:
                for kernel_file in self.temp_dir.rglob(pattern):
                    if kernel_file.is_file() and kernel_file.stat().st_size > 100000:
                        name_lower = kernel_file.name.lower()
                        if 'list' not in name_lower and 'control' not in name_lower:
                            self._copy_kernel_file(kernel_file)
                            kernel_found = True
                            break
                if kernel_found:
                    break
        
        # 3: extract kernel from firmware using binwalk analysis
        if not kernel_found:
            self._extract_kernel_from_firmware()
        
        if not kernel_found:
            self.extraction_log.append("Kernel not found")

    def _copy_kernel_file(self, kernel_path: Path) -> None:
        """
        Copies kernel file to kernel directory.
        """
        try:
            kernel_name = kernel_path.name
            if kernel_name == 'kernel' and kernel_path.parent.name:
                kernel_name = f"{kernel_path.parent.name}_{kernel_name}"
            dest = self.kernel_dir / kernel_name
            shutil.copy2(kernel_path, dest)
            self.extraction_log.append(f"Extracted kernel: {kernel_name} ({dest.stat().st_size} bytes)")
        except Exception as e:
            self.extraction_log.append(f"Error copying kernel: {str(e)}")

    def _extract_kernel_from_firmware(self) -> None:
        """
        Extracts kernel from firmware using binwalk analysis.
        """
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                firmware_size = self.firmware_path.stat().st_size
                kernel_patterns = [
                    (r'lzma.*compressed', 'LZMA'),
                    (r'uimage', 'uImage'),
                    (r'zimage', 'zImage'),
                    (r'linux kernel', 'Linux kernel'),
                ]
                
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    for pattern, kernel_type in kernel_patterns:
                        if re.search(pattern, line_lower):
                            match = re.search(r'(\d+)\s+0x[0-9A-Fa-f]+', line)
                            if match:
                                offset = int(match.group(1))
                                remaining = firmware_size - offset
                                extract_size = min(10 * 1024 * 1024, remaining)
                                
                                self.extraction_log.append(f"Found {kernel_type} kernel at offset {offset}")
                                self._extract_component_at_offset(offset, self.kernel_dir, f"kernel_{offset}_{kernel_type}", extract_size)
                                return
        except Exception as e:
            self.extraction_log.append(f"Error extracting kernel: {str(e)[:100]}")

    def _extract_rootfs(self) -> None:
        """
        Finds and extracts root filesystem while focusing on SquashFS
        detection and extraction.
        """
        rootfs_found = False
        
        # 1: search for SquashFS files in binwalk extracts
        for root_file in self.temp_dir.rglob('root'):
            if root_file.is_file() and self._is_squashfs(root_file):
                if self._extract_squashfs_rootfs(root_file):
                    rootfs_found = True
                    break
        
        # 2: search for SquashFS files
        if not rootfs_found:
            sqfs_files = list(self.temp_dir.rglob('*.squashfs'))
            sqfs_files.sort(key=lambda p: 0 if ('root' in p.name.lower() or 'root' in str(p.parent).lower()) else 1)
            
            for sqfs_file in sqfs_files:
                if sqfs_file.is_file():
                    if self._extract_squashfs_rootfs(sqfs_file):
                        rootfs_found = True
                        break
        
        # 3: extract SquashFS from firmware at detected offsets
        if not rootfs_found:
            self._extract_squashfs_from_firmware()
            file_count = sum(1 for _ in self.rootfs_dir.rglob('*') if _.is_file()) if self.rootfs_dir.exists() else 0
            if file_count > 0:
                rootfs_found = True
        
        if not rootfs_found:
            self.extraction_log.append("Rootfs not found")

    def _extract_squashfs_from_firmware(self) -> None:
        """
        Extracts SquashFS from firmware at detected offsets.
        """
        try:
            firmware_size = self.firmware_path.stat().st_size
            
            # check binwalk output for SquashFS offsets
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            found_offsets = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'squashfs' in line.lower():
                        match = re.search(r'(\d+)\s+0x[0-9A-Fa-f]+', line)
                        if match:
                            found_offsets.append(int(match.group(1)))
            
            # try each SquashFS found
            for offset in sorted(set(found_offsets)):
                test_chunk = self._read_firmware_chunk(offset, min(1024 * 1024, firmware_size - offset))
                if len(test_chunk) == 0:
                    continue
                    
                test_file = self.temp_dir / f"test_{offset}"
                with open(test_file, 'wb') as f:
                    f.write(test_chunk)
                
                try:
                    result = subprocess.run(
                        ['file', str(test_file)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    size_match = re.search(r'(\d+)\s+bytes', result.stdout)
                    if size_match:
                        exact_size = int(size_match.group(1))
                        remaining = firmware_size - offset
                        extract_size = min(exact_size, remaining)
                        
                        fs_data = self._read_firmware_chunk(offset, extract_size)
                        
                        if len(fs_data) > 1024:
                            fs_temp = self.temp_dir / f"squashfs_{offset}"
                            with open(fs_temp, 'wb') as f:
                                f.write(fs_data)
                            
                            if self._extract_squashfs_rootfs(fs_temp):
                                self.extraction_log.append(f"Extracted SquashFS from offset {offset}")
                                return
                except Exception:
                    continue
                        
        except Exception as e:
            self.extraction_log.append(f"Error extracting SquashFS from firmware: {str(e)[:100]}")

    def _extract_squashfs_rootfs(self, sqfs_path: Path) -> bool:
        """Extract SquashFS rootfs."""
        try:
            result = subprocess.run(
                ['file', str(sqfs_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'squashfs' not in result.stdout.lower():
                return False
            
            if self.rootfs_dir.exists():
                shutil.rmtree(self.rootfs_dir)
            self.rootfs_dir.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['unsquashfs', '-f', '-no-xattrs', '-d', str(self.rootfs_dir), str(sqfs_path)],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            file_count = sum(1 for _ in self.rootfs_dir.rglob('*') if _.is_file()) if self.rootfs_dir.exists() else 0
            
            # move contents up if subdirectory exists
            if file_count > 0:
                subdirs = [d for d in self.rootfs_dir.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    subdir = subdirs[0]
                    for item in list(subdir.iterdir()):
                        dest = self.rootfs_dir / item.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.move(str(item), str(dest))
                    subdir.rmdir()
                
                file_count = sum(1 for _ in self.rootfs_dir.rglob('*') if _.is_file())
                if self._has_rootfs_structure(self.rootfs_dir) or file_count > 100:
                    self.extraction_log.append(f"Extracted SquashFS rootfs: {file_count} files")
                    return True
                    
        except Exception as e:
            self.extraction_log.append(f"SquashFS extraction error: {str(e)[:100]}")
        return False

    def _extract_component_at_offset(self, offset: int, target_dir: Path, name: str, size: int = None) -> None:
        """
        Extracts a component from firmware at specific offset.
        """
        try:
            with open(self.firmware_path, 'rb') as f:
                f.seek(offset)
                if size is None:
                    remaining = f.seek(0, 2) - offset
                    extract_size = min(10 * 1024 * 1024, remaining)
                else:
                    extract_size = size
                f.seek(offset)
                data = f.read(extract_size)
            
            if len(data) >= 1024:
                output_file = target_dir / name
                with open(output_file, 'wb') as f:
                    f.write(data)
                self.extraction_log.append(f"Extracted component at offset {offset}: {len(data)} bytes -> {name}")
        except Exception as e:
            self.extraction_log.append(f"Error extracting component: {str(e)[:100]}")

    def _read_firmware_chunk(self, offset: int, size: int) -> bytes:
        """
        Reads a chunk from the firmware file.
        """
        try:
            with open(self.firmware_path, 'rb') as f:
                f.seek(offset)
                return f.read(size)
        except Exception:
            return b''

    def _is_squashfs(self, file_path: Path) -> bool:
        """
        Checks if a given file is SquashFS.
        """
        try:
            result = subprocess.run(
                ['file', str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'squashfs' in result.stdout.lower()
        except Exception:
            return False

    def _has_rootfs_structure(self, directory: Path) -> bool:
        """
        Checks if a given directory has root filesystem structure.
        """
        required_dirs = ['bin', 'etc', 'usr']
        found = sum(1 for d in required_dirs if (directory / d).exists())
        return found >= 2
