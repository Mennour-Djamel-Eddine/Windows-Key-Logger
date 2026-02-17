import os
import subprocess
import time
from flask import Flask, request

# Tor Hidden Service Configuration
HS_DIR = "/var/lib/tor/auto_receiver/"
TORRC_PATH = "/etc/tor/torrc"

def ensure_dirs():
    # Ensure Tor data directory exists with correct permissions
    if not os.path.exists(HS_DIR):
        os.makedirs(HS_DIR, exist_ok=True)

    # Set ownership to debian-tor (required for Tor service)
    subprocess.run(["sudo", "chown", "-R", "debian-tor:debian-tor", HS_DIR])
    subprocess.run(["sudo", "chmod", "700", HS_DIR])
    
    # Ensure local storage directory exists
    received_dir = "/home/djamel/received_files"
    if not os.path.exists(received_dir):
        os.makedirs(received_dir, exist_ok=True)
        print(f"Created directory: {received_dir}")

def write_tor_config():
    # Read existing config
    with open(TORRC_PATH, "r") as f:
        lines = f.readlines()

    # Clean up previous hidden service configurations
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip existing HiddenServiceDir block
        if f"HiddenServiceDir {HS_DIR}" in line:
            i += 1
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped.startswith("HiddenServicePort"):
                    i += 1
                    continue
                if next_stripped.startswith("HiddenServiceAuthorizeClient"):
                    i += 1
                    continue
                if next_stripped.startswith("#") and ("Auto-generated" in lines[i] or "hidden service" in lines[i].lower()):
                    i += 1
                    continue
                if next_stripped == "" or (not next_stripped.startswith("#") and not next_stripped.startswith("HiddenService")):
                    break
                break
            continue
        
        # Remove any orphaned HiddenServicePort lines for port 5000
        if stripped.startswith("HiddenServicePort") and "127.0.0.1:5000" in line:
            i += 1
            continue
        
        # Remove ALL HiddenServiceAuthorizeClient lines (they're obsolete)
        if stripped.startswith("HiddenServiceAuthorizeClient"):
            i += 1
            continue
        
        # Keep all other lines
        new_lines.append(line)
        i += 1
    
    # Write cleaned config
    with open(TORRC_PATH, "w") as f:
        f.writelines(new_lines)
    
    # Append new hidden service configuration
    config_block = f"""# Hidden Service for Receiver
HiddenServiceDir {HS_DIR}
HiddenServicePort 80 127.0.0.1:5000
"""
    with open(TORRC_PATH, "a") as f:
        f.write(config_block)
    print(f"Added/updated hidden service config in {TORRC_PATH}")
    
    # Verify the config syntax
    print("Verifying Tor configuration...")
    result = subprocess.run(["sudo", "tor", "--verify-config", "-f", TORRC_PATH], 
                          capture_output=True, text=True)
    
    # Check for real errors
    has_real_error = False
    error_message = ""
    
    if result.returncode != 0:
        # Check for specific critical errors
        if "HiddenServicePort with no preceding HiddenServiceDir" in result.stdout:
            has_real_error = True
            error_message = "Orphaned HiddenServicePort lines detected"
        elif "Failed to parse/validate config" in result.stdout:
            # Ignore ownership warnings when running verification as root
            if "is not owned by this user" in result.stdout:
                print("Note: Ownership warning is expected when verifying config as root.")
            else:
                has_real_error = True
                error_message = "Configuration parsing failed"
        else:
            has_real_error = True
            error_message = "Unknown configuration error"
    
    if has_real_error:
        print(f"\nERROR: {error_message}")
        print(f"stderr: {result.stderr}")
        print(f"stdout: {result.stdout}")
        raise RuntimeError(f"Tor configuration has errors: {error_message}")
    else:
        print("Tor configuration verified successfully")

