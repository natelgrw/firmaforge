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

def extract_default_credentials(rootfs_dir: Path) -> List[Dict[str, str]]:
    """Extracts default credentials from configuration files."""
    creds = []
    config_dir = rootfs_dir / "etc" / "config"
    if not config_dir.exists():
        return creds

    # check common config files
    for config_file in ["dropbear", "uhttpd", "system", "lucid"]:
        path = config_dir / config_file
        if path.exists():
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    # simple extraction for 'option password' or 'option username'
                    usernames = re.findall(r"option\s+username\s+['\"]?([^'\"\s]+)['\"]?", content)
                    passwords = re.findall(r"option\s+password\s+['\"]?([^'\"\s]+)['\"]?", content)
                    
                    for i in range(max(len(usernames), len(passwords))):
                        entry = {"source": config_file}
                        if i < len(usernames): entry["username"] = usernames[i]
                        if i < len(passwords):
                            pwd = passwords[i]
                            # omit placeholder password but keep entry
                            if pwd != "plaintext_or_md5_or_$p$user_for_system_user":
                                entry["password"] = pwd
                        
                        if len(entry) > 1: # more than just 'source'
                            creds.append(entry)
            except Exception:
                continue
    return creds

def extract_startup_services(rootfs_dir: Path) -> List[Dict[str, Any]]:
    """Extracts startup services and their priorities from /etc/init.d/."""
    services = []
    init_d = rootfs_dir / "etc" / "init.d"
    if not init_d.exists():
        return services

    for service_file in init_d.iterdir():
        if service_file.is_file() and not service_file.is_symlink():
            try:
                with open(service_file, 'r') as f:
                    content = f.read()
                    start = re.search(r"START=(\d+)", content)
                    stop = re.search(r"STOP=(\d+)", content)
                    services.append({
                        "name": service_file.name,
                        "start": int(start.group(1)) if start else None,
                        "stop": int(stop.group(1)) if stop else None
                    })
            except Exception:
                continue
    return sorted(services, key=lambda x: x['start'] if x['start'] is not None else 999)

def extract_firewall_rules(rootfs_dir: Path) -> Dict[str, Any]:
    """Extracts detailed firewall rules and redirects from /etc/config/firewall."""
    summary = {"rules": [], "redirects": [], "zones": []}
    firewall_config = rootfs_dir / "etc" / "config" / "firewall"
    if not firewall_config.exists():
        return summary

    try:
        with open(firewall_config, 'r') as f:
            content = f.read()
            
            # parse zones
            zones = re.findall(r"config\s+zone\s+(.*?)(?=config|$)", content, re.DOTALL)
            for z in zones:
                name = re.search(r"option\s+name\s+['\"]?([^'\"\s]+)['\"]?", z)
                if name: summary["zones"].append(name.group(1))
            
            # parse rules
            rules = re.findall(r"config\s+rule\s+(.*?)(?=config|$)", content, re.DOTALL)
            for r in rules:
                rule_info = {}
                name = re.search(r"option\s+name\s+['\"]?([^'\"\s]+)['\"]?", r)
                proto = re.search(r"option\s+proto\s+['\"]?([^'\"\s]+)['\"]?", r)
                src = re.search(r"option\s+src\s+['\"]?([^'\"\s]+)['\"]?", r)
                dest = re.search(r"option\s+dest\s+['\"]?([^'\"\s]+)['\"]?", r)
                target = re.search(r"option\s+target\s+['\"]?([^'\"\s]+)['\"]?", r)
                dest_port = re.search(r"option\s+dest_port\s+['\"]?([^'\"\s]+)['\"]?", r)
                
                if name: rule_info["name"] = name.group(1)
                if proto: rule_info["proto"] = proto.group(1)
                if src: rule_info["src"] = src.group(1)
                if dest: rule_info["dest"] = dest.group(1)
                if target: rule_info["target"] = target.group(1)
                if dest_port: rule_info["dest_port"] = dest_port.group(1)
                
                if rule_info: summary["rules"].append(rule_info)
                
            # parse redirects
            redirects = re.findall(r"config\s+redirect\s+(.*?)(?=config|$)", content, re.DOTALL)
            for rd in redirects:
                rd_info = {}
                name = re.search(r"option\s+name\s+['\"]?([^'\"\s]+)['\"]?", rd)
                src_dport = re.search(r"option\s+src_dport\s+['\"]?([^'\"\s]+)['\"]?", rd)
                dest_ip = re.search(r"option\s+dest_ip\s+['\"]?([^'\"\s]+)['\"]?", rd)
                dest_port = re.search(r"option\s+dest_port\s+['\"]?([^'\"\s]+)['\"]?", rd)
                
                if name: rd_info["name"] = name.group(1)
                if src_dport: rd_info["src_dport"] = src_dport.group(1)
                if dest_ip: rd_info["dest_ip"] = dest_ip.group(1)
                if dest_port: rd_info["dest_port"] = dest_port.group(1)
                
                if rd_info: summary["redirects"].append(rd_info)

    except Exception:
        pass
    return summary

