"""
summarize_results.py

Author: @natelgrw
Last Edited: 11/30/2025

A module that generates JSON output from firmware detection results.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from .detector import FirmwareDetector
from .extractor import FirmwareExtractor


def analyze_firmware(firmware_path: str, output_path: Optional[str] = None, extract_first: bool = True, results_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze firmware and return comprehensive results.
    
    Args:
        firmware_path: Path to firmware file
        output_path: Optional path to save JSON output
        extract_first: If True, extract firmware first then analyze extracted files
        results_dir: Optional results directory
    
    Returns:
        Dictionary containing all analysis results
    """
    firmware_path_obj = Path(firmware_path)
    firmware_name = firmware_path_obj.stem
    
    # determine results directory
    if results_dir is None:
        results_dir = firmware_path_obj.parent / "results"
    else:
        results_dir = Path(results_dir)
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # create firmware-specific directory
    firmware_result_dir = results_dir / firmware_name
    firmware_result_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_dir = None
    
    # 1: extract firmware if requested
    if extract_first:
        try:
            extractor = FirmwareExtractor(firmware_path, str(firmware_result_dir))
            extraction_results = extractor.extract_all()
            extracted_dir = extraction_results['output_directory']
        except Exception as e:
            import traceback
            traceback.print_exc()
    else:
        raw_extracts_dir = firmware_result_dir / "raw_extracts"
        if raw_extracts_dir.exists() and (raw_extracts_dir / "kernel").exists() or (raw_extracts_dir / "rootfs").exists():
            extracted_dir = str(firmware_result_dir)
    
    # 2: analyze with extracted files if available
    detector = FirmwareDetector(firmware_path, extracted_dir)
    results = detector.detect_all()
    
    # 3: create concise summary structure
    file_info = results.get('file_info', {})
    arch_results = results.get('architecture', {})
    
    summary = {
        'firmware_file': firmware_path_obj.name,  # Just filename, not full path
        'extracted_directory': str(extracted_dir) if extracted_dir else None,
        'file_info': {
            'size': file_info.get('size', 0),
            'file_type': file_info.get('file_type', 'unknown'),
        },
        'encryption_check': {
            'possibly_encrypted': results.get('encryption_check', {}).get('possibly_encrypted', False),
            'entropy': results.get('encryption_check', {}).get('entropy', 0),
        },
        'architecture': {
            'detected': arch_results.get('detected', ['unknown']),
            'confidence': arch_results.get('confidence', 'low'),
            'method': arch_results.get('method', 'unknown'),
        },
        'endianness': {
            'detected': results.get('endianness', {}).get('detected', ['unknown']),
            'confidence': results.get('endianness', {}).get('confidence', 'low'),
        },
        'container_formats': results.get('container_formats', []),
        'filesystem_types': results.get('filesystem_types', []),  # Already deduplicated in detector
        'bootloader_segments': results.get('bootloader_segments', []),
        'compression': results.get('compression', []),
        'binwalk_analysis': results.get('binwalk_analysis', {}),
    }
    
    # determine output path to save JSON in firmware result directory
    if output_path is None:
        output_path = str(firmware_result_dir / f"{firmware_name}_analysis.json")
    
    # ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # save to JSON file
    try:
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    except Exception as e:
        print(f"ERROR: Failed to save JSON to {output_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return summary


def load_analysis(json_path: str) -> Dict[str, Any]:
    """
    Load previously saved analysis results.
    
    Args:
        json_path: Path to JSON analysis file
    
    Returns:
        Dictionary containing analysis results
    """
    with open(json_path, 'r') as f:
        return json.load(f)