def check_tor_logs():
    """Check recent Tor logs for errors"""
    print("\nChecking Tor logs for errors...")
    result = subprocess.run(["sudo", "journalctl", "-u", "tor", "-n", "50", "--no-pager"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        logs = result.stdout
        # Look for hidden service specific messages
        hs_errors = []
        other_errors = []
        
        for line in logs.split('\n'):
            line_lower = line.lower()
            # Check for hidden service related errors
            if 'hiddenservice' in line_lower or 'hidden service' in line_lower:
                if any(keyword in line_lower for keyword in ['error', 'failed', 'warn', 'cannot', 'unable']):
                    hs_errors.append(line)
            # Check for other errors
            elif any(keyword in line_lower for keyword in ['error', 'failed', 'warn', 'cannot', 'unable']):
                other_errors.append(line)
        
        if hs_errors:
            print("Found hidden service related issues:")
            for line in hs_errors[:10]:  # Limit output
                print(f"  {line}")
        
        if other_errors:
            print("Found other potential issues:")
            for line in other_errors[:10]:  # Limit output
                print(f"  {line}")
        
        if not hs_errors and not other_errors:
            print("No obvious errors in recent Tor logs")
            # Still print last few lines for context
            print("\nLast few log lines:")
            for line in logs.split('\n')[-5:]:
                if line.strip():
                    print(f"  {line}")
    else:
        print("Could not retrieve Tor logs")

def restart_tor():
    # Full restart required for Hidden Service configuration changes
    print("Restarting Tor service...")
    result = subprocess.run(["sudo", "systemctl", "restart", "tor"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Tor restart returned code {result.returncode}")
        print(f"stderr: {result.stderr}")
        raise RuntimeError("Failed to restart Tor service")
    
    # Wait for Tor to fully start and bootstrap
    print("Waiting for Tor to start and bootstrap...")
    time.sleep(8)  # Give Tor more time to initialize
    
    # Verify Tor is running
    check_result = subprocess.run(["sudo", "systemctl", "is-active", "tor"], capture_output=True, text=True)
    if check_result.stdout.strip() != "active":
        check_tor_logs()
        raise RuntimeError("Tor service is not active after restart. Check Tor logs with: sudo journalctl -u tor")
    
    print("Tor service is active")
    
    # Check logs for any configuration issues
    check_tor_logs()
    
    # Additional check: see if Tor is actually bootstrapped
    print("Checking if Tor has bootstrapped...")
    result = subprocess.run(["sudo", "journalctl", "-u", "tor", "-n", "50", "--no-pager"], 
                          capture_output=True, text=True)
    if "Bootstrapped 100%" in result.stdout:
        print("Tor has successfully bootstrapped")
    else:
        print("Warning: Tor may still be bootstrapping. Hidden service creation may take longer.")

def get_onion_info():
    with open(os.path.join(HS_DIR, "hostname")) as f:
        onion = f.read().strip()
    return onion

def start_receiver():
    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def receive():
        data = request.get_data()
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"received_data_{timestamp}.bin"
        save_path = f"/home/djamel/received_files/{filename}" 
        
        try:
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"Received data saved to: {save_path}")
        except Exception as e:
            print(f"Error saving data: {e}")
            return "Server Error", 500
        
        return "OK", 200
    
    print("Receiver running on localhost:5000…")
    app.run("127.0.0.1", 5000)

def wait_for_onion_files(timeout=60):
    hostname_path = os.path.join(HS_DIR, "hostname")

    print(f"Waiting for Tor to create onion hostname file (timeout: {timeout}s)...")
    print(f"  - Hostname file: {hostname_path}")
    
    start = time.time()
    last_status_time = start
    
    while True:
        hostname_exists = os.path.exists(hostname_path)
        
        # Print status every 5 seconds
        if time.time() - last_status_time >= 5:
            print(f"  Status: hostname={hostname_exists}")
            last_status_time = time.time()
        
        if hostname_exists:
            print("Onion hostname file created successfully!")
            break
            
        if time.time() - start > timeout:
            print(f"\nTimeout after {timeout} seconds.")
            print(f"  hostname exists: {hostname_exists}")
            
            # Check Tor logs for errors
            check_tor_logs()
            
            # Check if the directory has the right permissions
            print("\nChecking directory permissions...")
            result = subprocess.run(["sudo", "ls", "-la", HS_DIR], capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            
            # Check if Tor can see the config
            print("\nChecking if Tor configuration is loaded...")
            result = subprocess.run(["sudo", "grep", "-A", "2", HS_DIR, TORRC_PATH], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Config found in torrc:")
                print(result.stdout)
            else:
                print("WARNING: Config not found in torrc!")
            
            print("\nTroubleshooting:")
            print("  1. Check Tor logs: sudo journalctl -u tor -n 50")
            print("  2. Verify Tor is running: sudo systemctl status tor")
            print("  3. Try reloading Tor config: sudo systemctl reload tor")
            print("  4. Check if Tor can read the config: sudo tor --verify-config -f /etc/tor/torrc")
            raise TimeoutError(f"Tor did not create onion hostname file within {timeout} seconds")
        
        time.sleep(1)


if __name__ == "__main__":
    ensure_dirs()
    write_tor_config()
    restart_tor()

    wait_for_onion_files()
    onion = get_onion_info()

    print("===== SHARE THIS WITH THE SENDER =====")
    print("Onion address:", onion)
    print("=======================================")

    start_receiver()
