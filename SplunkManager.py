import os
import json
import subprocess
import getpass
import time
import zipfile
import shutil
import platform
from tkinter import Tk, filedialog, messagebox
from tkinter.ttk import Progressbar
import tkinter as tk
from threading import Thread
from queue import Queue

# Initialize colorama on Windows
if platform.system() == 'Windows':
    import colorama
    colorama.init()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Splunk Index Manager v0.4
#  Developed by Jacob Wilson • dfirvault@gmail.com
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Color and symbol constants
class Style:
    HEADER = "━" * 60
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    PROMPT = "➤"
    DIVIDER = "─" * 60
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

# Print formatted header
def print_header():
    print(f"\n{Style.BLUE}{Style.HEADER}{Style.END}")
    print(f"{Style.BOLD}{Style.BLUE}  Splunk Index Manager {Style.END}v0.4")
    print(f"  {Style.BLUE}Developed by Jacob Wilson • dfirvault@gmail.com{Style.END}")
    print(f"{Style.BLUE}{Style.HEADER}{Style.END}\n")

print_header()

CONFIG_FILE = "config.txt"
DEFAULT_SPLUNK_PATHS = [
    "/opt/splunk/bin/splunk",
    "C:\\Program Files\\Splunk\\bin\\splunk.exe",
    "/Applications/Splunk/bin/splunk"
]

