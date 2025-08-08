# Splunk Index Manager V0.3

![Python](https://img.shields.io/badge/python-3.7%2B-blue)

<img width="626" height="589" alt="image" src="https://github.com/user-attachments/assets/effc6504-6331-491b-91ab-0a75a7d382d0" />
<img width="687" height="859" alt="image" src="https://github.com/user-attachments/assets/f2d35a3b-1d08-4ccf-9278-966ade1321d5" />

The output of the above will produce .zip files that contain your Splunk index which you can move or backup to a different location:
<img width="611" height="182" alt="image" src="https://github.com/user-attachments/assets/0bacfac6-d87e-493e-8da9-f1e74d20ef88" />


A Python-based GUI/CLI hybrid tool for managing Splunk indexes, including creation, deletion, and backup/restore operations.

## Features v0.3 added error handling, more functionlity and better ui!

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
   git clone https://github.com/dfirvault/Splunk-Case-Manager.git
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
Lastly, this only backs up your index, dashboards and other changes are not included. This is purely for index management.

## License
MIT License - See LICENSE file

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss proposed changes.   
