"""
QEMU CLI Integration for FirmaForge
==================================

Command-line interface for QEMU emulation capabilities.
Integrates with the main FirmaForge CLI to provide emulation commands.
"""

import click
import json
from .qemu_runner import QEMUEmulator


@click.group()
def emulator():
    """QEMU emulation commands for firmware analysis"""
    pass


@emulator.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.option('--architecture', '-a', 
              type=click.Choice(['arm', 'aarch64', 'mips', 'mipsel', 'mips64', 'x86', 'x86_64', 'riscv32', 'riscv64']),
              help='Target architecture (auto-detected if not specified)')
@click.option('--timeout', '-t', default=30, help='Emulation timeout in seconds')
@click.option('--memory', '-m', default='256M', help='Memory size for emulation')
@click.option('--network/--no-network', default=True, help='Enable network emulation')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def emulate(firmware_path, architecture, timeout, memory, network, verbose):
    """
    Emulate firmware using QEMU
    
    FIRMWARE_PATH: Path to firmware file to emulate
    """
    emulator = QEMUEmulator()
    
    try:
        # Create emulation environment
        config = emulator.create_emulation_environment(firmware_path, architecture)
        config['memory_size'] = memory
        config['network_enabled'] = network
        
        if verbose:
            click.echo(f"🔧 Emulation Configuration:")
            click.echo(f"   Architecture: {config['architecture']}")
            click.echo(f"   Memory: {config['memory_size']}")
            click.echo(f"   Network: {'Enabled' if network else 'Disabled'}")
            click.echo(f"   Timeout: {timeout}s")
        
        # Start emulation
        result = emulator.start_emulation(config, timeout)
        
        if result['success']:
            click.echo(f"✅ Emulation completed successfully!")
            click.echo(f"   Duration: {result['emulation_time']:.2f}s")
            
            if result['crashes']:
                click.echo(f"🚨 Crashes detected: {len(result['crashes'])}")
                for crash in result['crashes']:
                    click.echo(f"   - {crash['type']} ({crash['severity']})")
            else:
                click.echo("   No crashes detected")
                
            if verbose and result['output']:
                click.echo(f"\n📋 Emulation Output:")
                click.echo(result['output'][:500] + "..." if len(result['output']) > 500 else result['output'])
        else:
            click.echo(f"❌ Emulation failed: {result.get('error', 'Unknown error')}")
            if result.get('errors'):
                click.echo(f"   Errors: {result['errors']}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
    
    finally:
        emulator.cleanup()


@emulator.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--iterations', '-i', default=100, help='Number of fuzzing iterations')
@click.option('--architecture', '-a', help='Target architecture')
@click.option('--timeout', '-t', default=10, help='Emulation timeout per iteration')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def fuzz(firmware_path, output_dir, iterations, architecture, timeout, verbose):
    """
    Fuzz emulated firmware for vulnerability discovery
    
    FIRMWARE_PATH: Path to firmware file to fuzz
    OUTPUT_DIR: Directory to save fuzzing results
    """
    import os
    from firmaforge.fuzzer import FirmwareFuzzer
    
    emulator = QEMUEmulator()
    fuzzer = FirmwareFuzzer()
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create emulation environment
        config = emulator.create_emulation_environment(firmware_path, architecture)
        
        # Generate fuzz inputs
        fuzz_inputs = []
        for i in range(iterations):
            # Generate random fuzz data
            import random
            fuzz_data = bytes([random.randint(0, 255) for _ in range(1024)])
            fuzz_inputs.append(fuzz_data)
        
        if verbose:
            click.echo(f"🎯 Starting QEMU-based fuzzing...")
            click.echo(f"   Firmware: {firmware_path}")
            click.echo(f"   Architecture: {config['architecture']}")
            click.echo(f"   Iterations: {iterations}")
            click.echo(f"   Output: {output_dir}")
        
        # Run fuzzing
        result = emulator.fuzz_emulated_firmware(config, fuzz_inputs, iterations)
        
        # Save results
        results_file = os.path.join(output_dir, 'fuzzing_results.json')
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        click.echo(f"✅ Fuzzing completed!")
        click.echo(f"   Total iterations: {result['total_iterations']}")
        click.echo(f"   Crashes found: {result['crashes_found']}")
        click.echo(f"   Unique crashes: {len(result['unique_crashes'])}")
        click.echo(f"   Crash rate: {result['crash_rate']:.2%}")
        click.echo(f"   Results saved: {results_file}")
        
        if verbose and result['crash_inputs']:
            click.echo(f"\n🚨 Crash Details:")
            for crash in result['crash_inputs'][:5]:  # Show first 5
                click.echo(f"   Iteration {crash['iteration']}: {crash['crash']['type']}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
    
    finally:
        emulator.cleanup()


@emulator.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.option('--format', 'output_format', 
              type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def analyze(firmware_path, output_format):
    """
    Analyze firmware for emulation compatibility
    
    FIRMWARE_PATH: Path to firmware file to analyze
    """
    emulator = QEMUEmulator()
    
    try:
        # Detect architecture
        architecture = emulator.detect_architecture(firmware_path)
        
        # Create emulation environment
        config = emulator.create_emulation_environment(firmware_path, architecture)
        
        analysis = {
            'firmware_path': firmware_path,
            'detected_architecture': architecture,
            'qemu_command': config['qemu_command'],
            'supported': architecture in emulator.ARCHITECTURES,
            'recommended_memory': '256M',
            'network_support': True,
            'emulation_ready': True
        }
        
        if output_format == 'json':
            click.echo(json.dumps(analysis, indent=2))
        else:
            click.echo(f"🔍 Firmware Emulation Analysis: {firmware_path}")
            click.echo(f"   Architecture: {architecture}")
            click.echo(f"   QEMU Command: {config['qemu_command']}")
            click.echo(f"   Supported: {'Yes' if analysis['supported'] else 'No'}")
            click.echo(f"   Emulation Ready: {'Yes' if analysis['emulation_ready'] else 'No'}")
            click.echo(f"   Recommended Memory: {analysis['recommended_memory']}")
            click.echo(f"   Network Support: {'Yes' if analysis['network_support'] else 'No'}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
    
    finally:
        emulator.cleanup()


@emulator.command()
def architectures():
    """List supported QEMU architectures"""
    emulator = QEMUEmulator()
    
    click.echo("🏗️  Supported QEMU Architectures:")
    click.echo()
    
    for arch, command in emulator.ARCHITECTURES.items():
        click.echo(f"   {arch:12} - {command}")
    
    click.echo()
    click.echo("Note: QEMU must be installed with support for these architectures")


if __name__ == '__main__':
    emulator()
