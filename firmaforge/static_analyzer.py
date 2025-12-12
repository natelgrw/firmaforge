"""
static_analyzer.py

Author: @natelgrw
Last Edited: 12/09/2025

A module that performs static analysis on extracted firmware files,
specifically targeting user account information from /etc/passwd and /etc/shadow.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

def analyze_users(firmware_result_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Analyzes extracted firmware for user account information.
    
    Args:
        firmware_result_dir: Path to the firmware result directory containing 'raw_extracts'
        output_path: Path to the existing analysis JSON file to update
        
    Returns:
        Dictionary containing the user analysis results
    """
    firmware_dir = Path(firmware_result_dir)
    rootfs_dir = firmware_dir / "raw_extracts" / "rootfs"
    
    users_data = {}
    passwd_files = []
    shadow_files = []
    warnings = []
    passwd_users = []
    shadow_users = []
    
    # regex patterns for deep scan
    passwd_pattern = re.compile(r'^([a-zA-Z0-9._-]+):([^:]*):(\d+):(\d+):([^:]*):([^:]*):([^:]*)$')
    shadow_pattern = re.compile(r'^([a-zA-Z0-9._-]+):([^:]+):(\d*):(\d*):(\d*):(\d*):(\d*):(\d*):(\d*)$')

    # find all passwd and shadow files
    if rootfs_dir.exists():
        passwd_files = list(rootfs_dir.rglob("etc/passwd"))
        shadow_files = list(rootfs_dir.rglob("etc/shadow"))
        
        # explicit check in etc directories to catch broken symlinks
        for etc_dir in rootfs_dir.rglob("etc"):
            if etc_dir.is_dir():
                p_file = etc_dir / "passwd"
                s_file = etc_dir / "shadow"
                
                if (p_file.is_symlink() or p_file.exists()) and p_file not in passwd_files:
                    passwd_files.append(p_file)
                
                if (s_file.is_symlink() or s_file.exists()) and s_file not in shadow_files:
                    shadow_files.append(s_file)
    
    # parse passwd files
    parsed_users = {}
    for passwd_file in passwd_files:
        try:
            with open(passwd_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        passwd_users.append(username)
                        parsed_users[username] = {
                            'username': username,
                            'password_placeholder': parts[1],
                            'uid': parts[2],
                            'gid': parts[3],
                            'gecos': parts[4],
                            'home': parts[5],
                            'shell': parts[6],
                            'source_passwd': str(passwd_file.relative_to(firmware_dir))
                        }
        except Exception as e:
            msg = f"Error reading passwd file {passwd_file}: {e}"
            print(msg)
            warnings.append(msg)

    # parse shadow files and merge
    for shadow_file in shadow_files:
        try:
            with open(shadow_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split(':')
                    if len(parts) >= 2:
                        username = parts[0]
                        shadow_users.append(username)
                        password_hash = parts[1]
                        
                        if username in parsed_users:
                            parsed_users[username]['password_hash'] = password_hash
                            parsed_users[username]['source_shadow'] = str(shadow_file.relative_to(firmware_dir))
                            
                            # identify hash type
                            hash_type = "unknown"
                            if password_hash.startswith('$1$'):
                                hash_type = "MD5"
                            elif password_hash.startswith('$2a$') or password_hash.startswith('$2y$'):
                                hash_type = "Blowfish"
                            elif password_hash.startswith('$5$'):
                                hash_type = "SHA-256"
                            elif password_hash.startswith('$6$'):
                                hash_type = "SHA-512"
                            elif len(password_hash) == 13 and password_hash not in ['*', '!', '!!']:
                                hash_type = "DES"
                            elif password_hash in ['*', '!', '!!']:
                                hash_type = "locked/disabled"
                            
                            parsed_users[username]['hash_type'] = hash_type
                            
                            shadow_fields = ['lastchg', 'min', 'max', 'warn', 'inactive', 'expire']
                            for i, field in enumerate(shadow_fields):
                                if len(parts) > i + 2:
                                    parsed_users[username][field] = parts[i+2]

        except Exception as e:
            msg = f"Error reading shadow file {shadow_file}: {e}"
            print(msg)
            warnings.append(msg)

    # deep scan for hidden credentials
    if rootfs_dir.exists():
        print("Starting deep scan for credentials...")
        for file_path in rootfs_dir.rglob("*"):
            if not file_path.is_file() or file_path.is_symlink():
                continue
            if file_path in passwd_files or file_path in shadow_files:
                continue
            
            if file_path.stat().st_size > 1024 * 1024:
                continue

            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                    
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        pmatch = passwd_pattern.match(line)
                        if pmatch:
                            username = pmatch.group(1)
                            if username not in parsed_users:
                                print(f"Deep scan found user in {file_path.name}: {username}")
                                passwd_users.append(username)
                                parsed_users[username] = {
                                    'username': username,
                                    'password_placeholder': pmatch.group(2),
                                    'uid': pmatch.group(3),
                                    'gid': pmatch.group(4),
                                    'gecos': pmatch.group(5),
                                    'home': pmatch.group(6),
                                    'shell': pmatch.group(7),
                                    'source_passwd': str(file_path.relative_to(firmware_dir)) + " (deep_scan)"
                                }
                        
                        smatch = shadow_pattern.match(line)
                        if smatch:
                            username = smatch.group(1)
                            password_hash = smatch.group(2)
                            
                            if username not in parsed_users:
                                shadow_users.append(username)
                                parsed_users[username] = {'username': username}
                            
                            if 'password_hash' not in parsed_users[username]:
                                parsed_users[username]['password_hash'] = password_hash
                                parsed_users[username]['source_shadow'] = str(file_path.relative_to(firmware_dir)) + " (deep_scan)"
                                
                                # Identify hash type (reused logic)
                                hash_type = "unknown"
                                if password_hash.startswith('$1$'): hash_type = "MD5"
                                elif password_hash.startswith('$2a$') or password_hash.startswith('$2y$'): hash_type = "Blowfish"
                                elif password_hash.startswith('$5$'): hash_type = "SHA-256"
                                elif password_hash.startswith('$6$'): hash_type = "SHA-512"
                                elif len(password_hash) == 13 and password_hash != '*' and password_hash != '!' and password_hash != '!!': hash_type = "DES"
                                elif password_hash in ['*', '!', '!!']: hash_type = "locked/disabled"
                                parsed_users[username]['hash_type'] = hash_type

            except Exception:
                continue
            
    # convert to list for output
    users_list = list(parsed_users.values())
    
    total_users = len(users_list)
    login_capable_users = []
    system_users = []
    disabled_or_placeholder_passwords = []
    simplified_users = []

    for user in users_list:
        username = user.get('username')
        uid_str = user.get('uid', '-1')
        uid = int(uid_str) if uid_str.isdigit() else -1
        
        shell = user.get('shell', '')
        pwd_hash = user.get('password_hash', '')
        placeholder = user.get('password_placeholder', '')
        
        has_valid_password_hash = False
        if pwd_hash and pwd_hash not in ['*', '!', '!!', 'x']:
             has_valid_password_hash = True
        
        is_login_capable = False
        if shell and not shell.endswith('false') and not shell.endswith('nologin'):
            is_login_capable = True
            login_capable_users.append(username)

        simplified_users.append({
            "username": username,
            "uid": uid,
            "shell": shell,
            "has_valid_password_hash": has_valid_password_hash
        })

    if output_path:
        try:
            data = {}
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    data = json.load(f)
            
            data['static_analysis'] = {
                "total_users": total_users,
                "login_capable_users": sorted(list(set(login_capable_users))),
                "users": simplified_users
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error updating JSON {output_path}: {e}")
            
    return users_data
