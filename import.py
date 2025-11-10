#!/usr/bin/env python3
"""
Generate a valid Uptime Kuma backup.json with:
 • Optional groups (parent/childrenIDs)
 • Correct tag objects with consistent colors
 • Safe overwrite and auto-naming logic
 • File or inline host input
 • Schema verified against Kuma 1.23.17 exports
"""

import argparse
import json
import os
import re
import hashlib
import colorsys
from typing import List, Dict


# ---------------- Utility functions ----------------

def read_hosts(path: str) -> List[str]:
    """Read hostnames from file, stripping blanks."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def normalize_tags(tags: List[str]) -> List[str]:
    """Flatten, deduplicate, and sort tag names."""
    flat = []
    for t in tags:
        flat.extend([s.strip() for s in t.split(",") if s.strip()])
    seen, out = set(), []
    for t in flat:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return sorted(out, key=str.lower)


def clean_domain(url: str) -> str:
    """Normalize and return full domain name."""
    if not re.match(r"^https?://", url):
        url = f"https://{url}"
    return re.sub(r"^https?://", "", url).split("/")[0]


def load_backup(path: str) -> Dict:
    """Load existing backup.json or start a new one."""
    if not os.path.exists(path):
        return {"version": "1.23.17", "notificationList": [], "monitorList": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "monitorList" not in data:
            raise ValueError
        return data
    except Exception:
        print("⚠️ Existing backup invalid — creating new file.")
        return {"version": "1.23.17", "notificationList": [], "monitorList": []}


def next_id(monitors: List[Dict]) -> int:
    """Return the next available monitor ID."""
    return (max((m["id"] for m in monitors), default=0) + 1)


# ---------------- Tag helpers ----------------

def tag_color_for_name(name: str) -> str:
    """Stable bright color based on tag name hash."""
    h = int(hashlib.sha1(name.lower().encode()).hexdigest(), 16)
    hue = h % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360, 0.55, 0.8)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def make_tag(tag_counter: int, monitor_id: int, name: str) -> Dict:
    """Return a proper Uptime Kuma tag object."""
    return {
        "id": tag_counter,
        "monitor_id": monitor_id,
        "tag_id": tag_counter,
        "value": "",
        "name": name,
        "color": tag_color_for_name(name),
    }


# ---------------- Monitor + Group builders ----------------

def make_group(group_id: int, name: str) -> Dict:
    """Create a valid group entry."""
    return {
        "id": group_id,
        "name": name,
        "description": None,
        "pathName": name,
        "parent": None,
        "childrenIDs": [],
        "url": "https://",
        "method": "GET",
        "hostname": None,
        "port": None,
        "maxretries": 0,
        "weight": 2000,
        "active": True,
        "forceInactive": False,
        "type": "group",
        "timeout": 48,
        "interval": 60,
        "retryInterval": 60,
        "resendInterval": 0,
        "keyword": None,
        "invertKeyword": False,
        "expiryNotification": False,
        "ignoreTls": False,
        "upsideDown": False,
        "packetSize": 56,
        "maxredirects": 10,
        "accepted_statuscodes": ["200-299"],
        "dns_resolve_type": "A",
        "dns_resolve_server": "1.1.1.1",
        "dns_last_result": None,
        "docker_container": "",
        "docker_host": None,
        "proxyId": None,
        "notificationIDList": {},
        "tags": [],
        "maintenance": False,
        "mqttTopic": "",
        "mqttSuccessMessage": "",
        "databaseQuery": None,
        "authMethod": None,
        "grpcUrl": None,
        "grpcProtobuf": None,
        "grpcMethod": None,
        "grpcServiceName": None,
        "grpcEnableTls": False,
        "radiusCalledStationId": None,
        "radiusCallingStationId": None,
        "game": None,
        "gamedigGivenPortOnly": True,
        "httpBodyEncoding": "json",
        "jsonPath": None,
        "expectedValue": None,
        "kafkaProducerTopic": None,
        "kafkaProducerBrokers": [],
        "kafkaProducerSsl": False,
        "kafkaProducerAllowAutoTopicCreation": False,
        "kafkaProducerMessage": None,
        "screenshot": None,
        "headers": None,
        "body": None,
        "grpcBody": None,
        "grpcMetadata": None,
        "basic_auth_user": None,
        "basic_auth_pass": None,
        "oauth_client_id": None,
        "oauth_client_secret": None,
        "oauth_token_url": None,
        "oauth_scopes": None,
        "oauth_auth_method": "client_secret_basic",
        "pushToken": None,
        "databaseConnectionString": None,
        "radiusUsername": None,
        "radiusPassword": None,
        "radiusSecret": None,
        "mqttUsername": "",
        "mqttPassword": "",
        "authWorkstation": None,
        "authDomain": None,
        "tlsCa": None,
        "tlsCert": None,
        "tlsKey": None,
        "kafkaProducerSaslOptions": {"mechanism": "None"},
        "includeSensitiveData": True,
    }


def make_monitor(m_id: int, domain: str, group_id: int,
                 tags: List[str], group_name: str,
                 tag_counter: int) -> Dict:
    """Create a valid HTTP monitor assigned to a group."""
    url = f"https://{domain}"
    tag_objs = []
    for t in sorted(set(tags + ([group_name] if group_name else []))):
        tag_objs.append(make_tag(tag_counter, m_id, t))
        tag_counter += 1

    path_name = f"{group_name} / {domain}" if group_name else domain

    return {
        "id": m_id,
        "name": domain,
        "description": None,
        "pathName": path_name,
        "parent": group_id,
        "childrenIDs": [],
        "url": url,
        "method": "GET",
        "hostname": None,
        "port": None,
        "maxretries": 3,
        "weight": 2000,
        "active": True,
        "forceInactive": False,
        "type": "http",
        "timeout": 48,
        "interval": 60,
        "retryInterval": 60,
        "resendInterval": 0,
        "keyword": None,
        "invertKeyword": False,
        "expiryNotification": True,
        "ignoreTls": False,
        "upsideDown": False,
        "packetSize": 56,
        "maxredirects": 10,
        "accepted_statuscodes": ["200-299"],
        "dns_resolve_type": "A",
        "dns_resolve_server": "1.1.1.1",
        "dns_last_result": None,
        "docker_container": "",
        "docker_host": None,
        "proxyId": None,
        "notificationIDList": {},
        "tags": tag_objs,
        "maintenance": False,
        "mqttTopic": "",
        "mqttSuccessMessage": "",
        "databaseQuery": None,
        "authMethod": None,
        "grpcUrl": None,
        "grpcProtobuf": None,
        "grpcMethod": None,
        "grpcServiceName": None,
        "grpcEnableTls": False,
        "radiusCalledStationId": None,
        "radiusCallingStationId": None,
        "game": None,
        "gamedigGivenPortOnly": True,
        "httpBodyEncoding": "json",
        "jsonPath": None,
        "expectedValue": None,
        "kafkaProducerTopic": None,
        "kafkaProducerBrokers": [],
        "kafkaProducerSsl": False,
        "kafkaProducerAllowAutoTopicCreation": False,
        "kafkaProducerMessage": None,
        "screenshot": None,
        "headers": None,
        "body": None,
        "grpcBody": None,
        "grpcMetadata": None,
        "basic_auth_user": None,
        "basic_auth_pass": None,
        "oauth_client_id": None,
        "oauth_client_secret": None,
        "oauth_token_url": None,
        "oauth_scopes": None,
        "oauth_auth_method": "client_secret_basic",
        "pushToken": None,
        "databaseConnectionString": None,
        "radiusUsername": None,
        "radiusPassword": None,
        "radiusSecret": None,
        "mqttUsername": "",
        "mqttPassword": "",
        "authWorkstation": None,
        "authDomain": None,
        "tlsCa": None,
        "tlsCert": None,
        "tlsKey": None,
        "kafkaProducerSaslOptions": {"mechanism": "None"},
        "includeSensitiveData": True,
    }


# ---------------- Main logic ----------------

def generate_backup(hosts: List[str], group_name: str, tags: List[str],
                    output_path: str, overwrite: bool, force: bool):
    """Generate or merge a backup JSON file."""
    hosts = [clean_domain(h) for h in hosts]
    data = load_backup(output_path)
    merging = os.path.exists(output_path)

    if merging and not overwrite and not force:
        ans = input(f"⚠️ {output_path} exists. Overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print("❌ Cancelled.")
            return

    monitors = data["monitorList"]
    group_id = next_id(monitors) if group_name else None
    tag_counter = 1
    created_ids = []

    # Create optional group
    if group_name:
        group = make_group(group_id, group_name)
        monitors.append(group)

    # Create monitors
    m_id = next_id(monitors)
    for h in hosts:
        mon = make_monitor(m_id, h, group_id, tags, group_name, tag_counter)
        monitors.append(mon)
        created_ids.append(m_id)
        tag_counter += len(tags) + (1 if group_name else 0)
        m_id += 1

    # Update group children list
    if group_name:
        group["childrenIDs"] = created_ids

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ {'Overwritten' if overwrite else 'Created'} {output_path}")
    if group_name:
        print(f"  • Group '{group_name}' (ID {group_id}) with {len(created_ids)} sites")
    else:
        print(f"  • {len(created_ids)} independent sites created")
    print("  • Tags and relationships validated")


# ---------------- CLI ----------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Uptime Kuma backup.json with valid groups and colored tags."
    )
    parser.add_argument("-f", "--file", help="Hosts file path (default: hosts.txt if present)")
    parser.add_argument("--hosts", nargs="+", help="Provide hostnames inline")
    parser.add_argument("-g", "--group", help="Optional group name")
    parser.add_argument("-t", "--tags", nargs="+", default=[], help="Tags to apply (space/comma separated)")
    parser.add_argument("-o", "--output", help="Output filename (default: <input>_backup.json)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file without prompt")
    parser.add_argument("--force", action="store_true", help="Skip confirmation when merging")
    args = parser.parse_args()

    # Collect hosts
    hosts = []
    if args.file and os.path.exists(args.file):
        hosts.extend(read_hosts(args.file))
    elif os.path.exists("hosts.txt"):
        hosts.extend(read_hosts("hosts.txt"))
    if args.hosts:
        hosts.extend(args.hosts)
    if not hosts:
        print("❌ No hosts provided or file not found.")
        exit(1)

    # Normalize tags
    tags = normalize_tags(args.tags)

    # Determine output file name
    if args.output:
        output_path = args.output
    elif args.file:
        base = os.path.splitext(os.path.basename(args.file))[0]
        output_path = f"{base}_backup.json"
    else:
        output_path = "hosts_backup.json"

    generate_backup(hosts, args.group, tags, output_path, args.overwrite, args.force)
