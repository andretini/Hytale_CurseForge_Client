# Hytale CurseForge CLI

An APT-style command-line tool for managing Hytale mods via the CurseForge API. Designed for Linux servers with minimal dependencies.

Fork of [andretini/Hytale_CurseForge_Client](https://github.com/andretini/Hytale_CurseForge_Client) - adds a server-friendly CLI interface.

---

## Features

- **Zero dependencies** - Works with Python stdlib only (click/rich optional for prettier output)
- **APT-style commands** - Familiar syntax: `search`, `install`, `remove`, `update`, `list`
- **Cron compatible** - Use `-y` flag for non-interactive automation
- **Auto-sorting** - Automatically installs mods/worlds/prefabs to correct folders
- **Update management** - Checks for updates and removes old files automatically
- **Config persistence** - API key and settings stored in `~/.config/hytale-cf/`

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/rederyk/Hytale_CurseForge_CLI.git
cd Hytale_CurseForge_CLI

# No dependencies required! Just run:
./hytale-cf --help

# Configure (interactive - recommended)
./hytale-cf config --api-key-prompt
./hytale-cf config --game-path /path/to/hytale

# Search and install mods
./hytale-cf search magic
./hytale-cf install 1423494

# List installed mods
./hytale-cf list

# Update all mods
./hytale-cf update
```

### Optional: Pretty Output

```bash
# Install click + rich for colored tables and progress bars
pip install click rich

# Or via setup.py
pip install -e ".[pretty]"
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `hytale-cf search <query>` | Search for mods, worlds, prefabs |
| `hytale-cf install <id>` | Install a mod by ID |
| `hytale-cf remove <id>` | Remove an installed mod |
| `hytale-cf list` | List installed mods |
| `hytale-cf info <id>` | Show detailed mod information |
| `hytale-cf update` | Check and install updates for all mods |
| `hytale-cf config` | Configure API key and game path |

### Command Options

```bash
# Search options
hytale-cf search -c worlds "adventure"    # Search specific category
hytale-cf search -c mods -n 20 "magic"    # Limit results
# Categories: mods, worlds, prefabs, bootstrap, translations

# Skip confirmations (for scripts/cron)
hytale-cf install -y 12345
hytale-cf remove -y 12345
hytale-cf update -y

# Verbose output
hytale-cf list -v

# Config options
hytale-cf config --show                   # Show current config
hytale-cf config --api-key-prompt         # Set API key interactively
hytale-cf config --api-key 'KEY'          # Set API key (use single quotes!)
hytale-cf config --game-path /path        # Set game directory
```

---

## Automation (Cron)

The CLI is fully compatible with cron for automated updates:

```bash
# Edit crontab
crontab -e

# Add daily update at 4:00 AM
0 4 * * * /path/to/hytale-cf update -y >> /var/log/hytale-cf.log 2>&1
```

**Note:** The `-y` flag skips all confirmations for non-interactive use.

---

## Setup Guide

### 1. Obtaining a CurseForge API Key

1. Go to [CurseForge for Studios](https://console.curseforge.com/#/)
2. Log in and set organization name
3. Click **API Keys** in the sidebar
4. Copy your API key

```bash
# Set API key (interactive - recommended)
./hytale-cf config --api-key-prompt

# Or with single quotes (important for keys with $ characters!)
./hytale-cf config --api-key '$2a$10$YOUR_KEY_HERE'
```

### 2. Setting the Game Path

```bash
./hytale-cf config --game-path /path/to/hytale
```

The path should point to your Hytale installation root (containing `UserData` folder).

### 3. Verify Configuration

```bash
./hytale-cf config --show
```

---

## How It Works

### Auto-Sorting

The CLI automatically detects resource types and installs to the correct subfolder:

| Type | Destination |
|------|-------------|
| Mods | `UserData/Mods` |
| Worlds | `UserData/Saves` (auto-extracted from zip) |
| Prefabs | `prefabs` |
| Bootstrap | `bootstrap` |
| Translations | `translations` |

### Update Behavior

When updating mods:
1. Checks if newer version is available on CurseForge
2. Downloads the new file
3. **Automatically removes the old file** (if filename changed)
4. Updates tracking in config

---

## Configuration

Settings are stored in `~/.config/hytale-cf/config.json`:

```json
{
  "api_key": "$2a$10$...",
  "game_path": "/path/to/hytale",
  "installed": {
    "1423494": {
      "mod_id": 1423494,
      "name": "EyeSpy",
      "filename": "EyeSpy-2026.1.20-5708.jar",
      "version": "EyeSpy-2026.1.20-5708.jar",
      "file_id": 7491939,
      "class_id": 9137,
      "path": "/path/to/hytale/UserData/Mods/EyeSpy-2026.1.20-5708.jar"
    }
  }
}
```

---

## Requirements

**CLI (minimal):**
- Python 3.8+
- No external dependencies (uses stdlib only)

**CLI (pretty output):**
- click >= 8.0
- rich >= 13.0

**GUI (original):**
- Python 3.8+
- PySide6

---

## Project Structure

```
.
├── hytale-cf             # CLI entry point (executable)
├── cli/                  # CLI implementation
│   ├── main.py           # Commands (click/argparse)
│   └── output.py         # Output helpers (rich fallback)
├── curseforge/           # API client (shared)
│   ├── client.py         # CurseForge API wrapper
│   └── config.py         # Configuration management
├── ui/                   # GUI (PySide6) - original
├── tui/                  # Future TUI (textual) - planned
├── setup.py              # pip install support
├── requirements.txt      # GUI dependencies
└── requirements-cli.txt  # CLI optional dependencies
```

---

## GUI Usage (Original)

The original GUI is still available for desktop users:

```bash
pip install -r requirements.txt
python3 main.py
```

---

## License

MIT License

---

## Credits

- Original project: [andretini/Hytale_CurseForge_Client](https://github.com/andretini/Hytale_CurseForge_Client)
- CLI fork: [rederyk/Hytale_CurseForge_CLI](https://github.com/rederyk/Hytale_CurseForge_CLI)
