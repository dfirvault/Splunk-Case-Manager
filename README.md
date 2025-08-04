# Splunk Index Manager

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-lightgrey)

<img width="688" height="1259" alt="image" src="https://github.com/user-attachments/assets/7e04fa3d-8c0a-4c48-bc2b-a382abf18d28" />

A Python-based GUI/CLI hybrid tool for managing Splunk indexes, including creation, deletion, and backup/restore operations.

## Features

- **Index Management**:
  - Create new indexes
  - List existing indexes (excluding system indexes)
  - Delete indexes
- **Backup & Restore**:
  - Full index backup (including data files and folder structure)
  - Password-protected backups (optional)
  - Restore from backup files
- **User-Friendly Interface**:
  - Tkinter-based GUI for file selection
  - CLI menu system for operations
  - Automatic config file creation
- **Cross-Platform**:
  - Works on Windows, Linux, and macOS
  - Auto-detects common Splunk installation paths

## Prerequisites

- Python 3.7 or higher
- Splunk installed on the system
- Valid Splunk credentials

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/splunk-manager.git
   cd splunk-manager
   ```
2. ```bash
   python splunk_manager.py
   ```
## Backup Format
Backups are created as ZIP files containing:
The complete index folder structure (including empty directories)
The index's .dat file
Optional password protection

## Configuration
The configuration file (config.txt) stores:
Splunk binary path
Username (in plaintext - see Security Note)
Password (in plaintext - see Security Note)

## Security Note
⚠️ Important: The current implementation stores credentials in plaintext. For production use:
Consider using environment variables
Or implement proper encryption
Or use Splunk's app token authentication

## License
MIT License - See LICENSE file

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss proposed changes.   
