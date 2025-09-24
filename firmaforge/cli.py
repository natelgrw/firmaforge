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
from .modifier import FirmwareModifier, FileModificationError
from .repacker import FirmwareRepacker, RepackingError
from .builder import FirmwareBuilder, FirmwareBuilderError
from .emulator.cli import emulator


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
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('source_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('target_path')
@click.option('--preserve-permissions/--no-preserve-permissions', default=True, 
              help='Preserve file permissions')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def insert(filesystem_path, source_file, target_path, preserve_permissions, verbose):
    """
    Insert a file into an extracted firmware filesystem
    
    FILESYSTEM_PATH: Path to extracted firmware directory
    SOURCE_FILE: Path to file to insert
    TARGET_PATH: Destination path within filesystem (e.g., /usr/bin/busybox)
    """
    if verbose:
        click.echo(f"Inserting {source_file} to {target_path} in {filesystem_path}")
    
    modifier = FirmwareModifier()
    
    try:
        result = modifier.insert_file(filesystem_path, source_file, target_path, preserve_permissions)
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
            if verbose:
                file_info = modifier.get_file_info(filesystem_path, target_path)
                if file_info['success']:
                    click.echo(f"   Size: {file_info['size']} bytes")
                    click.echo(f"   Permissions: {file_info['permissions']}")
        else:
            click.echo(f"❌ Insert failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('target_path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def remove(filesystem_path, target_path, verbose):
    """
    Remove a file or directory from an extracted firmware filesystem
    
    FILESYSTEM_PATH: Path to extracted firmware directory
    TARGET_PATH: Path to file/directory to remove (e.g., /usr/bin/old_binary)
    """
    if verbose:
        click.echo(f"Removing {target_path} from {filesystem_path}")
    
    modifier = FirmwareModifier()
    
    try:
        # Check if file exists first
        file_info = modifier.get_file_info(filesystem_path, target_path)
        if not file_info['success']:
            click.echo(f"❌ File does not exist: {target_path}")
            sys.exit(1)
        
        if verbose:
            click.echo(f"   Found: {'directory' if file_info['is_directory'] else 'file'}")
        
        result = modifier.remove_file(filesystem_path, target_path)
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ Remove failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('source_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('target_path')
@click.option('--preserve-permissions/--no-preserve-permissions', default=True,
              help='Preserve original file permissions')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def replace(filesystem_path, source_file, target_path, preserve_permissions, verbose):
    """
    Replace a file in an extracted firmware filesystem
    
    FILESYSTEM_PATH: Path to extracted firmware directory
    SOURCE_FILE: Path to replacement file
    TARGET_PATH: Path to file to replace (e.g., /usr/bin/busybox)
    """
    if verbose:
        click.echo(f"Replacing {target_path} with {source_file} in {filesystem_path}")
    
    modifier = FirmwareModifier()
    
    try:
        # Check if target exists first
        file_info = modifier.get_file_info(filesystem_path, target_path)
        if not file_info['success']:
            click.echo(f"❌ Target file does not exist: {target_path}")
            sys.exit(1)
        
        if verbose:
            click.echo(f"   Target size: {file_info['size']} bytes")
            click.echo(f"   Target permissions: {file_info['permissions']}")
        
        result = modifier.replace_file(filesystem_path, source_file, target_path, preserve_permissions)
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
            if verbose:
                new_file_info = modifier.get_file_info(filesystem_path, target_path)
                if new_file_info['success']:
                    click.echo(f"   New size: {new_file_info['size']} bytes")
                    click.echo(f"   New permissions: {new_file_info['permissions']}")
        else:
            click.echo(f"❌ Replace failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', '-p', help='Filter files by pattern (e.g., "*.bin", "/bin/*")')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def list_files(filesystem_path, pattern, output_format):
    """
    List files in an extracted firmware filesystem
    
    FILESYSTEM_PATH: Path to extracted firmware directory
    """
    modifier = FirmwareModifier()
    
    try:
        files = modifier.list_files(filesystem_path, pattern)
        
        if output_format == 'json':
            result = {
                'filesystem_path': filesystem_path,
                'pattern': pattern,
                'file_count': len(files),
                'files': files
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"📁 Files in {filesystem_path}:")
            if pattern:
                click.echo(f"   Pattern: {pattern}")
            click.echo(f"   Total files: {len(files)}")
            click.echo()
            
            for file_path in files:
                click.echo(f"   {file_path}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('target_path')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def info(filesystem_path, target_path, output_format):
    """
    Get information about a file in an extracted firmware filesystem
    
    FILESYSTEM_PATH: Path to extracted firmware directory
    TARGET_PATH: Path to file (e.g., /usr/bin/busybox)
    """
    modifier = FirmwareModifier()
    
    try:
        result = modifier.get_file_info(filesystem_path, target_path)
        
        if not result['success']:
            click.echo(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            click.echo(f"📄 File Information: {target_path}")
            click.echo(f"   Exists: {result['exists']}")
            click.echo(f"   Type: {'Directory' if result['is_directory'] else 'File'}")
            click.echo(f"   Size: {result['size']:,} bytes")
            click.echo(f"   Permissions: {result['permissions']}")
            click.echo(f"   Executable: {'Yes' if result['is_executable'] else 'No'}")
            click.echo(f"   Readable: {'Yes' if result['is_readable'] else 'No'}")
            click.echo(f"   Writable: {'Yes' if result['is_writable'] else 'No'}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('output_file', type=click.Path())
@click.option('--filesystem-type', type=click.Choice(['squashfs', 'jffs2', 'ext2', 'ext3', 'ext4', 'cramfs']),
              help='Type of filesystem to create (auto-detected if not specified)')
@click.option('--validate/--no-validate', default=True, help='Validate filesystem before repacking')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def repack(filesystem_path, output_file, filesystem_type, validate, verbose):
    """
    Repack a modified filesystem into a firmware image
    
    FILESYSTEM_PATH: Path to modified filesystem directory
    OUTPUT_FILE: Path for output firmware file
    """
    if verbose:
        click.echo(f"Repacking {filesystem_path} to {output_file}")
    
    repacker = FirmwareRepacker()
    
    try:
        # Convert filesystem type string to enum
        fs_type = None
        if filesystem_type:
            fs_type = FirmwareType(filesystem_type)
        
        # Validate filesystem if requested
        if validate:
            click.echo("🔍 Validating filesystem...")
            validation = repacker.validate_filesystem(filesystem_path)
            
            if not validation['valid']:
                click.echo("❌ Filesystem validation failed:")
                for error in validation['errors']:
                    click.echo(f"   - {error}")
                sys.exit(1)
            
            if validation['warnings']:
                click.echo("⚠️  Validation warnings:")
                for warning in validation['warnings']:
                    click.echo(f"   - {warning}")
            
            click.echo(f"✅ Validation passed: {validation['file_count']} files, {validation['total_size']:,} bytes")
        
        # Get repacking info
        if fs_type:
            repack_info = repacker.get_repacking_info(fs_type)
        else:
            # Auto-detect filesystem type
            fs_type = repacker._detect_filesystem_type_from_dir(filesystem_path)
            repack_info = repacker.get_repacking_info(fs_type)
        
        if not repack_info['repackable']:
            click.echo(f"❌ Cannot repack {fs_type.value} filesystem")
            if repack_info['notes']:
                for note in repack_info['notes']:
                    click.echo(f"   - {note}")
            sys.exit(1)
        
        if verbose:
            click.echo(f"📦 Filesystem type: {fs_type.value}")
            click.echo(f"   Required tools: {', '.join(repack_info['tools_required'])}")
        
        # Perform repacking
        click.echo("🔨 Repacking filesystem...")
        result = repacker.repack_firmware(filesystem_path, output_file, fs_type)
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
            if verbose:
                click.echo(f"   Method: {result['method']}")
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    click.echo(f"   Output size: {file_size:,} bytes")
        else:
            click.echo(f"❌ Repacking failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def validate(filesystem_path, output_format):
    """
    Validate a filesystem directory
    
    FILESYSTEM_PATH: Path to filesystem directory to validate
    """
    repacker = FirmwareRepacker()
    
    try:
        result = repacker.validate_filesystem(filesystem_path)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            click.echo(f"🔍 Filesystem Validation: {filesystem_path}")
            click.echo(f"   Valid: {'Yes' if result['valid'] else 'No'}")
            click.echo(f"   Files: {result['file_count']:,}")
            click.echo(f"   Size: {result['total_size']:,} bytes")
            
            if result['errors']:
                click.echo("❌ Errors:")
                for error in result['errors']:
                    click.echo(f"   - {error}")
            
            if result['warnings']:
                click.echo("⚠️  Warnings:")
                for warning in result['warnings']:
                    click.echo(f"   - {warning}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('output_file', type=click.Path())
@click.option('--original-firmware', '-o', type=click.Path(exists=True), 
              help='Original firmware file for header extraction')
@click.option('--filesystem-type', type=click.Choice(['squashfs', 'jffs2', 'ext2', 'ext3', 'ext4', 'cramfs']),
              help='Type of filesystem to create')
@click.option('--container-format', type=click.Choice(['raw', 'uboot', 'trx']),
              help='Container format for the firmware')
@click.option('--preserve-headers/--no-preserve-headers', default=True,
              help='Preserve original headers and checksums')
@click.option('--validate/--no-validate', default=True, help='Validate before building')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def build(filesystem_path, output_file, original_firmware, filesystem_type, 
          container_format, preserve_headers, validate, verbose):
    """
    Build a complete firmware image with advanced container support
    
    FILESYSTEM_PATH: Path to modified filesystem directory
    OUTPUT_FILE: Path for output firmware file
    """
    if verbose:
        click.echo(f"Building firmware from {filesystem_path} to {output_file}")
    
    builder = FirmwareBuilder()
    
    try:
        # Extract metadata from original firmware if provided
        metadata = None
        if original_firmware:
            if verbose:
                click.echo(f"📋 Extracting metadata from {original_firmware}")
            
            metadata = builder.extract_firmware_metadata(original_firmware)
            if not metadata['success']:
                click.echo(f"⚠️  Warning: Could not extract metadata: {metadata['error']}")
            elif verbose:
                click.echo(f"   Detected container: {metadata.get('container_format', 'unknown')}")
                click.echo(f"   Filesystem type: {metadata.get('detected_type', 'unknown')}")
        
        # Auto-detect container format if not specified
        if not container_format and metadata and metadata['success']:
            container_format = metadata.get('container_format', 'raw')
            if verbose:
                click.echo(f"   Auto-detected container format: {container_format}")
        
        # Auto-detect filesystem type if not specified
        fs_type = None
        if filesystem_type:
            fs_type = FirmwareType(filesystem_type)
        elif metadata and metadata['success']:
            fs_type = metadata.get('detected_type')
        
        # Build the firmware
        if verbose:
            click.echo("🏗️  Building firmware...")
        
        result = builder.build_firmware(
            filesystem_path,
            output_file,
            original_firmware,
            fs_type,
            preserve_headers,
            container_format
        )
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
            
            if verbose:
                click.echo(f"   Filesystem: {result['filesystem_type']}")
                if result.get('container_format'):
                    click.echo(f"   Container: {result['container_format']}")
                
                # Show checksums
                checksums = result.get('checksums', {})
                if checksums:
                    click.echo("   Checksums:")
                    click.echo(f"     MD5:    {checksums.get('md5', 'N/A')}")
                    click.echo(f"     SHA1:   {checksums.get('sha1', 'N/A')}")
                    click.echo(f"     SHA256: {checksums.get('sha256', 'N/A')}")
                    click.echo(f"     Size:   {checksums.get('size', 0):,} bytes")
                
                # Show validation results
                validation = result.get('validation', {})
                if validation:
                    click.echo(f"   Validation: {validation.get('filesystem_type', 'unknown')}")
        else:
            click.echo(f"❌ Build failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def metadata(firmware_path, output_format):
    """
    Extract metadata from a firmware file
    
    FIRMWARE_PATH: Path to firmware file to analyze
    """
    builder = FirmwareBuilder()
    
    try:
        result = builder.extract_firmware_metadata(firmware_path)
        
        if not result['success']:
            click.echo(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            click.echo(f"📋 Firmware Metadata: {firmware_path}")
            click.echo(f"   File Size: {result['file_size']:,} bytes")
            click.echo(f"   Filesystem Type: {result.get('detected_type', 'Unknown')}")
            click.echo(f"   Container Format: {result.get('container_format', 'Unknown')}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
def containers(output_format):
    """Show supported container formats and their availability"""
    builder = FirmwareBuilder()
    
    try:
        containers = builder.get_supported_containers()
        
        if output_format == 'json':
            click.echo(json.dumps(containers, indent=2))
        else:
            click.echo("🏗️  Supported Container Formats:")
            click.echo()
            
            for container in containers:
                status = "✅" if container['supported'] else "❌"
                click.echo(f"{status} {container['format'].upper()}")
                click.echo(f"   Description: {container['description']}")
                if container['tools_required']:
                    click.echo(f"   Tools Required: {', '.join(container['tools_required'])}")
                click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
def tools():
    """Check availability of required extraction, repacking, and building tools"""
    extractor = FirmwareExtractor()
    repacker = FirmwareRepacker()
    builder = FirmwareBuilder()
    
    extraction_tools = [
        'unsquashfs',  # SquashFS
        'jefferson',   # JFFS2
        '7z',          # ext2/3/4, general archive
        'debugfs',     # ext2/3/4
        'cramfsck',    # CramFS
        'ubireader',   # UBIFS
    ]
    
    repacking_tools = [
        'mksquashfs',  # SquashFS
        'mkfs.jffs2',  # JFFS2
        'mkfs.ext2',   # ext2
        'mkcramfs',    # CramFS
        'tar',         # Fallback for ext filesystems
    ]
    
    building_tools = [
        'mkimage',     # U-Boot image creation
    ]
    
    click.echo("🔧 Checking extraction tools availability:")
    click.echo()
    
    available_extraction = []
    missing_extraction = []
    
    for tool in extraction_tools:
        if extractor._check_tool_available(tool):
            click.echo(f"✅ {tool}")
            available_extraction.append(tool)
        else:
            click.echo(f"❌ {tool}")
            missing_extraction.append(tool)
    
    click.echo()
    click.echo("🔨 Checking repacking tools availability:")
    click.echo()
    
    available_repacking = []
    missing_repacking = []
    
    for tool in repacking_tools:
        if repacker._check_tool_available(tool):
            click.echo(f"✅ {tool}")
            available_repacking.append(tool)
        else:
            click.echo(f"❌ {tool}")
            missing_repacking.append(tool)
    
    click.echo()
    click.echo("🏗️  Checking building tools availability:")
    click.echo()
    
    available_building = []
    missing_building = []
    
    for tool in building_tools:
        if builder._check_tool_available(tool):
            click.echo(f"✅ {tool}")
            available_building.append(tool)
        else:
            click.echo(f"❌ {tool}")
            missing_building.append(tool)
    
    click.echo()
    click.echo(f"Extraction: {len(available_extraction)}/{len(extraction_tools)} tools")
    click.echo(f"Repacking: {len(available_repacking)}/{len(repacking_tools)} tools")
    click.echo(f"Building: {len(available_building)}/{len(building_tools)} tools")
    
    if missing_extraction or missing_repacking or missing_building:
        click.echo(f"\nMissing tools:")
        if missing_extraction:
            click.echo(f"  Extraction: {', '.join(missing_extraction)}")
        if missing_repacking:
            click.echo(f"  Repacking: {', '.join(missing_repacking)}")
        if missing_building:
            click.echo(f"  Building: {', '.join(missing_building)}")
        click.echo("\nInstallation instructions:")
        click.echo("  macOS: brew install squashfs-tools jefferson p7zip e2fsprogs cramfsprogs ubi_reader mtd-utils u-boot-tools")
        click.echo("  Ubuntu: sudo apt install squashfs-tools jefferson p7zip-full e2fsprogs cramfsprogs ubi-utils mtd-utils u-boot-tools")


# Add emulator commands to main CLI
main.add_command(emulator)

if __name__ == '__main__':
    main()


@main.command()
@click.argument('firmware_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--fuzz-type', type=click.Choice(['random', 'bitflip', 'magic', 'boundary']), 
              default='random', help='Type of fuzzing to perform')
@click.option('--iterations', '-i', default=100, help='Number of fuzzing iterations')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def fuzz(firmware_path, output_dir, fuzz_type, iterations, verbose):
    """
    Fuzz a firmware file for vulnerability discovery
    
    FIRMWARE_PATH: Path to firmware file to fuzz
    OUTPUT_DIR: Directory to save fuzzed files
    """
    from .fuzzer import FirmwareFuzzer
    
    if verbose:
        click.echo(f"Fuzzing {firmware_path} with {fuzz_type} fuzzing...")
    
    fuzzer = FirmwareFuzzer()
    
    try:
        result = fuzzer.fuzz_firmware_file(firmware_path, output_dir, fuzz_type, iterations)
        
        if result['success']:
            click.echo(f"✅ Fuzzing complete!")
            click.echo(f"   Fuzzed files: {len(result['fuzzed_files'])}")
            click.echo(f"   Crashes found: {len(result['crashes'])}")
            click.echo(f"   Unique crashes: {result['unique_crashes']}")
            
            if verbose and result['crashes']:
                click.echo("\n🚨 Crashes found:")
                for crash in result['crashes'][:5]:  # Show first 5 crashes
                    click.echo(f"   - {crash['file_path']}: {crash['crash_type']}")
        else:
            click.echo(f"❌ Fuzzing failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('filesystem_path', type=click.Path(exists=True, file_okay=False))
@click.argument('output_dir', type=click.Path())
@click.option('--fuzz-type', type=click.Choice(['file_content', 'permissions', 'names']), 
              default='file_content', help='Type of filesystem fuzzing')
@click.option('--iterations', '-i', default=50, help='Number of fuzzing iterations')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def fuzz_fs(filesystem_path, output_dir, fuzz_type, iterations, verbose):
    """
    Fuzz an extracted filesystem for vulnerability discovery
    
    FILESYSTEM_PATH: Path to extracted filesystem directory
    OUTPUT_DIR: Directory to save fuzzed filesystems
    """
    from .fuzzer import FirmwareFuzzer
    
    if verbose:
        click.echo(f"Fuzzing filesystem {filesystem_path} with {fuzz_type} fuzzing...")
    
    fuzzer = FirmwareFuzzer()
    
    try:
        result = fuzzer.fuzz_filesystem(filesystem_path, output_dir, fuzz_type, iterations)
        
        if result['success']:
            click.echo(f"✅ Filesystem fuzzing complete!")
            click.echo(f"   Fuzzed filesystems: {iterations}")
            click.echo(f"   Crashes found: {len(result['crashes'])}")
            
            if verbose and result['crashes']:
                click.echo("\n🚨 Filesystem crashes found:")
                for crash in result['crashes'][:5]:
                    click.echo(f"   - {crash['fs_dir']}: {', '.join(crash['issues'])}")
        else:
            click.echo(f"❌ Fuzzing failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
def fuzz_stats():
    """Show fuzzing statistics"""
    from .fuzzer import FirmwareFuzzer
    
    fuzzer = FirmwareFuzzer()
    stats = fuzzer.get_fuzzing_stats()
    
    click.echo("📊 Fuzzing Statistics:")
    click.echo(f"   Total fuzz operations: {stats['total_fuzz_count']}")
    click.echo(f"   Crashes found: {stats['crashes_found']}")
    click.echo(f"   Unique crashes: {stats['unique_crashes']}")
    click.echo(f"   Crash rate: {stats['crash_rate']:.2%}")