def extract_init_scripts_data(rootfs_dir: Path) -> List[str]:
    """Briefly lists scripts in /etc/rc.d/ for boot sequence insight."""
    rc_d = rootfs_dir / "etc" / "rc.d"
    if not rc_d.exists():
        return []
    return sorted([f.name for f in rc_d.iterdir() if f.is_file() or f.is_symlink()])

def analyze_elves(rootfs_dir: Path) -> List[Dict[str, Any]]:
    """Analyzes ELF binaries in the rootfs for arch, bitness, libs, and dangerous functions."""
    elf_results = []
    dangerous_functions = ["strcpy", "sprintf", "system", "popen", "gets", "strcat", "scanf"]
    
    # helper to check if a file is an ELF
    def is_elf(file_path):
        try:
            with open(file_path, "rb") as f:
                return f.read(4) == b"\x7fELF"
        except Exception:
            return False

    elf_files = []
    if rootfs_dir.exists():
        for root, dirs, files in os.walk(rootfs_dir):
            for file in files:
                full_path = Path(root) / file
                if not full_path.is_symlink() and is_elf(full_path):
                    elf_files.append(full_path)
    
    # limit to most relevant binaries to keep summary concise
    # prioritizes those in bin/ sbin/
    priority_elves = [e for e in elf_files if any(p in str(e) for p in ["/bin/", "/sbin/"])]
    target_list = (priority_elves + elf_files)[:50] # analyze up to 50 elves
    
    for elf_path in target_list:
        try:
            with open(elf_path, "rb") as f:
                header = f.read(64)
                if len(header) < 54: continue
                
                # Bitness: 1=32bit, 2=64bit
                bitness = "32-bit" if header[4] == 1 else "64-bit" if header[4] == 2 else "unknown"
                
                # Architecture (approximate Machine field at 0x12)
                # machine = int.from_bytes(header[18:20], byteorder='little') # need to handle endianness
                # For simplicity and robustness, we use strings for more detailed info
                
                content = header + f.read(5 * 1024 * 1024) # read up to 5MB for string analysis
                content_str = content.decode(errors="ignore")
                
                # Linking
                linking = "dynamic" if "/lib/ld-" in content_str or "lib" in content_str else "static"
                
                # Libraries
                libs = sorted(list(set(re.findall(r"lib[a-zA-Z0-9._-]+\.so\.[0-9.]*", content_str))))
                
                # Dangerous functions
                found_dangerous = [func for func in dangerous_functions if func in content_str]
                
                # Security indicators
                rpath = "detected" if "RPATH" in content_str or "RUNPATH" in content_str else "none"
                rwx = "possibly detected" if "RWX" in content_str else "none" # very rough heuristic

                elf_results.append({
                    "file": str(elf_path.relative_to(rootfs_dir)),
                    "bitness": bitness,
                    "linking": linking,
                    "libraries": libs[:10], # top 10 libs
                    "dangerous_functions": found_dangerous,
                    "security": {
                        "rpath": rpath,
                        "rwx_segments": rwx
                    }
                })
        except Exception:
            continue
            
    return elf_results

