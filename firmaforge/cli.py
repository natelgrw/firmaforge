"""
FirmaForge CLI interface
"""

import os
import sys
import click
import json
from pathlib import Path
from .detector import FirmwareDetector, FirmwareType
from .extractor import FirmwareExtractor, ExtractionError


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    FirmaForge - Firmware modification and analysis tool
    
    Extract, modify, and rebuild firmware images for routers, IoT devices, and embedded systems.
    """
    pass


@main.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for extracted files')
@click.option('--info-only', '-i', is_flag=True, help='Only show firmware information, do not extract')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def extract(firmware_path, output, info_only, verbose):
    """
    Extract firmware filesystem to a directory
    
    FIRMWARE_PATH: Path to the firmware file to extract
    """
    if verbose:
        click.echo(f"Analyzing firmware: {firmware_path}")
    
    # Initialize components
    detector = FirmwareDetector()
    extractor = FirmwareExtractor()
    
    try:
        # Detect firmware type
        detection_result = detector.detect_firmware_type(firmware_path)
        
        if verbose:
            click.echo("Detection Results:")
            click.echo(json.dumps(detection_result, indent=2, default=str))
        
        # Display firmware information
        click.echo(f"\n📁 Firmware Analysis: {firmware_path}")
        click.echo(f"   File Size: {detection_result.get('file_size', 0):,} bytes")
        click.echo(f"   MIME Type: {detection_result.get('mime_type', 'Unknown')}")
        click.echo(f"   Filesystem: {detection_result.get('filesystem_type', 'Unknown')}")
        
        if detection_result.get('signatures_found'):
            click.echo("   Signatures Found:")
            for sig in detection_result['signatures_found']:
                click.echo(f"     - {sig['type'].value} (confidence: {sig['confidence']:.2f})")
        
        # Get filesystem info
        fs_type = detection_result.get('filesystem_type', FirmwareType.UNKNOWN)
        fs_info = detector.get_filesystem_info(firmware_path, fs_type)
        
        click.echo(f"\n🔧 Filesystem Information:")
        click.echo(f"   Type: {fs_info['type'].value}")
        click.echo(f"   Extractable: {'Yes' if fs_info['extractable'] else 'No'}")
        
        if fs_info['tools_required']:
            click.echo(f"   Required Tools: {', '.join(fs_info['tools_required'])}")
        
        if fs_info['notes']:
            click.echo("   Notes:")
            for note in fs_info['notes']:
                click.echo(f"     - {note}")
        
        # Check if extraction is possible
        if not fs_info['extractable']:
            click.echo(f"\n❌ Cannot extract {fs_type.value} filesystem")
            if fs_info['tools_required']:
                click.echo(f"   Install required tools: {', '.join(fs_info['tools_required'])}")
            return
        
        # If info-only, stop here
        if info_only:
            click.echo(f"\n✅ Analysis complete. Use --output to extract files.")
            return
        
        # Determine output directory
        if not output:
            firmware_name = Path(firmware_path).stem
            output = f"{firmware_name}_extracted"
        
        click.echo(f"\n🚀 Extracting to: {output}")
        
        # Extract firmware
        extraction_result = extractor.extract_firmware(firmware_path, output)
        
        if extraction_result['success']:
            click.echo(f"✅ Extraction successful!")
            click.echo(f"   Method: {extraction_result['extraction_method']}")
            click.echo(f"   Files extracted: {len(extraction_result['extracted_files'])}")
            
            if verbose and extraction_result['extracted_files']:
                click.echo("\n📋 Extracted files:")
                for file_path in extraction_result['extracted_files'][:20]:  # Show first 20
                    click.echo(f"   {file_path}")
                if len(extraction_result['extracted_files']) > 20:
                    click.echo(f"   ... and {len(extraction_result['extracted_files']) - 20} more files")
        else:
            click.echo(f"❌ Extraction failed: {extraction_result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml', 'text']), 
              default='text', help='Output format')
def analyze(firmware_path, output_format):
    """
    Analyze firmware without extracting
    
    FIRMWARE_PATH: Path to the firmware file to analyze
    """
    detector = FirmwareDetector()
    
    try:
        detection_result = detector.detect_firmware_type(firmware_path)
        fs_type = detection_result.get('filesystem_type', FirmwareType.UNKNOWN)
        fs_info = detector.get_filesystem_info(firmware_path, fs_type)
        
        # Combine results
        analysis = {
            'firmware_path': firmware_path,
            'detection': detection_result,
            'filesystem_info': fs_info
        }
        
        if output_format == 'json':
            click.echo(json.dumps(analysis, indent=2, default=str))
        elif output_format == 'yaml':
            import yaml
            click.echo(yaml.dump(analysis, default_flow_style=False))
        else:
            # Text format
            click.echo(f"Firmware Analysis: {firmware_path}")
            click.echo(f"File Size: {detection_result.get('file_size', 0):,} bytes")
            click.echo(f"Filesystem: {fs_type.value}")
            click.echo(f"Extractable: {'Yes' if fs_info['extractable'] else 'No'}")
    
    except Exception as e:
        click.echo(f"❌ Analysis failed: {str(e)}")
        sys.exit(1)


@main.command()
def tools():
    """Check availability of required extraction tools"""
    extractor = FirmwareExtractor()
    
    tools_to_check = [
        'unsquashfs',  # SquashFS
        'jefferson',   # JFFS2
        '7z',          # ext2/3/4, general archive
        'debugfs',     # ext2/3/4
        'cramfsck',    # CramFS
        'ubireader',   # UBIFS
    ]
    
    click.echo("🔧 Checking extraction tools availability:")
    click.echo()
    
    available_tools = []
    missing_tools = []
    
    for tool in tools_to_check:
        if extractor._check_tool_available(tool):
            click.echo(f"✅ {tool}")
            available_tools.append(tool)
        else:
            click.echo(f"❌ {tool}")
            missing_tools.append(tool)
    
    click.echo()
    click.echo(f"Available: {len(available_tools)}/{len(tools_to_check)} tools")
    
    if missing_tools:
        click.echo(f"\nMissing tools: {', '.join(missing_tools)}")
        click.echo("\nInstallation instructions:")
        click.echo("  macOS: brew install squashfs-tools jefferson p7zip e2fsprogs cramfsprogs ubi_reader")
        click.echo("  Ubuntu: sudo apt install squashfs-tools jefferson p7zip-full e2fsprogs cramfsprogs ubi-utils")


if __name__ == '__main__':
    main()
