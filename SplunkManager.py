import os
import json
import subprocess
import getpass
import time
import zipfile
import shutil
from tkinter import Tk, filedialog, messagebox, ttk, Label, Button
from tkinter.ttk import Progressbar
import tkinter as tk
from threading import Thread
from queue import Queue


# ───────────────────────────────────────────────
# Developed by Jacob Wilson - Version 0.1
# dfirvault@gmail.com
# ───────────────────────────────────────────────

print("\nDeveloped by Jacob Wilson - Version 0.1")
print("dfirvault@gmail.com\n")

CONFIG_FILE = "config.txt"

class SplunkManager:
    def __init__(self):
        self.splunk_path = ""
        self.username = ""
        self.password = ""
        self.load_config()
        self.verify_splunk()
        
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
        common_paths = [
            "/opt/splunk/bin/splunk",
            "C:\\Program Files\\Splunk\\bin\\splunk.exe",
            "/Applications/Splunk/bin/splunk"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                use_default = messagebox.askyesno(
                    "Splunk Path Found",
                    f"Splunk binary found at {path}. Use this location?"
                )
                if use_default:
                    self.splunk_path = path
                    return
        
        # If not found in common locations, ask user
        messagebox.showinfo(
            "Splunk Path",
            "Please select the Splunk binary (splunk or splunk.exe)"
        )
        self.splunk_path = filedialog.askopenfilename(
            title="Select Splunk binary"
        )
        
    def prompt_credentials(self):
        """Prompt user for Splunk credentials"""
        root = Tk()
        root.withdraw()
        
        self.username = input("Enter Splunk username: ")
        self.password = getpass.getpass("Enter Splunk password: ")
        
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
            print("Splunk binary not found at specified path.")
            self.prompt_splunk_path()
            self.save_config()
            
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
                print("Login failed with provided credentials.")
                self.prompt_credentials()
                self.save_config()
                self.verify_splunk()
            else:
                # Add success message
                print("\nSuccessfully connected to Splunk service!")
                print(f"Using Splunk binary at: {self.splunk_path}")
                print(f"Authenticated as user: {self.username}\n")
        except Exception as e:
            print(f"Error testing Splunk connection: {e}")
            self.prompt_splunk_path()
            self.save_config()
            self.verify_splunk()
            
    def run_splunk_command(self, command):
        """Run a Splunk CLI command"""
        full_cmd = [self.splunk_path] + command
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                shell=True if os.name == 'nt' else False
            )
            return result.stdout + result.stderr
        except Exception as e:
            print(f"Error running Splunk command: {e}")
            return None
            
    def create_index(self, index_name):
        """Create a new Splunk index"""
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
        
    def list_indexes(self):
        """List all indexes excluding system and special indexes"""
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
            'main',
            'history'
        }
        
        indexes = []
        for line in result.split('\n'):
            line = line.strip()
            # Skip empty lines and paths
            if not line or '\\' in line or '/' in line:
                continue
            
            # Check if index should be excluded
            if any(line.lower().startswith(excluded) for excluded in excluded_indexes):
                continue
                
            indexes.append(line)
        
        return indexes
        
    def delete_index(self, index_name):
        """Delete a Splunk index"""
        result = self.run_splunk_command([
            'remove', 'index', index_name,
            '-auth', f'{self.username}:{self.password}'
        ])
        
        if result is None:
            return False, "Failed to execute Splunk command"
            
        normalized_output = ' '.join(result.lower().split())
        success_phrases = ['removed', 'deleted', 'removal of index', 'successfully']
        
        if any(phrase in normalized_output for phrase in success_phrases):
            return True, f"Index '{index_name}' deleted successfully."
        elif "error" in normalized_output or "failed" in normalized_output:
            return False, f"Splunk error: {result.strip()}"
            
        return False, f"Unexpected response: {result.strip()}"
        
    def backup_index(self, index_name, backup_dir, password=None):
        """Backup an entire index folder (including empty subfolders) and its .dat file"""
        # Get the Splunk DB parent directory
        splunk_db = os.path.join(os.path.dirname(os.path.dirname(self.splunk_path)), 'var', 'lib', 'splunk')
        
        # Paths we want to back up
        index_folder = os.path.join(splunk_db, index_name)
        dat_file = os.path.join(splunk_db, f"{index_name}.dat")

        print(f"\nBacking up index data from:")
        if os.path.exists(dat_file):
            print(f" - DAT file: {dat_file}")
        print(f" - Index folder: {index_folder}")
        
        if not os.path.exists(index_folder) and not os.path.exists(dat_file):
            return False, f"No index data found (neither folder nor .dat file exists)"
        
        # Create backup
        zip_filename = os.path.join(backup_dir, f"{index_name}_backup_{time.strftime('%Y%m%d-%H%M%S')}.zip")
        start_time = time.time()
        
        try:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add .dat file if exists
                if os.path.exists(dat_file):
                    zipf.write(dat_file, os.path.basename(dat_file))
                    print(f"Added .dat file to backup")
                
                # Add entire index folder structure
                if os.path.exists(index_folder):
                    # First add empty directories
                    for root, dirs, files in os.walk(index_folder):
                        for dir in dirs:
                            dir_path = os.path.join(root, dir)
                            # Create relative path for zip
                            arcname = os.path.join(
                                os.path.basename(index_folder),
                                os.path.relpath(dir_path, index_folder)
                            )
                            # Add empty directory
                            zipf.write(dir_path, arcname)
                            print(f"Added empty directory: {arcname}")
                    
                    # Then add files
                    file_count = 0
                    for root, dirs, files in os.walk(index_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(
                                os.path.basename(index_folder),
                                os.path.relpath(file_path, index_folder)
                            )
                            zipf.write(file_path, arcname)
                            file_count += 1
                            
                            # Update progress every 10 files
                            if file_count % 10 == 0:
                                print(f"Added {file_count} files...")
                    
                    print(f"Added {file_count} files from index folder")
                
                if password:
                    zipf.setpassword(password.encode())
            
            time_taken = time.time() - start_time
            return True, (f"\nBackup completed successfully in {time_taken:.1f} seconds!\n"
                         f"Saved to: {zip_filename}\n"
                         f"Includes empty directories: Yes")
        except Exception as e:
            return False, f"Backup failed: {str(e)}"


    def _print_progress(self, processed, total, start_time):
        """Helper method to print progress information"""
        progress = (processed / total) * 100
        elapsed = time.time() - start_time
        if processed > 0:
            remaining = (elapsed / processed) * (total - processed)
        else:
            remaining = 0
        
        # Clear previous line and print new progress
        print(f"\rProgress: {processed}/{total} files ({progress:.1f}%) | "
              f"Elapsed: {elapsed:.1f}s | "
              f"Remaining: {remaining:.1f}s", end="", flush=True)
        
    def main_menu(self):
        """Display the main menu"""
        while True:
            print("\nSplunk Index Management Tool")
            print("1: Create an index")
            print("2: Manage an index")
            print("3: Restore from backup")
            print("0: Exit")
            
            choice = input("Enter your choice: ")
            
            if choice == "1":
                self.create_index_menu()
            elif choice == "2":
                self.manage_index_menu()
            elif choice == "3":
                self.restore_backup_menu()
            elif choice == "0":
                break
            else:
                print("Invalid choice, please try again.")

    def restore_backup_menu(self):
        """Menu for restoring from backup"""
        print("\nRestore from Backup")
        root = Tk()
        root.withdraw()
        
        backup_file = filedialog.askopenfilename(
            title="Select backup file to restore",
            filetypes=[("ZIP files", "*.zip")]
        )
        root.destroy()
        
        if not backup_file:
            print("Restore cancelled.")
            return
        
        if not self.confirm_restore():
            print("Restore cancelled.")
            return
        
        success, message = self.restore_backup(backup_file)
        print(message)

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

    def restore_backup(self, backup_file):
        """Restore an index from backup zip file"""
        splunk_db = os.path.join(
            os.path.dirname(os.path.dirname(self.splunk_path)),
            'var', 'lib', 'splunk'
        )
        
        if not os.path.exists(backup_file):
            return False, "Backup file not found"
        
        print(f"\nRestoring backup from: {backup_file}")
        print(f"Target location: {splunk_db}")
        
        try:
            # Extract the index name from the backup filename
            base_name = os.path.basename(backup_file)
            index_name = base_name.split('_backup_')[0]
            
            # Track what we're restoring
            restoring_dat = False
            restoring_folder = False
            
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                # First check what we have in the backup
                for file in zip_ref.namelist():
                    if file.endswith('.dat'):
                        restoring_dat = True
                    elif file.startswith(f'{index_name}/'):
                        restoring_folder = True
                
                # Restore .dat file if present
                if restoring_dat:
                    dat_file = f"{index_name}.dat"
                    print(f"\nRestoring {dat_file}...")
                    zip_ref.extract(dat_file, splunk_db)
                    print(f"Restored {dat_file} to {splunk_db}")
                
                # Restore folder if present
                if restoring_folder:
                    print(f"\nRestoring {index_name} folder...")
                    for file in zip_ref.namelist():
                        if file.startswith(f'{index_name}/'):
                            zip_ref.extract(file, splunk_db)
                    print(f"Restored {index_name} folder to {splunk_db}")
                
                # Verify the index exists in Splunk
                if not self.index_exists(index_name):
                    print(f"\nCreating index {index_name} in Splunk...")
                    success, message = self.create_index(index_name)
                    if not success:
                        return False, f"Restore failed: {message}"
                
            return True, (f"\nRestore completed successfully!\n"
                         f"Index: {index_name}\n"
                         f"Location: {splunk_db}")
        
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    def index_exists(self, index_name):
        """Check if an index exists in Splunk"""
        indexes = self.list_indexes()
        return index_name in indexes
    def create_index_menu(self):
        """Menu for creating a new index"""
        print("\nCreate New Index")
        index_name = input("Enter the name for the new index: ")
        
        if not index_name:
            print("Index name cannot be empty.")
            return
            
        success, message = self.create_index(index_name)
        print(message)
            
    def manage_index_menu(self):
        """Menu for managing existing indexes"""
        print("\nManage Indexes")
        indexes = self.list_indexes()
        
        if not indexes:
            print("No non-system indexes found.")
            return
            
        print("\nAvailable indexes:")
        for i, index in enumerate(indexes, 1):
            print(f"{i}: {index}")
        print("0: Back to main menu")
        
        try:
            choice = input("Select an index to manage: ")
            if choice == "0":
                return
            choice = int(choice)
            if 1 <= choice <= len(indexes):
                selected_index = indexes[choice-1]
                self.index_operations_menu(selected_index)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")
            
    def index_operations_menu(self, index_name):
        """Menu for operations on a specific index"""
        while True:
            print(f"\nOperations for index: {index_name}")
            print("1: Delete index")
            print("2: Backup index")
            print("3: Backup and delete index")
            print("0: Back to index list")
            
            choice = input("Enter your choice: ")
            
            if choice == "1":
                self.delete_index_menu(index_name)
                break
            elif choice == "2":
                self.backup_index_menu(index_name)
            elif choice == "3":
                if self.backup_index_menu(index_name):
                    self.delete_index_menu(index_name)
                break
            elif choice == "0":
                break
            else:
                print("Invalid choice, please try again.")
                
    def delete_index_menu(self, index_name):
        """Menu for deleting an index"""
        confirm = input(f"\nAre you absolutely sure you want to permanently delete index '{index_name}'? (y/n): ")
        if confirm.lower() == 'y':
            success, message = self.delete_index(index_name)
            print(message)
        else:
            print("Index deletion cancelled.")
                
    def backup_index_menu(self, index_name):
        """Menu for backing up an index"""
        print("\nSelect backup directory")
        backup_dir = input("Enter backup directory path (or leave blank to browse): ")
        
        if not backup_dir:
            root = Tk()
            root.withdraw()
            backup_dir = filedialog.askdirectory(title="Select backup directory")
            root.destroy()
            
        if not backup_dir:
            print("Backup cancelled.")
            return False
            
        password = None
        use_password = input("Would you like to password protect the backup? (y/n): ")
        if use_password.lower() == 'y':
            password = getpass.getpass("Enter backup password: ")
            
        success, message = self.backup_index(index_name, backup_dir, password)
        print(message)
        return success

if __name__ == "__main__":
    manager = SplunkManager()
    manager.main_menu()