def extract_secrets(rootfs_dir: Path) -> Dict[str, Any]:
    """Scans for secrets, keys, and certificates in the rootfs with professional categorization."""
    results = {
        "summary": {
            "hardcoded_passwords": 0,
            "private_keys": 0,
            "api_tokens": 0,
            "public_certificates": 0
        },
        "findings": []
    }
    
    # Exclude logic/handling patterns
    false_positive_words = ["randomid", "checkpassword", "validate", "generate", "override_token", "rollback_token", "csrf"]
    
    patterns = {
        "Private Key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "Public Certificate": re.compile(r"-----BEGIN CERTIFICATE-----"),
        "Public Key": re.compile(r"-----BEGIN PUBLIC KEY-----"),
        "AWS API Key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "Hardcoded Password": re.compile(r"(password|secret|apikey|token|auth_token)\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]", re.IGNORECASE)
    }
    
    sensitive_extensions = {".pem", ".key", ".crt", ".p12", ".pfx"}

    if not rootfs_dir.exists():
        return results

    for root, dirs, files in os.walk(rootfs_dir):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(rootfs_dir)
            
            # skip noise
            if any(p in str(rel_path) for p in ["/lib/", "/usr/lib/"]) or full_path.suffix in [".so", ".bin"]:
                continue

            # scan content
            try:
                if full_path.stat().st_size > 512 * 1024: continue
                with open(full_path, "r", errors="ignore") as f:
                    content = f.read()
                    
                    found_in_file = False
                    for s_type, pattern in patterns.items():
                        matches = pattern.finditer(content)
                        for match in matches:
                            snippet = content[max(0, match.start()-20) : min(len(content), match.end()+20)].strip().replace("\n", " ")
                            
                            finding = {
                                "type": s_type,
                                "file": str(rel_path),
                                "context": f"... {snippet} ..."
                            }

                            # Apply professional logic
                            lower_snippet = snippet.lower()
                            if any(fp in lower_snippet for fp in false_positive_words):
                                continue
                            elif s_type == "Private Key":
                                finding["confidence"] = "high"
                                finding["impact"] = "Direct access to encrypted material or secure communications"
                                results["summary"]["private_keys"] += 1
                            elif s_type in ["Public Certificate", "Public Key"]:
                                finding["confidence"] = "informational"
                                finding["note"] = "Expected public cryptographic asset"
                                results["summary"]["public_certificates"] += 1
                            elif s_type == "Hardcoded Password":
                                # distinguish between real passwords and config/scripts
                                if any(x in lower_snippet for x in ["password='password'", "password: 'password'"]):
                                    finding["confidence"] = "high"
                                    finding["impact"] = "Default credentials enable trivial unauthorized access"
                                    results["summary"]["hardcoded_passwords"] += 1
                                else:
                                    continue
                            elif s_type == "AWS API Key":
                                finding["confidence"] = "high"
                                finding["impact"] = "Direct access to cloud infrastructure"
                                results["summary"]["api_tokens"] += 1
                            
                            results["findings"].append(finding)
                            found_in_file = True
                            if results["summary"]["hardcoded_passwords"] + results["summary"]["private_keys"] > 100: break # safety break
                        if found_in_file: break

            except Exception:
                continue

    return results["summary"]

