#!/usr/bin/env python3
import argparse
import json
import re
import os
from typing import List, Tuple

# --- Helpers ---------------------------------------------------------------

def clean_hostname(host: str) -> Tuple[str, str]:
    """Ensure https:// prefix and return (url, simplified hostname)."""
    if not re.match(r'^https?://', host):
        host = f"https://{host}"
    clean_host = re.sub(r'^https?://', '', host)
    clean_host = re.sub(r'\.[a-z]+$', '', clean_host)
    return host, clean_host


def read_hosts_file(file_name: str) -> List[str]:
    """Read host list from text file."""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_name}' was not found.")
        return []


def normalize_tags(raw_tags: List[str]) -> List[str]:
    """Flatten, deduplicate, and sort tags."""
    flat = []
    for t in raw_tags:
        flat.extend([s.strip() for s in t.split(",") if s.strip()])
    seen, unique = set(), []
    for s in flat:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return sorted(unique, key=str.lower)


# --- JSON Builders ---------------------------------------------------------

def create_group_monitor(group_id: int, name: str) -> dict:
    """Create a group monitor entry."""
    return {
        "id": group_id,
        "name": name,
        "description": None,
        "pathName": name,
        "parent": None,
        "childrenIDs": [],
        "url": "",
        "method": "GET",
        "hostname": None,
        "port": None,
        "maxretries": 0,
        "weight": 2000,
        "active": False,
        "forceInactive": False,
        "type": "group",
        "timeout": 0,
        "interval": 0,
        "retryInterval": 0,
        "resendInterval": 0,
        "keyword": None,
        "invertKeyword": False,
        "expiryNotification": False,
        "ignoreTls": False,
        "upsideDown": False,
        "packetSize": 0,
        "maxredirects": 0,
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
        "includeSensitiveData": True
    }


def create_site_monitor(site_id: int, host: str, tags: List[str], group_id: int, group_name: str) -> dict:
    """Create a site monitor entry assigned to the given group."""
    host_url, clean_host = clean_hostname(host)
    all_tags = sorted(set(tags + [group_name]))
    return {
        "id": site_id,
        "name": clean_host,
        "description": None,
        "pathName": f"{group_name} / {clean_host}",
        "parent": group_id,
        "childrenIDs": [],
        "url": host_url,
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
        "tags": all_tags,
        "maintenance": False,
        "mqttTopic": "",
        "mqttSuccessMessage": "",
        "databaseQuery": None,
        "authMethod": None,
        "includeSensitiveData": True
    }


# --- Core ------------------------------------------------------------------

def load_existing_backup(file_path: str) -> dict:
    """Load an existing backup.json if valid."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "monitorList" not in data:
                raise ValueError
            return data
        except Exception:
            print("⚠️ Existing backup.json found but invalid — will recreate.")
    return {"version": "1.23.17", "notificationList": [], "monitorList": []}


def get_next_id(monitors: List[dict]) -> int:
    """Get the next available monitor ID."""
    if not monitors:
        return 1
    return max(m["id"] for m in monitors) + 1


def create_backup_json(hosts_file: str, tags: List[str], group_name: str, force: bool) -> None:
    hosts = read_hosts_file(hosts_file)
    if not hosts:
        return

    file_path = "backup.json"
    merging = os.path.exists(file_path)

    # If merging and not forced, confirm
    if merging and not force:
        ans = input(f"⚠️ '{file_path}' exists. Merge new group '{group_name}' into it? [y/N]: ").strip().lower()
        if ans != "y":
            print("❌ Operation cancelled.")
            return

    data = load_existing_backup(file_path)
    monitors = data["monitorList"]

    start_id = get_next_id(monitors)
    group_id = start_id
    next_id = group_id + 1

    # Create the new group
    group_monitor = create_group_monitor(group_id, group_name)
    monitors.append(group_monitor)

    # Add all sites under that group
    for host in hosts:
        monitors.append(create_site_monitor(next_id, host, tags, group_id, group_name))
        next_id += 1

    # Write back
    data["monitorList"] = monitors
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    action = "Merged into" if merging else "Created new"
    print(f"✅ {action} backup.json with group '{group_name}' and {len(hosts)} sites.")
    print(f"  → IDs start at {group_id}")
    print(f"  → Total monitors now: {len(monitors)}")
    if tags:
        print(f"  → Base tags: {tags}")
    print(f"  → Each site automatically tagged with '{group_name}'")


# --- CLI -------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or merge Uptime Kuma backup.json with one group and tagged site monitors."
    )
    parser.add_argument("hosts_file", help="Path to hosts file (e.g., hosts.txt)")
    parser.add_argument("-t", dest="tags", action="extend", nargs="+", default=[],
                        help="Tag(s) to apply to all sites (space/comma separated).")
    parser.add_argument("-g", dest="group", required=True,
                        help="Single group name to create (e.g., -g jolmes).")
    parser.add_argument("--force", action="store_true",
                        help="Skip confirmation prompt when merging into existing backup.json.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    tags = normalize_tags(args.tags)
    create_backup_json(args.hosts_file, tags, args.group, args.force)
