# Recall - Personal Memory Search App for macOS

## Overview

Recall is a native macOS menu bar application that creates a unified, searchable timeline of your digital activity by combining:

- **WindRecorder**: Screen recordings with OCR text extraction
- **AI Chat Logs**: Claude and ChatGPT conversation history
- **Smart Archiving**: Automatic backup to Hetzner server when thresholds are reached

## Features

- 🧠 **Menu Bar Integration**: Always accessible from your Mac's menu bar
- 🔍 **Quick Search**: Instant search across all your digital activity
- 📊 **Timeline View**: Visual browsing of your day/week/month
- 💾 **Smart Archiving**: Automatic backup when database reaches 5GB or 30 days
- 🔄 **Background Sync**: Silent archiving to Hetzner server via SFTP
- 🔔 **Native Notifications**: macOS-style alerts for sync status

## Architecture

```
RecallApp/
├── app/                    # Main application code
│   ├── menu_bar.py        # Primary menu bar app (rumps)
│   ├── search_window.py   # Search interface (PyQt6)
│   ├── timeline_viewer.py # Timeline browser
│   └── settings.py        # Preferences window
├── core/                  # Core functionality
│   ├── windrecorder_client.py  # WindRecorder database integration
│   ├── claude_parser.py        # Claude JSONL parser
│   ├── archiver.py             # Hetzner archive manager
│   ├── search_engine.py        # Unified search with Chroma
│   └── models.py               # Data models
├── resources/             # App resources
│   ├── icon.icns         # Menu bar icon
│   └── sounds/           # Notification sounds
├── setup.py              # py2app configuration
└── requirements.txt      # Python dependencies
```

## Technology Stack

- **rumps**: Mac menu bar application framework
- **py2app**: Python to native .app packaging
- **PyQt6**: GUI framework for detailed windows
- **ChromaDB**: Vector search for semantic queries
- **paramiko**: SFTP uploads to Hetzner
- **sqlite3**: WindRecorder database access

## Installation & Setup

### Prerequisites

1. **WindRecorder**: Install from [yuka-friends/Windrecorder](https://github.com/yuka-friends/Windrecorder)
2. **Python 3.9+**: Required for the application
3. **Hetzner Server**: For archive storage (optional)

### Build Instructions

```bash
# Clone the repository
git clone <repo-url>
cd RecallApp

# Install dependencies
pip install -r requirements.txt

# Build the application
python setup.py py2app

# Install to Applications folder
cp -r dist/Recall.app /Applications/

# Launch
open /Applications/Recall.app
```

## Configuration

### Environment Variables (.env)

```bash
# WindRecorder
WINDRECORDER_DB_PATH=~/WindRecorder/userdata/db/windrecorder.db
MAX_SIZE_MB=5000
MAX_AGE_DAYS=30

# Hetzner Server
HETZNER_HOST=your-server.hetzner.com
HETZNER_USER=backup-user
SSH_KEY_PATH=~/.ssh/id_rsa
REMOTE_BACKUP_DIR=/var/backups/windrecorder

# Local Settings
CHROMA_DB_PATH=~/Library/Application Support/Recall/chroma_db
```

### SSH Key Setup for Hetzner

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/recall_backup

# Copy public key to Hetzner server
ssh-copy-id -i ~/.ssh/recall_backup.pub backup-user@your-server.hetzner.com
```

## Usage

### Menu Bar Options

- **🔍 Quick Search**: Open search dialog (⌘+Space)
- **📊 Timeline View**: Browse activities by time
- **📁 Recent Activities**: Show last hour of activity
- **💾 Archive Status**: Database size and sync information
- **🔄 Sync Now**: Manually trigger archive upload
- **⚙️ Preferences**: Configure settings

### Search Examples

- "What was I working on yesterday at 3 PM?"
- "Show me all Claude conversations about CRM"
- "Find error messages from last week"
- "What browser tabs were open during the meeting?"

## Data Flow

1. **WindRecorder** continuously records screen with OCR
2. **Claude logs** are parsed from ~/.claude/projects/
3. **Timeline merger** combines data sources
4. **Search engine** indexes with Chroma embeddings
5. **Archive manager** monitors thresholds and uploads to Hetzner
6. **Menu bar app** provides instant access to search

## Privacy & Security

- All processing happens locally on your Mac
- Only compressed, encrypted archives sent to Hetzner
- SSH key authentication (no passwords)
- Code-signed application bundle
- Sandboxed for additional security

## System Requirements

- macOS 11.0 (Big Sur) or later
- Python 3.9+
- 100MB disk space for application
- WindRecorder installed and running
- SSH access to Hetzner server (for archiving)

## Development

### Running in Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the menu bar app directly
python app/menu_bar.py

# Run search window for testing
python app/search_window.py
```

### Building for Distribution

```bash
# Clean previous builds
rm -rf build dist

# Build signed application
python setup.py py2app
codesign --deep --force --sign - dist/Recall.app

# Create installer (optional)
create-dmg dist/Recall.app
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issues page.