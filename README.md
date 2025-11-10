# 🛠️ Uptime Kuma Bulk Importer

A modern Python tool to **bulk-import domains into Uptime Kuma** with full support for **groups**, **tags**, and **color-coded hierarchy**.

This script generates a valid `backup.json` file that you can directly import via the Uptime Kuma UI.  
It follows the official JSON schema (tested with Kuma v1.23.17) and ensures that all groups, monitors, and tag objects are correctly linked.

---

## ✨ Features

- ✅ Create **monitor groups** automatically (`--group`)
- ✅ Bulk-add **domains/hosts** from a simple text file
- ✅ Assign **tags** to all created monitors (`--tags`)
- ✅ Deterministic **tag colors** for consistent UI display
- ✅ Proper **parent/child linking** for group hierarchy  
- ✅ **Merge-safe** — appends to existing `backup.json` without overwriting
- ✅ Zero configuration: produces a ready-to-import file

---

## 📦 Requirements

- Python 3.7 or newer  
- No external dependencies (uses only standard library)

---

## 📄 Setup

Clone or download the repository, then place your domains in a `hosts.txt` file:

```
example.com
https://sub.domain.org
anotherhost.net
```

---

## 🚀 Usage

### Basic command
```bash
python3 import.py -g mygroup
```
Creates:
- A group named **mygroup**
- One monitor per host in `hosts.txt`
- Output file: `backup.json`

### With tags
```bash
python3 import.py -g production -t prod live internal
```
Adds tags to each monitor:
- `prod`
- `live`
- `internal`
- Plus the group name (`production`) as a tag automatically

### Force overwrite existing backup
```bash
python3 import.py -g staging -t test --force
```
Skips the merge confirmation prompt and appends new entries directly.

---

## 🧩 Import into Uptime Kuma

1. Open your Uptime Kuma web UI.  
2. Go to **Settings → Import/Export**.  
3. Choose **Import Backup** and select the generated `backup.json`.  
4. After import, you’ll see:
   - Your new **group** (e.g., “production”)  
   - All **sites** nested under that group  
   - Correct **tags and colors** in the UI  

---

## 🧠 Example output

```json
{
  "id": 260,
  "name": "production",
  "type": "group",
  "childrenIDs": [261, 262]
},
{
  "id": 261,
  "name": "example.com",
  "parent": 260,
  "pathName": "production / example.com",
  "tags": [
    { "name": "prod", "color": "#E47440" },
    { "name": "production", "color": "#3DD992" }
  ]
}
```

---

## 🧹 Notes

- `notificationIDList` is intentionally empty to prevent SQLite foreign-key errors.  
- All colors are derived deterministically from tag names for visual consistency.  
- The script validates JSON structure automatically before writing.

---

## 🧑‍💻 CLI Help

```bash
python3 import.py -h
```

```
usage: import.py [-h] -g GROUP [-t TAGS [TAGS ...]] [--force] hosts_file

Generate Uptime Kuma backup.json with valid groups and colored tags.

positional arguments:
  hosts_file            File containing hostnames (one per line)

options:
  -g, --group           Group name to create
  -t, --tags            Tags to apply (space/comma separated)
  --force               Skip confirmation when merging
  -h, --help            Show this help message
```

---

## 🧾 License

MIT License – Free for personal and commercial use.

---

> 💡 **Tip:** You can safely merge multiple runs into one `backup.json`  
> to maintain multiple groups (e.g. `production`, `staging`, `internal`).

---