def analyze_web_security(rootfs_dir: Path) -> Dict[str, Any]:
    """Scans for command injections and insecure web endpoints."""
    web_results = {
        "summary": {
            "command_injections": 0,
            "insecure_endpoints": 0,
            "unsafe_scripts": 0
        },
        "findings": []
    }
    
    target_dirs = ["www", "cgi-bin", "usr/lib/lua", "usr/www", "usr/share/ucode", "usr/share/rpcd", "usr/libexec"]
    
    # regex for command injection sinks
    # LUA/ucode/Shell injection patterns
    injection_patterns = {
        "Script Command Injection": re.compile(r"(os\.execute|io\.popen|sys\.exec|sys\.call|system|popen|exec)\s*\(.*[a-zA-Z_0-9]+.*\)"),
        "Shell Backtick/Subshell": re.compile(r"(`|\$\()(.*\$[a-zA-Z_0-9]+.*)(\)|`)"),
    }
    
    endpoint_patterns = {
        "Insecure Endpoint Definition": re.compile(r"(entry|action)\s*\(\s*\{.*\},\s*.*,\s*nil\s*[,\)]"),
        "Unvalidated Parameter Access": re.compile(r"(request\.params|request\.form|request\.query|ctx\.params|params)\[['\"].*['\"]\]"),
    }

    if not rootfs_dir.exists():
        return web_results

    def is_binary(file_path):
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk: return True
                # also check for high binary ratio
                if len(chunk) > 0:
                    non_text = sum(1 for b in chunk if b < 32 and b not in [9, 10, 13])
                    if non_text / len(chunk) > 0.3: return True
                return False
        except Exception:
            return True

    for t_dir in target_dirs:
        abs_t_dir = rootfs_dir / t_dir
        if not abs_t_dir.exists(): continue
        
        for root, dirs, files in os.walk(abs_t_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(rootfs_dir)
                
                # skip known binary/media
                if full_path.suffix.lower() in [".so", ".bin", ".png", ".jpg", ".jpeg", ".css", ".js", ".gif"]:
                    continue

                if is_binary(full_path):
                    continue

                try:
                    if full_path.stat().st_size > 512 * 1024: continue
                    with open(full_path, "r", errors="ignore") as f:
                        content = f.read()
                        
                        # filter: only scan if it looks like a script or logic
                        lower_content = content.lower()
                        is_likely_script = full_path.suffix.lower() in [".lua", ".sh", ".cgi", ".php", ".py", ".pl", ".uc"] or \
                                          content.startswith("#!") or \
                                          any(x in lower_content for x in ["function", "module", "require", "import", "local"])
                        
                        if not is_likely_script:
                            continue

                        # Check injections
                        found_vulnerabilities = False
                        for name, pattern in injection_patterns.items():
                            matches = pattern.finditer(content)
                            for match in matches:
                                snippet = content[max(0, match.start()-30) : min(len(content), match.end()+30)].strip().replace("\n", " ")
                                web_results["findings"].append({
                                    "type": "Command Injection Sink",
                                    "file": str(rel_path),
                                    "context": f"... {snippet} ...",
                                    "confidence": "high"
                                })
                                web_results["summary"]["command_injections"] += 1
                                found_vulnerabilities = True
                        
                        # Check endpoints
                        for name, pattern in endpoint_patterns.items():
                            matches = pattern.finditer(content)
                            for match in matches:
                                snippet = content[max(0, match.start()-30) : min(len(content), match.end()+30)].strip().replace("\n", " ")
                                web_results["findings"].append({
                                    "type": "Insecure Web Pattern",
                                    "file": str(rel_path),
                                    "context": f"... {snippet} ...",
                                    "confidence": "medium"
                                })
                                if "Endpoint" in name:
                                    web_results["summary"]["insecure_endpoints"] += 1
                                else:
                                    web_results["summary"]["unsafe_scripts"] += 1
                                found_vulnerabilities = True

                except Exception:
                    continue

    return web_results

def analyze_static(firmware_result_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Analyzes extracted firmware for various static details.
    """
    firmware_dir = Path(firmware_result_dir)
    rootfs_dir = firmware_dir / "raw_extracts" / "rootfs"
    
    results = {}
    
    # 1. User analysis (merged from old analyze_users)
    user_results = _analyze_users_internal(firmware_dir, rootfs_dir)
    results["users"] = user_results
    
    # 2. Advanced extractions
    if rootfs_dir.exists():
        results["default_credentials"] = extract_default_credentials(rootfs_dir)
        results["startup_services"] = extract_startup_services(rootfs_dir)
        results["firewall_summary"] = extract_firewall_rules(rootfs_dir)
        results["init_scripts"] = extract_init_scripts_data(rootfs_dir)

    if output_path:
        try:
            data = {}
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    data = json.load(f)
            
            data['static_analysis'] = {
                "login_capable_users": user_results["login_capable_users"],
                "users": user_results["users_list"],
                "default_credentials": results.get("default_credentials", []),
                "startup_services": results.get("startup_services", []), 
                "firewall": results.get("firewall_summary", {}),
                "init_scripts": results.get("init_scripts", []),
                "elf_analysis": analyze_elves(rootfs_dir) if rootfs_dir.exists() else [],
                "secrets_analysis": extract_secrets(rootfs_dir) if rootfs_dir.exists() else {},
                "web_security": analyze_web_security(rootfs_dir) if rootfs_dir.exists() else {}
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error updating JSON {output_path}: {e}")
            
    return results

def _analyze_users_internal(firmware_dir: Path, rootfs_dir: Path) -> Dict[str, Any]:
    """Internal helper for user analysis logic."""
    
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
    simplified_users = []

    for user in users_list:
        username = user.get('username')
        uid_str = user.get('uid', '-1')
        uid = int(uid_str) if uid_str.isdigit() else -1
        
        shell = user.get('shell', '')
        pwd_hash = user.get('password_hash', '')
        
        has_valid_password_hash = False
        if pwd_hash and pwd_hash not in ['*', '!', '!!', 'x']:
             has_valid_password_hash = True
        
        if shell and not shell.endswith('false') and not shell.endswith('nologin'):
            login_capable_users.append(username)

        simplified_users.append({
            "username": username,
            "uid": uid,
            "shell": shell,
            "has_valid_password_hash": has_valid_password_hash
        })

    return {
        "total_users": total_users,
        "login_capable_users": sorted(list(set(login_capable_users))),
        "users_list": simplified_users
    }

def analyze_users(firmware_result_dir: str, output_path: str) -> Dict[str, Any]:
    """Legacy wrapper for compatibility."""
    return analyze_static(firmware_result_dir, output_path)
