# Splunk Index Manager V0.2

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Uploading image.png…]()


<img width="688" height="1259" alt="image" src="https://github.com/user-attachments/assets/7e04fa3d-8c0a-4c48-bc2b-a382abf18d28" />

A Python-based GUI/CLI hybrid tool for managing Splunk indexes, including creation, deletion, and backup/restore operations.

## Features v0.2 added error handling, more functionlity and better ui!

### 🗂️ **Index Management**
- Create, delete, and manage Splunk indexes with simple menu-driven operations  
- View index sizes with automatic MB/GB conversion for easy monitoring  
- Intelligent filtering of system indexes and default destinations  

### 💾 **Backup & Restore**
- Complete index backup including all data files and empty directories  
- Optional password protection for sensitive backup archives  
- Full restore functionality with automatic configuration updates  

### 🎨 **User-Friendly Interface**
- Color-coded console output with intuitive symbols (✓ ✗ ⚠)  
- Progress bars and animations for long-running operations  
- Context-aware confirmation prompts for destructive actions  

### ⚙️ **Configuration & Automation**
- Persistent configuration storage for Splunk path and credentials  
- Batch operations (backup + delete in one step)  
- Works across Windows, Linux, and macOS platforms  

### 📊 **Size-Aware Operations**
- Automatic index size calculation before operations  
- Visual warnings for large indexes (>2GB)  
- Smart filtering of system/main indexes from management lists 

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