class SplunkManager:
    def __init__(self):
        self.splunk_path = ""
        self.username = ""
        self.password = ""
        self.load_config()
        self.verify_splunk()

    def show_progress(self, message, duration=2):
        """Show a spinning progress animation"""
        spinner = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            print(f"\r{Style.BLUE}{spinner[i % len(spinner)]}{Style.END} {message}", end="")
            time.sleep(0.1)
            i += 1
        print("\r" + " " * (len(message) + 2) + "\r", end="")

    def print_success(self, message):
        print(f"{Style.GREEN}{Style.SUCCESS} {message}{Style.END}")

    def print_error(self, message):
        print(f"{Style.RED}{Style.ERROR} {message}{Style.END}")

    def print_warning(self, message):
        print(f"{Style.YELLOW}{Style.WARNING} {message}{Style.END}")

    def print_info(self, message):
        print(f"{Style.BLUE}{Style.INFO} {message}{Style.END}")

    def print_divider(self):
        print(f"{Style.BLUE}{Style.DIVIDER}{Style.END}")

    def load_config(self):
        """Load configuration from file or prompt user for input"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.splunk_path = config.get('splunk_path', '')
                    self.username = config.get('username', '')
                    self.password = config.get('password', '')
            except:
                # Config file is corrupted, we'll recreate it
                pass
        
        # If Splunk path isn't set or doesn't exist, prompt user
        if not self.splunk_path or not os.path.exists(self.splunk_path):
            self.prompt_splunk_path()
            
        # If credentials aren't set, prompt user
        if not self.username or not self.password:
            self.prompt_credentials()
            
        self.save_config()
        
    def prompt_splunk_path(self):
        """Prompt user for Splunk binary path"""
        root = Tk()
        root.withdraw()
        
        # Try to find Splunk binary in common locations
        for path in DEFAULT_SPLUNK_PATHS:
            if os.path.exists(path):
                use_default = messagebox.askyesno(
                    "Splunk Path Found",
                    f"Splunk binary found at {path}. Use this location?"
                )
                if use_default:
                    self.splunk_path = path
                    root.destroy()
                    return
        
        # If not found in common locations, ask user
        messagebox.showinfo(
            "Splunk Path",
            "Please select the Splunk binary (splunk or splunk.exe)"
        )
        self.splunk_path = filedialog.askopenfilename(
            title="Select Splunk binary"
        )
        root.destroy()
        
    def prompt_credentials(self):
        """Prompt user for Splunk credentials"""
        print(f"\n{Style.YELLOW}🔑 Splunk Credentials Required{Style.END}")
        self.username = input(f"{Style.PROMPT} Enter Splunk username: ")
        self.password = getpass.getpass(f"{Style.PROMPT} Enter Splunk password: ")
        
    def save_config(self):
        """Save configuration to file"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'splunk_path': self.splunk_path,
                'username': self.username,
                'password': self.password
            }, f)
            
    def verify_splunk(self):
        """Verify Splunk binary and credentials work"""
        if not os.path.exists(self.splunk_path):
            self.print_error("Splunk binary not found at specified path.")
            self.prompt_splunk_path()
            self.save_config()
            
        self.show_progress("Verifying Splunk connection...")
        
        # Test login
        test_cmd = [
            self.splunk_path,
            'login',
            '-auth',
            f'{self.username}:{self.password}'
        ]
        
        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True
            )
            if "Login failed" in result.stderr:
                self.print_error("Login failed with provided credentials.")
                self.prompt_credentials()
                self.save_config()
                self.verify_splunk()
            else:
                self.print_success("Successfully connected to the local Splunk service! http://127.0.0.1:8000/")
                print(f"{Style.BLUE}•{Style.END} Using Splunk binary at: {self.splunk_path}")
                print(f"{Style.BLUE}•{Style.END} Authenticated as user: {self.username}\n")
        except Exception as e:
            self.print_error(f"Error testing Splunk connection: {e}")
            self.prompt_splunk_path()
            self.save_config()
            self.verify_splunk()
            
    def run_splunk_command(self, command):
        """Run a Splunk CLI command with suppressed SSL warnings"""
        full_cmd = [self.splunk_path] + command
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                shell=True if os.name == 'nt' else False,
                env={**os.environ, 'SPLUNK_CLI_SERVER_CERT_VERIFY': '0'}  # Suppress SSL warning
            )
            # Filter out SSL warnings
            filtered_output = '\n'.join(
                line for line in result.stdout.split('\n') 
                if 'Server Certificate Hostname Validation' not in line
            )
            filtered_errors = '\n'.join(
                line for line in result.stderr.split('\n') 
                if 'Server Certificate Hostname Validation' not in line
            )
            return filtered_output + filtered_errors
        except Exception as e:
            self.print_error(f"Error running Splunk command: {e}")
            return None
            
    def create_index(self, index_name):
        """Create a new Splunk index"""
        self.show_progress(f"Creating index '{index_name}'...")
        result = self.run_splunk_command([
            'add', 'index', index_name,
            '-auth', f'{self.username}:{self.password}'
        ])
        
        if result is None:
            return False, "Failed to execute Splunk command"
            
        normalized_output = ' '.join(result.lower().split())
        success_phrases = ['created', 'added', 'already exists', 'index created']
        
        if any(phrase in normalized_output for phrase in success_phrases):
            return True, f"Index '{index_name}' created successfully."
        elif "error" in normalized_output or "failed" in normalized_output:
            return False, f"Splunk error: {result.strip()}"
            
        return False, f"Unexpected response: {result.strip()}"
    
    def get_index_size(self, index_name):
        """Get the size of an index in bytes"""
        splunk_db = os.path.join(
            os.path.dirname(os.path.dirname(self.splunk_path)),
            'var', 'lib', 'splunk'
        )
        index_path = os.path.join(splunk_db, index_name)
        
        if not os.path.exists(index_path):
            return 0
        
        total_size = 0
        for dirpath, _, filenames in os.walk(index_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except:
                    continue
        return total_size

    def format_size(self, bytes):
        """Convert bytes to human-readable format (MB or GB)"""
        mb = bytes / (1024 * 1024)
        if mb > 2000:  # More than 2GB
            return f"{mb / 1024:.1f}GB"
        return f"{mb:.1f}MB"

    def list_indexes(self, exclude_system=True):
        """List all indexes with option to exclude system indexes"""
        self.show_progress("Fetching list of indexes...")
        result = self.run_splunk_command([
            'list', 'index',
            '-auth', f'{self.username}:{self.password}'
        ])
        if not result:
            return []
        
        # List of indexes to exclude
        excluded_indexes = {
            '_',  # All system indexes starting with underscore
            'summary',
            'splunklogger',
            "main",
            'history'
        } if exclude_system else set()
        
        indexes = []
        for line in result.split('\n'):
            line = line.strip()
            # Skip empty lines and paths
            if not line or '\\' in line or '/' in line:
                continue
            
            # Check if index should be excluded
            if any(line.lower().startswith(excluded) for excluded in excluded_indexes):
                continue
                
            # Get index size and format it
            size_bytes = self.get_index_size(line)
            size_str = self.format_size(size_bytes)
            indexes.append(f"{line} - {size_str}")
        
        return indexes

    def delete_index(self, index_name):
        """Delete a Splunk index and remove its configuration from indexes.conf"""
        self.show_progress(f"Deleting index '{index_name}'...")
        result = self.run_splunk_command([
            'remove', 'index', index_name,
            '-auth', f'{self.username}:{self.password}'
        ])
        
        if result is None:
            return False, "Failed to execute Splunk command"
            
        normalized_output = ' '.join(result.lower().split())
        success_phrases = ['removed', 'deleted', 'removal of index', 'successfully']
        windows_success_phrases = ['admin handler not found']
        
        # Check if deletion was successful
        if (any(phrase in normalized_output for phrase in success_phrases) or 
            (os.name == 'nt' and any(phrase in normalized_output for phrase in windows_success_phrases))):
            
            # Now remove from indexes.conf
            conf_updated = self.remove_index_from_conf(index_name)
            if conf_updated:
                return True, f"Index '{index_name}' deleted successfully and removed from indexes.conf"
            else:
                return True, (f"Index '{index_name}' deleted successfully but could not update indexes.conf\n"
                             f"You may need to manually remove the [{index_name}] section")
        elif "error" in normalized_output or "failed" in normalized_output:
            return False, f"Splunk error: {result.strip()}"
            
        return False, f"Unexpected response: {result.strip()}"

    def remove_index_from_conf(self, index_name):
        """Remove an index section from indexes.conf"""
        # Try to find indexes.conf in common locations
        conf_locations = [
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'system', 'local', 'indexes.conf'),
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'apps', 'search', 'local', 'indexes.conf'),
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'system', 'default', 'indexes.conf')
        ]
        
        conf_path = None
        for path in conf_locations:
            if os.path.exists(path):
                conf_path = path
                break
        
        if not conf_path:
            # If we can't find it, ask the user
            root = Tk()
            root.withdraw()
            messagebox.showinfo(
                "indexes.conf Location",
                "Could not automatically find indexes.conf.\n"
                "It's typically located in:\n"
                "etc/system/local/ or etc/apps/search/local/"
            )
            conf_path = filedialog.askopenfilename(
                title="Select indexes.conf file",
                filetypes=[("Config files", "*.conf")]
            )
            root.destroy()
            
            if not conf_path:
                self.print_warning("Could not update indexes.conf - you'll need to manually remove the index section")
                return False
        
        try:
            with open(conf_path, 'r') as f:
                content = f.read()
            
            # Find and remove the index section
            start_idx = content.find(f"[{index_name}]")
            if start_idx == -1:
                return True  # Section doesn't exist, nothing to do
            
            # Find the end of the section (either double newline or next section)
            end_idx = content.find("\n[", start_idx)  # Start of next section
            if end_idx == -1:
                end_idx = len(content)
            else:
                # Include the newline before next section
                end_idx = content.rfind("\n", start_idx, end_idx)
            
            # Remove the section
            new_content = content[:start_idx] + content[end_idx:]
            
            # Write the updated content back to the file
            with open(conf_path, 'w') as f:
                f.write(new_content)
            
            self.print_info(f"Removed [{index_name}] section from {conf_path}")
            return True
        
        except Exception as e:
            self.print_warning(f"Could not update indexes.conf: {str(e)}")
            self.print_warning(f"You'll need to manually remove the [{index_name}] section")
            return False
        
    def index_exists(self, index_name):
        """Check if an index exists in Splunk"""
        indexes = self.list_indexes()
        return index_name in indexes
        
    def backup_index(self, index_name, backup_dir, password=None):
        """Backup an entire index folder (including empty subfolders) and its .dat file"""
        # Get the Splunk DB parent directory
        splunk_db = os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'var', 'lib', 'splunk')
        
        # Paths we want to back up
        index_folder = os.path.join(splunk_db, index_name)
        dat_file = os.path.join(splunk_db, f"{index_name}.dat")

        print(f"\n{Style.BLUE}📦 Backing up index data from:{Style.END}")
        if os.path.exists(dat_file):
            print(f" {Style.BLUE}•{Style.END} DAT file: {dat_file}")
        print(f" {Style.BLUE}•{Style.END} Index folder: {index_folder}")
        
        if not os.path.exists(index_folder) and not os.path.exists(dat_file):
            return False, f"No index data found (neither folder nor .dat file exists)"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir)
            except OSError as e:
                return False, f"Failed to create backup directory: {str(e)}"
        
        # Create backup
        zip_filename = os.path.join(backup_dir, f"{index_name}_backup_{time.strftime('%Y%m%d-%H%M%S')}.zip")
        start_time = time.time()
        
        try:
            print(f"\n{Style.BLUE}⏳ Creating backup archive...{Style.END}")
            
            total_files = 0
            if os.path.exists(index_folder):
                total_files = sum(len(files) for _, _, files in os.walk(index_folder))
            
            # Try to use pyzipper for AES encryption if password is provided
            if password:
                try:
                    import pyzipper
                    use_pyzipper = True
                except ImportError:
                    use_pyzipper = False
                    self.print_warning("pyzipper not available, falling back to standard zipfile")
                    self.print_warning("For proper encryption, install pyzipper: pip install pyzipper")
            else:
                use_pyzipper = False
            
            processed_files = 0
            
            if password and use_pyzipper:
                # Use pyzipper with AES encryption
                with pyzipper.AESZipFile(
                    zip_filename,
                    'w',
                    compression=pyzipper.ZIP_DEFLATED,
                    encryption=pyzipper.WZ_AES
                ) as zipf:
                    zipf.setpassword(password.encode('utf-8'))
                    
                    # Add .dat file if exists
                    if os.path.exists(dat_file):
                        zipf.write(dat_file, os.path.basename(dat_file))
                        print(f" {Style.GREEN}✓{Style.END} Added encrypted .dat file to backup")
                        processed_files += 1
                    
                    # Add entire index folder structure
                    if os.path.exists(index_folder):
                        for root, dirs, files in os.walk(index_folder):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(
                                    os.path.basename(index_folder),
                                    os.path.relpath(file_path, index_folder)
                                )
                                zipf.write(file_path, arcname)
                                processed_files += 1
                                
                                # Update progress
                                if processed_files % 10 == 0 or processed_files == total_files:
                                    progress = int(50 * processed_files / total_files) if total_files > 0 else 50
                                    print(f"\r[{Style.GREEN}{'█' * progress}{' ' * (50 - progress)}{Style.END}] {processed_files}/{total_files}", end="")
            else:
                # Fallback to standard zipfile
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if password:
                        zipf.setpassword(password.encode('utf-8'))
                        self.print_warning("Using weak ZIP encryption (install pyzipper for AES encryption)")
                    
                    # Add .dat file if exists
                    if os.path.exists(dat_file):
                        zipf.write(dat_file, os.path.basename(dat_file))
                        print(f" {Style.GREEN}✓{Style.END} Added .dat file to backup")
                        processed_files += 1
                    
                    # Add entire index folder structure
                    if os.path.exists(index_folder):
                        for root, dirs, files in os.walk(index_folder):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(
                                    os.path.basename(index_folder),
                                    os.path.relpath(file_path, index_folder)
                                )
                                zipf.write(file_path, arcname)
                                processed_files += 1
                                
                                # Update progress
                                if processed_files % 10 == 0 or processed_files == total_files:
                                    progress = int(50 * processed_files / total_files) if total_files > 0 else 50
                                    print(f"\r[{Style.GREEN}{'█' * progress}{' ' * (50 - progress)}{Style.END}] {processed_files}/{total_files}", end="")
            
            time_taken = time.time() - start_time
            print(f"\n{Style.GREEN}✓{Style.END} Backup completed in {time_taken:.1f} seconds!")
            
            # Verify encryption if password was used
            if password:
                try:
                    if use_pyzipper:
                        # Test pyzipper encryption
                        with pyzipper.AESZipFile(zip_filename) as test_zip:
                            test_zip.setpassword(password.encode('utf-8'))
                            test_zip.testzip()
                        self.print_success("Backup successfully encrypted with AES-256")
                    else:
                        # Test standard zip encryption
                        with zipfile.ZipFile(zip_filename, 'r') as test_zip:
                            test_zip.setpassword(password.encode('utf-8'))
                            test_zip.testzip()
                        self.print_success("Password protection verified (weak encryption)")
                except Exception as e:
                    self.print_warning(f"Could not verify encryption: {str(e)}")
            
            return True, (f"\n{Style.GREEN}Backup completed successfully!{Style.END}\n"
                  f"{Style.BLUE}Location:{Style.END} {os.path.normpath(zip_filename)}\n"
                  f"{Style.BLUE}Contents:{Style.END} {'DAT file + ' if os.path.exists(dat_file) else ''}{processed_files} files from index folder\n"
                  f"{Style.BLUE}Encryption:{Style.END} {'Enabled (AES-256)' if password and use_pyzipper else 'Enabled (weak)' if password else 'Disabled'}")
        except Exception as e:
            return False, f"Backup failed: {str(e)}"

    
    def restore_backup(self, backup_file):
        """Restore an index from backup zip file"""
        self.show_progress("Preparing to restore backup...")
        splunk_db = os.path.join(
            os.path.dirname(os.path.dirname(self.splunk_path)),
            'var', 'lib', 'splunk'
        )
        
        if not os.path.exists(backup_file):
            return False, "Backup file not found"
        
        print(f"\n{Style.BLUE}♻ Restoring backup from:{Style.END} {backup_file}")
        print(f"{Style.BLUE}•{Style.END} Target location: {splunk_db}")
        
        # Check if the backup is encrypted and if we have pyzipper
        is_encrypted = False
        try:
            # First try with standard zipfile
            with zipfile.ZipFile(backup_file, 'r') as test_zip:
                try:
                    test_zip.testzip()
                except RuntimeError as e:
                    if 'encrypted' in str(e):
                        is_encrypted = True
        except Exception as e:
            return False, f"Unable to read backup file: {str(e)}"
        
        password = None
        if is_encrypted:
            print(f"\n{Style.YELLOW}🔑 This backup is password protected{Style.END}")
            password = getpass.getpass(f"{Style.PROMPT} Enter backup password: ")
        
        try:
            # Extract the index name from the backup filename
            base_name = os.path.basename(backup_file)
            index_name = base_name.split('_backup_')[0]
            
            # Track what we're restoring
            restoring_dat = False
            restoring_folder = False
            
            # Determine which library to use for extraction
            use_pyzipper = False
            if is_encrypted:
                try:
                    import pyzipper
                    use_pyzipper = True
                except ImportError:
                    self.print_warning("pyzipper not available, falling back to standard zipfile for encrypted backup")
                    self.print_warning("For better compatibility with encrypted backups, install pyzipper: pip install pyzipper")
            
            if use_pyzipper:
                # Use pyzipper for encrypted backups
                with pyzipper.AESZipFile(backup_file, 'r') as zip_ref:
                    if password:
                        zip_ref.setpassword(password.encode('utf-8'))
                    
                    # First check what we have in the backup
                    for file in zip_ref.namelist():
                        if file.endswith('.dat'):
                            restoring_dat = True
                        elif file.startswith(f'{index_name}/'):
                            restoring_folder = True
                    
                    # Restore .dat file if present
                    if restoring_dat:
                        dat_file = f"{index_name}.dat"
                        print(f"\n{Style.BLUE}⏳ Restoring {dat_file}...{Style.END}")
                        try:
                            zip_ref.extract(dat_file, splunk_db)
                            print(f" {Style.GREEN}✓{Style.END} Restored {dat_file} to {splunk_db}")
                        except RuntimeError as e:
                            if 'Bad password' in str(e):
                                return False, "Incorrect password provided for encrypted backup"
                            raise
                    
                    # Restore folder if present
                    if restoring_folder:
                        print(f"\n{Style.BLUE}⏳ Restoring {index_name} folder...{Style.END}")
                        file_count = 0
                        for file in zip_ref.namelist():
                            if file.startswith(f'{index_name}/'):
                                try:
                                    zip_ref.extract(file, splunk_db)
                                    file_count += 1
                                    if file_count % 10 == 0:
                                        print(f"\r {Style.BLUE}•{Style.END} Restored {file_count} files...", end="")
                                except RuntimeError as e:
                                    if 'Bad password' in str(e):
                                        return False, "Incorrect password provided for encrypted backup"
                                    raise
                        print(f"\r {Style.GREEN}✓{Style.END} Restored {file_count} files to {index_name} folder")
            else:
                # Use standard zipfile for unencrypted or fallback for encrypted
                with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                    if password:
                        zip_ref.setpassword(password.encode('utf-8'))
                    
                    # First check what we have in the backup
                    for file in zip_ref.namelist():
                        if file.endswith('.dat'):
                            restoring_dat = True
                        elif file.startswith(f'{index_name}/'):
                            restoring_folder = True
                    
                    # Restore .dat file if present
                    if restoring_dat:
                        dat_file = f"{index_name}.dat"
                        print(f"\n{Style.BLUE}⏳ Restoring {dat_file}...{Style.END}")
                        try:
                            zip_ref.extract(dat_file, splunk_db)
                            print(f" {Style.GREEN}✓{Style.END} Restored {dat_file} to {splunk_db}")
                        except RuntimeError as e:
                            if 'Bad password' in str(e):
                                return False, "Incorrect password provided for encrypted backup"
                            elif 'compression method' in str(e):
                                return False, "Compression method not supported - try installing pyzipper: pip install pyzipper"
                            raise
                    
                    # Restore folder if present
                    if restoring_folder:
                        print(f"\n{Style.BLUE}⏳ Restoring {index_name} folder...{Style.END}")
                        file_count = 0
                        for file in zip_ref.namelist():
                            if file.startswith(f'{index_name}/'):
                                try:
                                    zip_ref.extract(file, splunk_db)
                                    file_count += 1
                                    if file_count % 10 == 0:
                                        print(f"\r {Style.BLUE}•{Style.END} Restored {file_count} files...", end="")
                                except RuntimeError as e:
                                    if 'Bad password' in str(e):
                                        return False, "Incorrect password provided for encrypted backup"
                                    elif 'compression method' in str(e):
                                        return False, "Compression method not supported - try installing pyzipper: pip install pyzipper"
                                    raise
                        print(f"\r {Style.GREEN}✓{Style.END} Restored {file_count} files to {index_name} folder")
            
            # Verify the index exists in Splunk
            if not self.index_exists(index_name):
                print(f"\n{Style.BLUE}⏳ Creating index {index_name} in Splunk...{Style.END}")
                success, message = self.create_index(index_name)
                if not success:
                    return False, f"Restore failed: {message}"
            
            # Update indexes.conf
            conf_updated = self.update_indexes_conf(index_name)
            
            return True, (f"\n{Style.GREEN}✓ Restore completed successfully!{Style.END}\n"
                     f"{Style.BLUE}Index:{Style.END} {index_name}\n"
                     f"{Style.BLUE}Location:{Style.END} {splunk_db}\n"
                     f"{Style.BLUE}Configuration:{Style.END} {'updated' if conf_updated else 'update attempted'}\n"
                     f"{Style.YELLOW}Note:{Style.END} You may need to manually restart Splunk for changes to take effect")
        
        except Exception as e:
            return False, f"Restore failed: {str(e)}"

    def update_indexes_conf(self, index_name):
        """Update indexes.conf with the restored index configuration"""
        self.show_progress(f"Updating indexes.conf for {index_name}...")
        # Try to find indexes.conf in common locations
        conf_locations = [
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'system', 'local', 'indexes.conf'),
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'apps', 'search', 'local', 'indexes.conf'),
            os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'etc', 'system', 'default', 'indexes.conf')
        ]
        
        conf_path = None
        for path in conf_locations:
            if os.path.exists(path):
                conf_path = path
                break
        
        if not conf_path:
            # If we can't find it, ask the user
            root = Tk()
            root.withdraw()
            messagebox.showinfo(
                "indexes.conf Location",
                "Could not automatically find indexes.conf.\n"
                "It's typically located in:\n"
                "etc/system/local/ or etc/apps/search/local/"
            )
            conf_path = filedialog.askopenfilename(
                title="Select indexes.conf file",
                filetypes=[("Config files", "*.conf")]
            )
            root.destroy()
            
            if not conf_path:
                self.print_warning("Could not update indexes.conf - index paths may need manual configuration")
                return False
        
        # Configuration to add
        config_content = f"""
[{index_name}]
coldPath = $SPLUNK_DB\\{index_name}\\colddb
enableDataIntegrityControl = 0
enableTsidxReduction = 0
homePath = $SPLUNK_DB\\{index_name}\\db
maxTotalDataSizeMB = 512000
thawedPath = $SPLUNK_DB\\{index_name}\\thaweddb
"""
        
        try:
            # Check if the index already exists in the config
            with open(conf_path, 'r') as f:
                content = f.read()
            
            # If the index section already exists, we'll replace it
            if f"[{index_name}]" in content:
                # Find the existing section and remove it
                start_idx = content.find(f"[{index_name}]")
                end_idx = content.find("\n\n", start_idx)  # Look for double newline as section end
                if end_idx == -1:
                    end_idx = len(content)
                
                new_content = content[:start_idx] + config_content + content[end_idx:]
            else:
                # Just append the new configuration
                new_content = content + "\n" + config_content
            
            # Write the updated content back to the file
            with open(conf_path, 'w') as f:
                f.write(new_content)
            
            self.print_success(f"Updated {conf_path} with {index_name} configuration")
            return True
        
        except Exception as e:
            self.print_warning(f"Could not update indexes.conf: {str(e)}")
            self.print_warning("You may need to manually add the index configuration")
            return False

    def main_menu(self):
        """Display the main menu"""
        while True:
            self.print_divider()
            print(f"\n{Style.BOLD}{Style.BLUE}📋 Splunk Index Management Tool{Style.END}")
            print(f"{Style.BLUE}1:{Style.END} 🆕 Create an index")
            print(f"{Style.BLUE}2:{Style.END} 🛠  Manage indexes")
            print(f"{Style.BLUE}3:{Style.END} 💾 Restore from backup")
            print(f"{Style.BLUE}0:{Style.END} 🚪 Exit")
            
            choice = input(f"\n{Style.PROMPT} Enter your choice: ")
            
            if choice == "1":
                self.create_index_menu()
            elif choice == "2":
                self.manage_indexes_menu()
            elif choice == "3":
                self.restore_backup_menu()
            elif choice == "0":
                self.print_success("Goodbye!")
                break
            else:
                self.print_error("Invalid choice, please try again.")

    def create_index_menu(self):
        """Menu for creating a new index"""
        self.print_divider()
        print(f"\n{Style.BOLD}🆕 Create New Index{Style.END}")
        index_name = input(f"{Style.PROMPT} Enter the name for the new index: ")
        
        if not index_name:
            self.print_error("Index name cannot be empty.")
            return
            
        success, message = self.create_index(index_name)
        if success:
            self.print_success(message)
        else:
            self.print_error(message)

    def manage_indexes_menu(self):
        """Menu for managing existing indexes"""
        self.print_divider()
        print(f"\n{Style.BOLD}🛠 Manage Indexes{Style.END}")
        indexes = self.list_indexes()
        
        if not indexes:
            self.print_warning("No non-system indexes found.")
            return
            
        print(f"\n{Style.BLUE}📋 Available indexes:{Style.END}")
        for i, index in enumerate(indexes, 1):
            print(f"{Style.BLUE}{i}:{Style.END} {index}")
        print(f"{Style.BLUE}0:{Style.END} ↩ Back to main menu")
        
        try:
            choice = input(f"\n{Style.PROMPT} Select an index to manage: ")
            if choice == "0":
                return
            choice = int(choice)
            if 1 <= choice <= len(indexes):
                # Pass the complete display string (with size) to operations menu
                self.index_operations_menu(indexes[choice-1])
            else:
                self.print_error("Invalid selection.")
        except ValueError:
            self.print_error("Please enter a number.")
            
    def index_operations_menu(self, index_display):
        """Menu for operations on a specific index (index_display includes size info)"""
        # Extract just the index name (before the "-" for size)
        index_name = index_display.split(' - ')[0].strip()
        
        while True:
            self.print_divider()
            print(f"\n{Style.BOLD}🛠 Operations for index:{Style.END} {Style.BLUE}{index_display}{Style.END}")
            print(f"{Style.BLUE}1:{Style.END} 🗑 Delete index")
            print(f"{Style.BLUE}2:{Style.END} 💾 Backup index")
            print(f"{Style.BLUE}3:{Style.END} 💾🗑 Backup and delete index")
            print(f"{Style.BLUE}0:{Style.END} ↩ Back to index list")
            
            choice = input(f"\n{Style.PROMPT} Enter your choice: ")
            
            if choice == "1":
                confirm = input(f"\n{Style.RED}⚠ Are you absolutely sure you want to permanently delete index '{index_name}'? (y/n): {Style.END}")
                if confirm.lower() == 'y':
                    success, message = self.delete_index(index_name)  # Use cleaned index_name
                    if success:
                        self.print_success(message)
                    else:
                        self.print_error(message)
                else:
                    self.print_warning("Index deletion cancelled.")
                break
                
            elif choice == "2":
                self.backup_index_menu(index_name)  # Use cleaned index_name
                break
                
            elif choice == "3":
                if self.backup_index_menu(index_name):  # Use cleaned index_name
                    confirm = input(f"\n{Style.RED}⚠ Are you absolutely sure you want to permanently delete index '{index_name}'? (y/n): {Style.END}")
                    if confirm.lower() == 'y':
                        success, message = self.delete_index(index_name)  # Use cleaned index_name
                        if success:
                            self.print_success(message)
                        else:
                            self.print_error(message)
                    else:
                        self.print_warning("Index deletion cancelled.")
                break
                
            elif choice == "0":
                break
            else:
                self.print_error("Invalid choice, please try again.")

                
    def delete_index_menu(self, index_name):
        """Menu for deleting an index"""
        confirm = input(f"\n{Style.RED}⚠ Are you absolutely sure you want to permanently delete index '{index_name}'? (y/n): {Style.END}")
        if confirm.lower() == 'y':
            success, message = self.delete_index(index_name)
            if success:
                self.print_success(message)
            else:
                self.print_error(message)
        else:
            self.print_warning("Index deletion cancelled.")
                
    def backup_index_menu(self, index_name):
        """Menu for backing up an index - returns True if backup was initiated"""
        print(f"\n{Style.BLUE}📁 Select backup directory{Style.END}")
        backup_dir = input(f"{Style.PROMPT} Enter backup directory path (or leave blank to browse): ")
        
        if not backup_dir:
            root = Tk()
            root.withdraw()
            backup_dir = filedialog.askdirectory(title="Select backup directory")
            root.destroy()
            
        if not backup_dir:
            self.print_warning("Backup cancelled.")
            return False
            
        password = None
        use_password = input(f"{Style.PROMPT} Would you like to password protect the backup? (y/n): ")
        if use_password.lower() == 'y':
            password = getpass.getpass(f"{Style.PROMPT} Enter backup password: ")
            
        success, message = self.backup_index(index_name, backup_dir, password)
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        return success

    def restore_backup_menu(self):
        """Menu for restoring from backup"""
        self.print_divider()
        print(f"\n{Style.BOLD}💾 Restore from Backup{Style.END}")
        root = Tk()
        root.withdraw()
        
        backup_file = filedialog.askopenfilename(
            title="Select backup file to restore",
            filetypes=[("ZIP files", "*.zip")]
        )
        root.destroy()
        
        if not backup_file:
            self.print_warning("Restore cancelled.")
            return
        
        if not self.confirm_restore():
            self.print_warning("Restore cancelled.")
            return
        
        success, message = self.restore_backup(backup_file)
        if success:
            self.print_success(message)
        else:
            self.print_error(message)

    def confirm_restore(self):
        """Confirm the user wants to proceed with restore"""
        root = Tk()
        root.withdraw()
        response = messagebox.askyesno(
            "Confirm Restore",
            "WARNING: This will overwrite any existing index data.\n\n"
            "Are you sure you want to continue?"
        )
        root.destroy()
        return response

if __name__ == "__main__":
    try:
        manager = SplunkManager()
        manager.main_menu()
    except KeyboardInterrupt:
        print("\n\n" + Style.HEADER)
        print(f"{Style.RED}{Style.ERROR} Operation cancelled by user{Style.END}")
        print(Style.HEADER + "\n")
    except Exception as e:
        print("\n\n" + Style.HEADER)
        print(f"{Style.RED}{Style.ERROR} Critical error: {str(e)}{Style.END}")
        print(Style.HEADER + "\n")
