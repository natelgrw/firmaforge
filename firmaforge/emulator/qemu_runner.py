"""
QEMU Emulation Module for FirmaForge
===================================

This module provides QEMU-based emulation capabilities for firmware analysis,
rehosting, and dynamic testing. Integrates with FirmaForge's existing pipeline
to enable full-system emulation of embedded devices.

Key Features:
- Multi-architecture support (ARM, MIPS, x86, RISC-V)
- Dynamic firmware execution and testing
- Memory and register introspection
- Network emulation for IoT devices
- Automated rehosting workflows
"""

import os
import subprocess
import tempfile
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class QEMUEmulator:
    """QEMU-based firmware emulation and rehosting"""
    
    # Supported architectures and their QEMU commands
    ARCHITECTURES = {
        'arm': 'qemu-system-arm',
        'aarch64': 'qemu-system-aarch64', 
        'mips': 'qemu-system-mips',
        'mipsel': 'qemu-system-mipsel',
        'mips64': 'qemu-system-mips64',
        'x86': 'qemu-system-i386',
        'x86_64': 'qemu-system-x86_64',
        'riscv32': 'qemu-system-riscv32',
        'riscv64': 'qemu-system-riscv64'
    }
    
    def __init__(self):
        self.temp_dir = None
        self.qemu_process = None
        self.emulation_log = []
        
    def detect_architecture(self, firmware_path: str) -> str:
        """
        Detect the target architecture of firmware
        
        Args:
            firmware_path: Path to firmware file
            
        Returns:
            Detected architecture string
        """
        try:
            # Use file command to detect architecture
            result = subprocess.run(['file', firmware_path], 
                                  capture_output=True, text=True)
            
            output = result.stdout.lower()
            
            # Architecture detection patterns
            if 'arm' in output and '64' in output:
                return 'aarch64'
            elif 'arm' in output:
                return 'arm'
            elif 'mips' in output and '64' in output:
                return 'mips64'
            elif 'mips' in output and 'little' in output:
                return 'mipsel'
            elif 'mips' in output:
                return 'mips'
            elif 'x86-64' in output or 'amd64' in output:
                return 'x86_64'
            elif 'i386' in output or 'i686' in output:
                return 'x86'
            elif 'riscv' in output and '64' in output:
                return 'riscv64'
            elif 'riscv' in output:
                return 'riscv32'
            else:
                return 'x86_64'  # Default fallback
                
        except Exception as e:
            print(f"Architecture detection failed: {e}")
            return 'x86_64'
    
    def create_emulation_environment(self, firmware_path: str, 
                                   architecture: str = None) -> Dict[str, Any]:
        """
        Create QEMU emulation environment for firmware
        
        Args:
            firmware_path: Path to firmware file
            architecture: Target architecture (auto-detected if None)
            
        Returns:
            Dictionary with emulation configuration
        """
        if not architecture:
            architecture = self.detect_architecture(firmware_path)
            
        # Create temporary directory for emulation
        self.temp_dir = tempfile.mkdtemp(prefix='firmaforge_qemu_')
        
        config = {
            'architecture': architecture,
            'firmware_path': firmware_path,
            'temp_dir': self.temp_dir,
            'qemu_command': self.ARCHITECTURES.get(architecture, 'qemu-system-x86_64'),
            'memory_size': '256M',
            'network_enabled': True,
            'monitor_socket': os.path.join(self.temp_dir, 'qemu-monitor.sock'),
            'serial_socket': os.path.join(self.temp_dir, 'qemu-serial.sock')
        }
        
        return config
    
    def start_emulation(self, config: Dict[str, Any], 
                       timeout: int = 30) -> Dict[str, Any]:
        """
        Start QEMU emulation of firmware
        
        Args:
            config: Emulation configuration
            timeout: Maximum emulation time in seconds
            
        Returns:
            Dictionary with emulation results
        """
        try:
            # Build QEMU command
            cmd = self._build_qemu_command(config)
            
            print(f"🚀 Starting QEMU emulation: {config['architecture']}")
            print(f"   Command: {' '.join(cmd)}")
            
            # Start QEMU process
            self.qemu_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor emulation
            start_time = time.time()
            result = self._monitor_emulation(config, timeout, start_time)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'emulation_time': 0
            }
    
    def _build_qemu_command(self, config: Dict[str, Any]) -> List[str]:
        """Build QEMU command based on configuration"""
        cmd = [config['qemu_command']]
        
        # Memory configuration
        cmd.extend(['-m', config['memory_size']])
        
        # Network configuration
        if config['network_enabled']:
            cmd.extend(['-netdev', 'user,id=net0'])
            cmd.extend(['-device', 'rtl8139,netdev=net0'])
        
        # Monitor socket
        cmd.extend(['-monitor', f"unix:{config['monitor_socket']},server,nowait"])
        
        # Serial socket
        cmd.extend(['-serial', f"unix:{config['serial_socket']},server,nowait"])
        
        # Firmware file
        cmd.append(config['firmware_path'])
        
        # Additional architecture-specific options
        arch = config['architecture']
        if arch in ['arm', 'aarch64']:
            cmd.extend(['-machine', 'virt'])
        elif arch in ['mips', 'mipsel', 'mips64']:
            cmd.extend(['-machine', 'malta'])
        elif arch in ['riscv32', 'riscv64']:
            cmd.extend(['-machine', 'virt'])
        
        return cmd
    
    def _monitor_emulation(self, config: Dict[str, Any], 
                          timeout: int, start_time: float) -> Dict[str, Any]:
        """Monitor QEMU emulation process"""
        result = {
            'success': False,
            'emulation_time': 0,
            'output': '',
            'errors': '',
            'crashes': [],
            'network_activity': [],
            'system_calls': []
        }
        
        try:
            # Wait for emulation to complete or timeout
            while time.time() - start_time < timeout:
                if self.qemu_process.poll() is not None:
                    # Process completed
                    result['success'] = True
                    result['emulation_time'] = time.time() - start_time
                    break
                    
                time.sleep(0.1)
            
            # Get output
            if self.qemu_process.stdout:
                result['output'] = self.qemu_process.stdout.read()
            if self.qemu_process.stderr:
                result['errors'] = self.qemu_process.stderr.read()
            
            # Analyze output for crashes and issues
            result['crashes'] = self._analyze_crashes(result['output'], result['errors'])
            
        except Exception as e:
            result['error'] = str(e)
        
        finally:
            # Cleanup
            if self.qemu_process:
                self.qemu_process.terminate()
                self.qemu_process.wait()
        
        return result
    
    def _analyze_crashes(self, output: str, errors: str) -> List[Dict[str, Any]]:
        """Analyze emulation output for crashes and issues"""
        crashes = []
        
        # Common crash patterns
        crash_patterns = [
            'segmentation fault',
            'bus error',
            'illegal instruction',
            'stack overflow',
            'memory access violation',
            'kernel panic',
            'system halted'
        ]
        
        combined_output = output + errors
        
        for pattern in crash_patterns:
            if pattern.lower() in combined_output.lower():
                crashes.append({
                    'type': pattern,
                    'timestamp': time.time(),
                    'severity': 'high' if 'panic' in pattern else 'medium'
                })
        
        return crashes
    
    def fuzz_emulated_firmware(self, config: Dict[str, Any], 
                              fuzz_inputs: List[bytes], 
                              iterations: int = 100) -> Dict[str, Any]:
        """
        Fuzz emulated firmware with various inputs
        
        Args:
            config: Emulation configuration
            fuzz_inputs: List of fuzzed input data
            iterations: Number of fuzzing iterations
            
        Returns:
            Dictionary with fuzzing results
        """
        fuzz_results = {
            'total_iterations': iterations,
            'crashes_found': 0,
            'unique_crashes': set(),
            'execution_times': [],
            'crash_inputs': []
        }
        
        print(f"🎯 Fuzzing emulated firmware with {iterations} iterations...")
        
        for i in range(iterations):
            # Create fuzzed firmware
            fuzzed_firmware = self._create_fuzzed_firmware(
                config['firmware_path'], 
                fuzz_inputs[i % len(fuzz_inputs)]
            )
            
            # Update config with fuzzed firmware
            fuzz_config = config.copy()
            fuzz_config['firmware_path'] = fuzzed_firmware
            
            # Run emulation
            result = self.start_emulation(fuzz_config, timeout=10)
            
            # Record results
            fuzz_results['execution_times'].append(result['emulation_time'])
            
            if result['crashes']:
                fuzz_results['crashes_found'] += len(result['crashes'])
                for crash in result['crashes']:
                    fuzz_results['unique_crashes'].add(crash['type'])
                    fuzz_results['crash_inputs'].append({
                        'iteration': i,
                        'input': fuzz_inputs[i % len(fuzz_inputs)].hex()[:32],
                        'crash': crash
                    })
            
            if i % 10 == 0:
                print(f"   Progress: {i}/{iterations} (crashes: {fuzz_results['crashes_found']})")
        
        fuzz_results['unique_crashes'] = list(fuzz_results['unique_crashes'])
        fuzz_results['crash_rate'] = fuzz_results['crashes_found'] / iterations
        
        return fuzz_results
    
    def _create_fuzzed_firmware(self, original_firmware: str, 
                               fuzz_data: bytes) -> str:
        """Create fuzzed version of firmware"""
        fuzzed_path = os.path.join(self.temp_dir, f"fuzzed_{int(time.time())}.bin")
        
        with open(original_firmware, 'rb') as f:
            original_data = f.read()
        
        # Apply fuzzing (simple byte replacement for demo)
        fuzzed_data = bytearray(original_data)
        for i, byte in enumerate(fuzz_data[:len(fuzzed_data)]):
            fuzzed_data[i] = byte
        
        with open(fuzzed_path, 'wb') as f:
            f.write(fuzzed_data)
        
        return fuzzed_path
    
    def cleanup(self):
        """Clean up temporary files and processes"""
        if self.qemu_process:
            self.qemu_process.terminate()
            self.qemu_process.wait()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
