"""
detector.py

Author: @natelgrw
Last Edited: 11/30/2025

A firmware detection module that automatically identifies 
architecture, endianness, container formats, filesystem types, 
and bootloader segments.
"""

import os
import struct
import subprocess
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import magic


class FirmwareDetector:
    """
    Comprehensive module containing functions for firmware detection.
    """
    
    # magic signatures for container formats
    CONTAINER_SIGNATURES = {
        b'HDR0': 'TRX',
        b'HDR1': 'TRX',
        b'CHK\x00': 'CHK',
        b'\xd0\x0d\xfe\xed': 'FIT',
        b'\x27\x05\x19\x56': 'U-Boot',
        b'\x5d\x00\x00': 'LZMA',
        b'\x1f\x8b': 'GZIP',
        b'BZ': 'BZIP2',
        b'\xfd7zXZ': 'XZ',
    }
    
    # filesystem magic signatures
    FILESYSTEM_SIGNATURES = {
        b'hsqs': 'SquashFS',
        b'sqsh': 'SquashFS',
        b'qshs': 'SquashFS',
        b'shsq': 'SquashFS',
        b'\x53\xef': 'ext2/3/4',
        b'ustar': 'TAR',
    }
    
    # architecture detection patterns
    ARCH_PATTERNS = {
        'ARM': [
            b'\x7fELF\x01\x01\x01\x00',
            b'ARM',
        ],
        'AArch64': [
            b'\x7fELF\x02\x01\x01\x00',
            b'AArch64',
        ],
        'MIPS': [
            b'\x7fELF\x01\x02\x01\x00',
            b'\x7fELF\x02\x02\x01\x00',
            b'MIPS',
        ],
        'PowerPC': [
            b'\x7fELF\x01\x14\x00\x00',
            b'PowerPC',
            b'PPC',
        ],
        'x86': [
            b'\x7fELF\x01\x01\x01\x00',
            b'80386',
            b'Intel 80386',
        ],
        'x86_64': [
            b'\x7fELF\x02\x01\x01\x00',
            b'x86-64',
        ],
    }
    
    def __init__(self, firmware_path: str, extracted_dir: Optional[str] = None):
        """
        Initializes the detector with the firmware file path and 
        optional extracted directory.
        
        Args:
            firmware_path: Path to firmware file
            extracted_dir: Optional path to extracted firmware directory
        """
        self.firmware_path = Path(firmware_path)
        if not self.firmware_path.exists():
            raise FileNotFoundError(f"Firmware file not found: {firmware_path}")
        
        if not self.firmware_path.is_file():
            raise ValueError(f"Path is not a file: {firmware_path}")
        
        self.file_size = self.firmware_path.stat().st_size
        
        if self.file_size == 0:
            raise ValueError(f"Firmware file is empty: {firmware_path}")
        
        self.extracted_dir = Path(extracted_dir) if extracted_dir else None
        self.results = {}
        
    def detect_all(self) -> Dict[str, Any]:
        """
        Performs comprehensive firmware detection.
        
        Returns:
            Dictionary containing all detection results
        """
        encryption_check = self._check_encryption()
        
        self.results = {
            'file_info': self._get_file_info(),
            'encryption_check': encryption_check,
            'architecture': self._detect_architecture(),
            'endianness': self._detect_endianness(),
            'container_formats': self._detect_container_formats(),
            'filesystem_types': self._detect_filesystems(),
            'bootloader_segments': self._detect_bootloader_segments(),
            'compression': self._detect_compression(),
            'binwalk_analysis': self._binwalk_analysis(),
        }
        
        return self.results
    
    def _check_encryption(self) -> Dict[str, Any]:
        """
        Checks if firmware might be encrypted.
        """
        # reads a sample from the file
        sample = self._read_bytes(0, 1024)
        
        if not sample:
            return {
                'possibly_encrypted': True,
                'reason': 'Cannot read file',
            }
        
        entropy = self._calculate_entropy(sample)
        
        encryption_sigs = [
            b'-----BEGIN',
            b'ENCRYPTED',
            b'AES',
            b'DES',
        ]
        
        has_encryption_sig = any(sig in sample for sig in encryption_sigs)
        
        possibly_encrypted = entropy > 7.5 and not has_encryption_sig and len(sample) > 100
        
        return {
            'possibly_encrypted': possibly_encrypted,
            'entropy': round(entropy, 2),
            'has_encryption_signatures': has_encryption_sig,
            'note': 'High entropy may indicate encryption or strong compression' if possibly_encrypted else None,
        }
    
    def _calculate_entropy(self, data: bytes) -> float:
        """
        Calculate Shannon entropy of data.
        """
        if not data:
            return 0.0
        
        import math
        entropy = 0.0
        for x in range(256):
            p_x = float(data.count(bytes([x]))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
        return entropy
    
    def _get_file_info(self) -> Dict[str, Any]:
        """
        Gets basic file information.
        """
        try:
            try:
                mime = magic.Magic(mime=True)
                file_type = magic.Magic()
                mime_type = mime.from_file(str(self.firmware_path))
                file_type_str = file_type.from_file(str(self.firmware_path))
            except Exception:
                result = subprocess.run(
                    ['file', str(self.firmware_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                file_type_str = result.stdout.strip() if result.returncode == 0 else 'unknown'
                mime_type = 'application/octet-stream'
            
            return {
                'path': str(self.firmware_path),
                'size': self.file_size,
                'mime_type': mime_type,
                'file_type': file_type_str,
            }
        except Exception as e:
            return {
                'path': str(self.firmware_path),
                'size': self.file_size,
                'error': str(e),
            }
    
    def _read_bytes(self, offset: int = 0, length: int = 1024) -> bytes:
        """
        Reads bytes from the firmware file.
        """
        try:
            with open(self.firmware_path, 'rb') as f:
                f.seek(offset)
                return f.read(length)
        except (IOError, OSError) as e:
            return b''
    
    def _detect_architecture(self) -> Dict[str, Any]:
        """
        Detect CPU architectures using priority-based approach:
        1. Kernel image magic headers (highest priority)
        2. Device Tree Blob (DTB) parsing
        3. U-Boot header inspection
        4. ELF binary inspection (BusyBox)
        5. Byte-pattern detection (lowest priority, fallback)
        """
        detected_arch = None
        detection_method = None
        confidence = 'low'
        
        # 1: kernel image magic headers
        kernel_arch = self._detect_kernel_architecture()
        if kernel_arch:
            detected_arch = kernel_arch['arch']
            detection_method = kernel_arch['method']
            confidence = 'high'
            return {
                'detected': [detected_arch],
                'confidence': confidence,
                'method': detection_method,
            }
        
        # 2: device tree blob parsing
        dtb_arch = self._detect_dtb_architecture()
        if dtb_arch:
            detected_arch = dtb_arch['arch']
            detection_method = dtb_arch['method']
            confidence = 'high'
            return {
                'detected': [detected_arch],
                'confidence': confidence,
                'method': detection_method,
            }
        
        # 3: U-Boot header inspection
        uboot_arch = self._detect_uboot_architecture()
        if uboot_arch:
            detected_arch = uboot_arch['arch']
            detection_method = uboot_arch['method']
            confidence = 'high'
            return {
                'detected': [detected_arch],
                'confidence': confidence,
                'method': detection_method,
            }
        
        # 4: ELF binary inspection
        busybox_arch = self._detect_busybox_architecture()
        if busybox_arch:
            detected_arch = busybox_arch['arch']
            detection_method = busybox_arch['method']
            confidence = 'high'
            return {
                'detected': [detected_arch],
                'confidence': confidence,
                'method': detection_method,
            }
        
        # 5: fallback - ELF header detection
        elf_arch = self._detect_elf_architecture()
        if elf_arch:
            detected_arch = elf_arch['arch']
            detection_method = elf_arch['method']
            confidence = 'medium'
            return {
                'detected': [detected_arch],
                'confidence': confidence,
                'method': detection_method,
            }
        
        return {
            'detected': ['unknown'],
            'confidence': 'low',
            'method': 'none',
        }
    
    def _detect_kernel_architecture(self) -> Optional[Dict[str, str]]:
        """
        Detect architecture from Linux kernel image magic headers.
        """
        if self.extracted_dir:
            kernel_dir = self.extracted_dir / "raw_extracts" / "kernel"

            if not kernel_dir.exists():
                kernel_dir = self.extracted_dir / "kernel"

            if kernel_dir.exists():
                for kernel_file in kernel_dir.iterdir():
                    if kernel_file.is_file():
                        arch = self._analyze_kernel_file(kernel_file)
                        if arch:
                            return arch
        
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 5 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            # ARM Linux zImage magic
            if b'\x18\x28\x6f\x01' in chunk or b'\x01\x6f\x28\x18' in chunk:
                return {'arch': 'ARM', 'method': 'kernel_header_zImage'}
            
            # AArch64 Linux Image
            if b'ARM\x64' in chunk or b'AArch64' in chunk[:100]:
                if b'\xd0\x0d\xfe\xed' in chunk:
                    return {'arch': 'AArch64', 'method': 'kernel_header_Image'}
            
            # MIPS uImage: 0x27051956
            if b'\x27\x05\x19\x56' in chunk or b'\x56\x19\x05\x27' in chunk:
                offset = chunk.find(b'\x27\x05\x19\x56')
                if offset == -1:
                    offset = chunk.find(b'\x56\x19\x05\x27')
                if offset != -1:
                    try:
                        uimg_offset = scanned_bytes + offset
                        uimg_header = self._read_bytes(uimg_offset, 64)
                        if len(uimg_header) >= 64:
                            arch_byte = uimg_header[7]
                            if arch_byte == 4:
                                return {'arch': 'MIPS', 'method': 'kernel_header_uImage'}
                            elif arch_byte == 2:
                                return {'arch': 'ARM', 'method': 'kernel_header_uImage'}
                            elif arch_byte == 5:
                                return {'arch': 'PowerPC', 'method': 'kernel_header_uImage'}
                    except Exception:
                        pass
            
            # x86 bzImage header
            if chunk[:2] == b'MZ' or b'Linux version' in chunk[:512]:
                if b'x86' in chunk[:512].lower() or b'i386' in chunk[:512].lower() or b'i686' in chunk[:512].lower():
                    return {'arch': 'x86', 'method': 'kernel_header_bzImage'}
            
            scanned_bytes += chunk_size
        
        return None
    
    def _analyze_kernel_file(self, kernel_file: Path) -> Optional[Dict[str, str]]:
        """
        Analyzes a kernel file to determine architecture.
        """
        try:
            with open(kernel_file, 'rb') as f:
                header = f.read(512)
            
            # ARM zImage
            if b'\x18\x28\x6f\x01' in header or b'\x01\x6f\x28\x18' in header:
                return {'arch': 'ARM', 'method': 'kernel_file_zImage'}
            
            # MIPS uImage
            if b'\x27\x05\x19\x56' in header[:64] or b'\x56\x19\x05\x27' in header[:64]:
                if len(header) >= 64:
                    arch_byte = header[7]
                    arch_map = {4: 'MIPS', 2: 'ARM', 5: 'PowerPC'}
                    if arch_byte in arch_map:
                        return {'arch': arch_map[arch_byte], 'method': 'kernel_file_uImage'}
            
            # x86 bzImage
            if header[:2] == b'MZ':
                return {'arch': 'x86', 'method': 'kernel_file_bzImage'}
        except Exception:
            pass
        return None
    
    def _detect_dtb_architecture(self) -> Optional[Dict[str, str]]:
        """
        Detects architecture from Device Tree Blob (DTB).
        """
        if self.extracted_dir:
            dtb_dir = self.extracted_dir / "raw_extracts" / "dtb"

            if not dtb_dir.exists():
                dtb_dir = self.extracted_dir / "dtb"

            if dtb_dir.exists():
                for dtb_file in dtb_dir.iterdir():
                    if dtb_file.is_file():
                        arch = self._analyze_dtb_file(dtb_file)
                        if arch:
                            return arch
        
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 10 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            dtb_magic_be = b'\xd0\x0d\xfe\xed'
            dtb_magic_le = b'\xed\xfe\x0d\xd0'
            
            for magic_bytes in [dtb_magic_be, dtb_magic_le]:
                if magic_bytes in chunk:
                    offset = chunk.find(magic_bytes) + scanned_bytes
                    try:
                        dtb_chunk = self._read_bytes(offset, min(1024 * 1024, self.file_size - offset))
                        dtb_str = dtb_chunk.decode('utf-8', errors='ignore')
                        
                        if 'arm,cortex' in dtb_str.lower() or 'arm,armv' in dtb_str.lower():
                            if 'arm64' in dtb_str.lower() or 'aarch64' in dtb_str.lower():
                                return {'arch': 'AArch64', 'method': 'DTB_compatible_string'}
                            return {'arch': 'ARM', 'method': 'DTB_compatible_string'}
                        elif 'mips' in dtb_str.lower():
                            return {'arch': 'MIPS', 'method': 'DTB_compatible_string'}
                        elif 'powerpc' in dtb_str.lower() or 'ppc' in dtb_str.lower():
                            return {'arch': 'PowerPC', 'method': 'DTB_compatible_string'}
                        elif 'x86' in dtb_str.lower() or 'intel' in dtb_str.lower():
                            return {'arch': 'x86', 'method': 'DTB_compatible_string'}
                    except Exception:
                        pass
            
            scanned_bytes += chunk_size
        
        return None
    
    def _analyze_dtb_file(self, dtb_file: Path) -> Optional[Dict[str, str]]:
        """
        Analyzes a DTB file to determine architecture.
        """
        try:
            with open(dtb_file, 'rb') as f:
                dtb_data = f.read(min(1024 * 1024, dtb_file.stat().st_size))
            
            dtb_str = dtb_data.decode('utf-8', errors='ignore')
            
            if 'arm,cortex' in dtb_str.lower() or 'arm,armv' in dtb_str.lower():
                if 'arm64' in dtb_str.lower() or 'aarch64' in dtb_str.lower():
                    return {'arch': 'AArch64', 'method': 'DTB_file_compatible_string'}
                return {'arch': 'ARM', 'method': 'DTB_file_compatible_string'}
            elif 'mips' in dtb_str.lower():
                return {'arch': 'MIPS', 'method': 'DTB_file_compatible_string'}
            elif 'powerpc' in dtb_str.lower() or 'ppc' in dtb_str.lower():
                return {'arch': 'PowerPC', 'method': 'DTB_file_compatible_string'}
            elif 'x86' in dtb_str.lower() or 'intel' in dtb_str.lower():
                return {'arch': 'x86', 'method': 'DTB_file_compatible_string'}
        except Exception:
            pass
        return None
    
    def _detect_uboot_architecture(self) -> Optional[Dict[str, str]]:
        """
        Detects architecture from U-Boot image headers.
        """
        # U-Boot uImage magic: 0x27051956
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 5 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            # look for uImage magic
            if b'\x27\x05\x19\x56' in chunk or b'\x56\x19\x05\x27' in chunk:
                offset = chunk.find(b'\x27\x05\x19\x56')
                if offset == -1:
                    offset = chunk.find(b'\x56\x19\x05\x27')
                
                if offset != -1:
                    try:
                        uimg_offset = scanned_bytes + offset
                        uimg_header = self._read_bytes(uimg_offset, 64)
                        if len(uimg_header) >= 64:
                            arch_byte = uimg_header[7]
                            arch_map = {
                                2: 'ARM',
                                4: 'MIPS',
                                5: 'PowerPC',
                                3: 'x86',
                            }
                            if arch_byte in arch_map:
                                return {'arch': arch_map[arch_byte], 'method': 'U-Boot_uImage_header'}
                    except Exception:
                        pass
            
            scanned_bytes += chunk_size
        
        return None
    
    def _detect_busybox_architecture(self) -> Optional[Dict[str, str]]:
        """
        Detects architecture by inspecting BusyBox ELF binary.
        """
        if self.extracted_dir:
            binaries_dir = self.extracted_dir / "binaries"
            if binaries_dir.exists():
                for binary_file in binaries_dir.iterdir():
                    if binary_file.is_file() and 'busybox' in binary_file.name.lower():
                        arch = self._analyze_elf_binary(binary_file)
                        if arch:
                            return arch
            
            # check rootfs recursively for busybox
            rootfs_dir = self.extracted_dir / "raw_extracts" / "rootfs"
            if not rootfs_dir.exists():
                rootfs_dir = self.extracted_dir / "rootfs"
            if rootfs_dir.exists():
                for busybox_path in rootfs_dir.rglob('busybox'):
                    if busybox_path.is_file():
                        arch = self._analyze_elf_binary(busybox_path)
                        if arch:
                            return arch
                
                # check common binary locations
                for bin_path in [rootfs_dir / "bin" / "busybox", 
                                rootfs_dir / "sbin" / "busybox",
                                rootfs_dir / "usr" / "bin" / "busybox"]:
                    if bin_path.exists():
                        arch = self._analyze_elf_binary(bin_path)
                        if arch:
                            return arch
        
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            for line in result.stdout.split('\n'):
                if 'ELF' in line and ('busybox' in line.lower() or 'executable' in line.lower()):
                    match = re.search(r'(\d+)', line)
                    if match:
                        offset = int(match.group(1))
                        elf_chunk = self._read_bytes(offset, 20)
                        if len(elf_chunk) >= 20 and elf_chunk[:4] == b'\x7fELF':
                            ei_data = elf_chunk[5]
                            ei_machine = struct.unpack('<H', elf_chunk[18:20])[0] if ei_data == 1 else struct.unpack('>H', elf_chunk[18:20])[0]
                            
                            machine_map = {
                                0x03: 'x86',
                                0x3E: 'x86_64',
                                0x28: 'ARM',
                                0xB7: 'AArch64',
                                0x08: 'MIPS',
                                0x14: 'PowerPC',
                                0x15: 'PowerPC64',
                                0xF3: 'RISC-V',
                            }
                            
                            if ei_machine in machine_map:
                                arch = machine_map[ei_machine]
                                return {'arch': arch, 'method': 'BusyBox_ELF_header'}
        except Exception:
            pass
        
        return None
    
    def _analyze_elf_binary(self, binary_file: Path) -> Optional[Dict[str, str]]:
        """
        Analyzes an ELF binary to determine architecture.
        """
        try:
            with open(binary_file, 'rb') as f:
                elf_header = f.read(20)
            
            if len(elf_header) >= 20 and elf_header[:4] == b'\x7fELF':
                ei_data = elf_header[5]
                ei_machine = struct.unpack('<H', elf_header[18:20])[0] if ei_data == 1 else struct.unpack('>H', elf_header[18:20])[0]
                
                machine_map = {
                    0x03: 'x86',
                    0x3E: 'x86_64',
                    0x28: 'ARM',
                    0xB7: 'AArch64',
                    0x08: 'MIPS',
                    0x14: 'PowerPC',
                    0x15: 'PowerPC64',
                    0xF3: 'RISC-V',
                }
                
                if ei_machine in machine_map:
                    arch = machine_map[ei_machine]
                    return {'arch': arch, 'method': f'ELF_binary_{binary_file.name}'}
        except Exception:
            pass
        return None
    
    def _detect_elf_architecture(self) -> Optional[Dict[str, str]]:
        """
        Fallback: Detect architecture from ELF headers (lowest priority).
        """
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 2 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            # look for ELF headers
            if b'\x7fELF' in chunk:
                offset = chunk.find(b'\x7fELF') + scanned_bytes
                elf_header = self._read_bytes(offset, 20)
                if len(elf_header) >= 20:
                    ei_data = elf_header[5]
                    ei_machine = struct.unpack('<H', elf_header[18:20])[0] if ei_data == 1 else struct.unpack('>H', elf_header[18:20])[0]
                    
                    machine_map = {
                        0x03: 'x86',
                        0x3E: 'x86_64',
                        0x28: 'ARM',
                        0xB7: 'AArch64',
                        0x08: 'MIPS',
                        0x14: 'PowerPC',
                        0x15: 'PowerPC64',
                        0xF3: 'RISC-V',
                    }
                    
                    if ei_machine in machine_map:
                        arch = machine_map[ei_machine]
                        return {'arch': arch, 'method': 'ELF_header_fallback'}
            
            scanned_bytes += chunk_size
        
        return None
    
    def _detect_endianness(self) -> Dict[str, Any]:
        """
        Detects byte endianness.
        """
        endianness = []
        methods = []
        
        # check extracted binaries for ELF files
        if self.extracted_dir:
            rootfs_dir = self.extracted_dir / "raw_extracts" / "rootfs"
            if not rootfs_dir.exists():
                rootfs_dir = self.extracted_dir / "rootfs"
            if rootfs_dir.exists():
                for bin_name in ['busybox', 'ash', 'sh', 'init']:
                    for bin_path in rootfs_dir.rglob(bin_name):
                        if bin_path.is_file():
                            try:
                                with open(bin_path, 'rb') as f:
                                    elf_header = f.read(20)
                                if len(elf_header) >= 20 and elf_header[:4] == b'\x7fELF':
                                    ei_data = elf_header[5]
                                    if ei_data == 1 and 'little' not in endianness:
                                        endianness.append('little')
                                        methods.append(f'extracted_binary_{bin_name}')
                                    elif ei_data == 2 and 'big' not in endianness:
                                        endianness.append('big')
                                        methods.append(f'extracted_binary_{bin_name}')
                                    if endianness:
                                        break
                            except Exception:
                                pass
                    if endianness:
                        break
        
        # scan for ELF files throughout the firmware
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 10 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            offset = 0
            while True:
                elf_pos = chunk.find(b'\x7fELF', offset)
                if elf_pos == -1:
                    break
                
                if elf_pos + 20 <= len(chunk):
                    elf_header = chunk[elf_pos:elf_pos + 20]
                    ei_data = elf_header[5]
                    
                    if ei_data == 1:
                        if 'little' not in endianness:
                            endianness.append('little')
                            methods.append(f'ELF_at_offset_{scanned_bytes + elf_pos}')
                    elif ei_data == 2:
                        if 'big' not in endianness:
                            endianness.append('big')
                            methods.append(f'ELF_at_offset_{scanned_bytes + elf_pos}')
                
                offset = elf_pos + 1
                if offset >= len(chunk):
                    break
            
            scanned_bytes += chunk_size
        
        header = self._read_bytes(0, 20)
        if header[:4] == b'\x7fELF':
            ei_data = header[5]
            if ei_data == 1 and 'little' not in endianness:
                endianness.append('little')
                methods.append('ELF_header_at_start')
            elif ei_data == 2 and 'big' not in endianness:
                endianness.append('big')
                methods.append('ELF_header_at_start')
        
        # check for endianness indicators in strings
        try:
            result = subprocess.run(
                ['strings', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            strings_output = result.stdout.lower()
            if 'little-endian' in strings_output or 'little endian' in strings_output:
                if 'little' not in endianness:
                    endianness.append('little')
                    methods.append('strings_analysis')
            if 'big-endian' in strings_output or 'big endian' in strings_output:
                if 'big' not in endianness:
                    endianness.append('big')
                    methods.append('strings_analysis')
        except Exception:
            pass
        
        header = self._read_bytes(0, 1024)
        
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            for line in result.stdout.split('\n'):
                if 'ELF' in line and ('executable' in line.lower() or 'shared' in line.lower() or 'object' in line.lower()):
                    match = re.search(r'(\d+)', line)
                    if match:
                        offset = int(match.group(1))
                        elf_chunk = self._read_bytes(offset, 20)
                        if len(elf_chunk) >= 20 and elf_chunk[:4] == b'\x7fELF':
                            ei_data = elf_chunk[5]
                            if ei_data == 1 and 'little' not in endianness:
                                endianness.append('little')
                                methods.append(f'binwalk_ELF_at_{offset}')
                            elif ei_data == 2 and 'big' not in endianness:
                                endianness.append('big')
                                methods.append(f'binwalk_ELF_at_{offset}')
        except Exception:
            pass
        
        if not endianness:
            arch_results = self._detect_architecture()
            detected_archs = arch_results.get('detected', [])
            
            arch_endianness = {
                'MIPS': 'big',
                'PowerPC': 'big',
                'ARM': 'little',
                'AArch64': 'little',
                'x86': 'little',
                'x86_64': 'little',
            }
            
            for arch in detected_archs:
                if arch in arch_endianness:
                    inferred_endian = arch_endianness[arch]
                    if inferred_endian not in endianness:
                        endianness.append(inferred_endian)
                        methods.append(f'inferred_from_{arch}_architecture')
                        break
        
        return {
            'detected': list(set(endianness)) if endianness else ['unknown'],
            'detection_methods': methods[:5],
            'confidence': 'high' if endianness and 'inferred' not in str(methods) else ('medium' if endianness else 'low'),
        }
    
    def _detect_container_formats(self) -> List[Dict[str, Any]]:
        """
        Detects firmware container formats.
        """
        containers = []
        
        # read header for signature detection
        header = self._read_bytes(0, 512)
        
        # check for known container signatures
        for sig, container_type in self.CONTAINER_SIGNATURES.items():
            if sig in header:
                offset = header.find(sig)
                containers.append({
                    'type': container_type,
                    'offset': offset,
                    'signature': sig.hex(),
                    'method': 'magic_signature',
                })
        
        # check for TRX format
        if header[:4] in [b'HDR0', b'HDR1']:
            try:
                # Pare TRX header
                trx_header = struct.unpack('<IIIIIIII', header[:32])
                magic_num, len_total, crc32, flag_version, offsets, len_kernel, len_rootfs, len_rootfs_initrd = trx_header
                
                containers.append({
                    'type': 'TRX',
                    'offset': 0,
                    'total_length': len_total,
                    'kernel_length': len_kernel,
                    'rootfs_length': len_rootfs,
                    'rootfs_initrd_length': len_rootfs_initrd,
                    'method': 'TRX_header_parsing',
                })
            except Exception:
                pass
        
        # check for CHK format
        if header[:4] == b'CHK\x00':
            containers.append({
                'type': 'CHK',
                'offset': 0,
                'method': 'CHK_signature',
            })
        
        # check for U-Boot FIT format
        if header[:4] == b'\xd0\x0d\xfe\xed':
            containers.append({
                'type': 'FIT',
                'offset': 0,
                'method': 'FIT_signature',
            })
        
        # use binwalk to find containers
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            for line in result.stdout.split('\n'):
                if 'TRX' in line or 'CHK' in line or 'FIT' in line:
                    match = re.search(r'(\d+)', line)
                    if match:
                        offset = int(match.group(1))
                        if 'TRX' in line and not any(c['type'] == 'TRX' for c in containers):
                            containers.append({
                                'type': 'TRX',
                                'offset': offset,
                                'method': 'binwalk',
                            })
        except Exception:
            pass
        
        return containers
    
    def _detect_filesystems(self) -> List[Dict[str, Any]]:
        """
        Detects embedded filesystem types.
        """
        filesystems = []
        seen_types = {}
        
        # read file in chunks to find filesystem signatures
        chunk_size = 4096
        scanned_bytes = 0
        max_scan = min(self.file_size, 10 * 1024 * 1024)
        
        while scanned_bytes < max_scan:
            chunk = self._read_bytes(scanned_bytes, chunk_size)
            if not chunk:
                break
            
            # check for filesystem signatures
            for sig, fs_type in self.FILESYSTEM_SIGNATURES.items():
                if sig in chunk:
                    offset = chunk.find(sig) + scanned_bytes
                    
                    # only keep first occurrence of each filesystem type
                    if fs_type not in seen_types:
                        seen_types[fs_type] = True
                        filesystems.append({
                            'type': fs_type,
                            'offset': offset,
                            'signature': sig.hex() if len(sig) <= 16 else sig[:16].hex(),
                            'method': 'magic_signature',
                        })
            
            scanned_bytes += chunk_size
        
        # use binwalk for deeper analysis
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            binwalk_fs_types = {
                'SquashFS': 'SquashFS',
                'ext2': 'ext2/3/4',
                'ext3': 'ext2/3/4',
                'ext4': 'ext2/3/4',
                'tar': 'TAR',
            }
            
            for line in result.stdout.split('\n'):
                for binwalk_name, fs_type in binwalk_fs_types.items():
                    if binwalk_name in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            offset = int(match.group(1))
                            if fs_type not in seen_types:
                                seen_types[fs_type] = True
                                filesystems.append({
                                    'type': fs_type,
                                    'offset': offset,
                                    'method': 'binwalk',
                                })
        except Exception:
            pass
        
        return filesystems
    
    def _detect_bootloader_segments(self) -> List[Dict[str, Any]]:
        """
        Detects bootloader segments and headers.
        """
        bootloaders = []
        
        header = self._read_bytes(0, 1024)
        
        # U-Boot signatures
        u_boot_sigs = [
            (b'U-Boot', 'U-Boot'),
            (b'\x27\x05\x19\x56', 'U-Boot'),
            (b'uboot', 'U-Boot'),
        ]
        
        for sig, name in u_boot_sigs:
            if sig in header:
                offset = header.find(sig)
                bootloaders.append({
                    'type': name,
                    'offset': offset,
                    'signature': sig.hex() if len(sig) <= 16 else sig[:16].hex(),
                    'method': 'signature',
                })
        
        # check for bootloader strings
        try:
            result = subprocess.run(
                ['strings', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            bootloader_patterns = {
                'U-Boot': ['U-Boot', 'uboot'],
                'RedBoot': ['RedBoot', 'redboot'],
                'CFE': ['CFE', 'Broadcom CFE'],
                'Das U-Boot': ['Das U-Boot'],
            }
            
            for boot_type, patterns in bootloader_patterns.items():
                if any(pattern in result.stdout for pattern in patterns):
                    if not any(b['type'] == boot_type for b in bootloaders):
                        bootloaders.append({
                            'type': boot_type,
                            'method': 'strings_analysis',
                        })
        except Exception:
            pass
        
        common_offsets = [0, 0x1000, 0x2000, 0x4000, 0x8000]
        for offset in common_offsets:
            if offset < self.file_size:
                chunk = self._read_bytes(offset, 256)
                if b'U-Boot' in chunk or b'uboot' in chunk:
                    if not any(b['type'] == 'U-Boot' and b.get('offset') == offset for b in bootloaders):
                        bootloaders.append({
                            'type': 'U-Boot',
                            'offset': offset,
                            'method': 'offset_scan',
                        })
        
        return bootloaders
    
    def _detect_compression(self) -> List[Dict[str, Any]]:
        """
        Detects compression algorithms.
        """
        compression = []
        
        header = self._read_bytes(0, 1024)
        
        compression_sigs = {
            b'\x1f\x8b': 'GZIP',
            b'BZ': 'BZIP2',
            b'\xfd7zXZ': 'XZ',
            b'\x5d\x00\x00': 'LZMA',
            b'\x02!LZ': 'LZ4',
            b'\x28\xb5\x2f\xfd': 'ZSTD',
        }
        
        for sig, comp_type in compression_sigs.items():
            if sig in header:
                offset = header.find(sig)
                compression.append({
                    'type': comp_type,
                    'offset': offset,
                    'signature': sig.hex(),
                })
        
        return compression
    
    def _binwalk_analysis(self) -> Dict[str, Any]:
        """
        Runs binwalk analysis for comprehensive detection.
        """
        try:
            result = subprocess.run(
                ['binwalk', str(self.firmware_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output_lines = result.stdout.split('\n')
            summary_lines = output_lines[:50]
            if len(output_lines) > 50:
                summary_lines.append(f'... ({len(output_lines) - 50} more lines truncated)')
            
            # extract key findings
            key_findings = []
            for line in output_lines[:100]:
                if any(keyword in line.lower() for keyword in ['squashfs', 'elf', 'trx', 'chk', 'fit']):
                    key_findings.append(line.strip())
                    if len(key_findings) >= 20:
                        break
            
            return {
                'success': True,
                'summary': '\n'.join(summary_lines),
                'key_findings': key_findings[:20],
                'total_lines': len(output_lines),
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'binwalk timeout',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
