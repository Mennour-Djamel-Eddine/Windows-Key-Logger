# PyLoggy - Advanced Polymorphic Keylogger & Surveillance Tool

## 1. Project Overview

**PyLoggy** is an advanced Python-based surveillance tool designed to demonstrate sophisticated malware techniques including polymorphic evasion, stealth persistence, and anonymous data exfiltration over the Tor network. The project is modular, separating the core surveillance logic (`PyLoggy.py`) from the communication infrastructure (`Sender/Receiver_setup.py`), demonstrating a complete C2 (Command & Control) architecture.

## 2. Technical Architecture

The system operates on a client-server architecture leveraging the **Tor Anonymity Network** for secure, encrypted, and anonymous communication.

*   **Client (Target System - Windows):** Executes the surveillance payload (`PyLoggy.py`), collects intelligence, and uses a bundled Tor client to exfiltrate data to a Hidden Service (.onion).
*   **Server (Attacker System - Linux):** Hosts a Tor Hidden Service that proxies incoming traffic to a local Flask application (`Receiver_setup.py`), which stores the exfiltrated logs.

## 3. Detailed Feature Analysis

### 3.1. Advanced Surveillance Capabilities

*   **Keystroke Logging (`PyLoggy.py`)**: 
    *   Utilizes the `pynput` library to hook low-level keyboard events.
    *   Captures all alphanumeric keys and special characters.
    *   **Context-Aware Logging**: Captures the active window title (using `pygetwindow`) for every keystroke to provide context on user activity (e.g., differentiating between a Facebook password and a Notepad entry).

*   **Mouse Activity Monitoring**:
    *    Logs mouse clicks (Left/Right/Middle) and coordinate positions (X, Y).
    *   Designed to capture virtual keyboard inputs or graphical interactions.

*   **Clipboard Monitoring (`clipboard_monitor.py`)**:
    *   Implements a dedicated thread to monitor the Windows Clipboard.
    *   Uses `ctypes` to interface directly with Windows API functions (`OpenClipboard`, `GetClipboardData`, `GlobalLock`) to capture copied text, essential for stealing passwords or cryptocurrency addresses copied by the user.

*   **System Reconnaissance (`system_recon.py`)**:
    *   Executes automatically on startup to fingerprint the host.
    *   **Collected Data**: Public IP (via external API), MAC Address (for unique identification), OS Version/Architecture, Processor details, and User/Hostname.
    *   **Security Product Detection**: Queries WMI (`root\SecurityCenter2`) to detect installed Antivirus products, allowing the malware to potentially alter its behavior based on the security environment.

### 3.2. Polymorphic Evasion Engine (`polymorphic_evasion.py`)

To defeat signature-based and heuristic analysis, PyLoggy incorporates a custom polymorphic engine:

*   **Dynamic Module Loading**: 
    *   Critical imports (`winreg`, `pynput`) are not imported globally but loaded dynamically at runtime using a custom `DynamicLoader`. This prevents these sensitive APIs from appearing in the Import Address Table (IAT), bypassing static analysis scanners that flag executables based on imported functions.
*   **Behavioral Obfuscation**:
    *   **Randomized Execution**: The keylogger introduces random sleep intervals (`time.sleep`) between operations to disrupt sandbox analysis and behavior monitoring tools that look for rapid, sequential API calls.
    *   **Variable Buffer Sizes**: Network packet sizes and log buffer thresholds are randomized to avoid consistent network traffic signatures.
*   **Polymorphic Persistence**:
    *   Instead of using a static registry key name (which triggers AV signatures), the engine generates random, legitimate-sounding names (e.g., "Windows Security Update", "System Configuration Manager") for its startup entry every time it installs.

### 3.3. Stealth & Persistence Mechanisms

*   **Registry Persistence**: 
    *   Adds an entry to the Windows Registry Key `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` to ensure execution on every user login.
*   **File Hiding**:
    *   Uses `ctypes.windll.kernel32.SetFileAttributesW` to set the `FILE_ATTRIBUTE_HIDDEN` (0x02) flag on its own directory and log files, making them invisible to the default Windows Explorer view.
*   **Process Hiding**:
    *   When compiled or run, the script uses `ctypes.windll.user32.ShowWindow` to hide the console window, ensuring the process runs invisibly in the background.

### 3.4. Anonymous Data Exfiltration (Tor)

*   **Sender Module (`Sender_setup.py`)**:
    *   **Bundled Tor Client**: Includes a portable Tor binary to establish a secure connection without requiring Tor to be installed on the target machine.
    *   **SOCKS5 Proxy**: Routes all HTTP POST requests through a local SOCKS5 proxy (`127.0.0.1:9050`) created by the bundled Tor process.
    *   **Firewall Bypass**: Since traffic is outbound over standard ports (routed through Tor circuits), it bypasses most NATs and firewalls without requiring port forwarding.

*   **Receiver Module (`Receiver_setup.py`)**:
    *   **Tor Hidden Service**: Automatically configures a Tor Hidden Service on the attacker's machine. This generates a `.onion` address that completely anonymizes the attacker's IP location.
    *   **Flask C2 Server**: A lightweight Python Flask server listens on the localhost, receiving data forwarded by the Tor service.
    *   **Data Integrity**: Incoming logs are saved with timestamps to prevent overwriting and allow for chronological reconstruction of the target's activities.

## 4. File Structure & Components

*   **`src/PyLoggy.py`**: The main payload. Initializes hooks, persistence, and the polymorphic engine.
*   **`src/polymorphic_evasion.py`**: The core evasion logic (Dynamic imports, randomizer, name generator).
*   **`src/system_recon.py`**: Module for gathering victim system information.
*   **`src/clipboard_monitor.py`**: Module for capturing clipboard contents.
*   **`src/Sender_setup.py`**: Handles the Tor connection and reliable file transmission from the victim.
*   **`src/Receiver_setup.py`**: Server-side script to set up the Listening Post (Hidden Service + Flask App).

## 5. How to Use (Educational Lab Setup)

**Prerequisites:**
*   **Linux Machine (Attacker)**: Python 3, `tor`, `flask`
*   **Windows Machine (target)**: Python 3, `pynput`, `pygetwindow`, `requests`, `pysocks`

### Step 1: Set Up the Receiver (Linux)
1.  **Install Dependencies**:
    ```bash
    sudo apt update && sudo apt install tor
    pip install flask
    ```
2.  **Run the Receiver Script**:
    ```bash
    sudo python3 src/Receiver_setup.py
    ```
    *   The script will configure Tor, restart the service, and display a unique **.onion address**.
    *   Copy this address.

### Step 2: Configure the Client (Windows)
1.  **Edit `src/Sender_setup.py`**:
    *   Open the file and locate the `ONION` variable.
    *   Replace the placeholder with the .onion address from Step 1.
    ```python
    ONION = "your_generated_onion_address.onion"
    ```
2.  **Deploy**:
    *   Run `src/PyLoggy.py` on the Windows machine.
    *   The script will begin logging in the background.

### Step 3: Verify Data Exfiltration
1.  Check the `received_files` directory on your Linux machine (created by `Receiver_setup.py`).
2.  Incoming logs will appear as timestamped `.bin` or `.txt` files.

---

## 📢 Legal Disclaimer & Educational Purpose

**⚠️ IMPORTANT: PLEASE READ CAREFULLY ⚠️**

This project, **PyLoggy**, is a **University Research Project** developed strictly for **educational and defensive cybersecurity research purposes**. 

*   **Academic Context**: This code was created to demonstrate how malware, C2 infrastructure, and polymorphic evasion techniques operate in a controlled environment. The goal is to help security researchers and students understand attack vectors to build better defenses.
*   **No Malicious Intent**: The author does not condone or support the use of this software for malicious activities.
*   **Restricted Use**: This tool should **ONLY** be used on systems you explicitly own or have written permission to test. Unauthorized access to computer systems is illegal and punishable by law.
*   **Platform Compliance**: This repository is hosted on GitHub for academic archiving and portfolio demonstration. It does not contain pre-compiled binaries or active exploits targeting specific vulnerabilities.

**By accessing this repository, you agree to use the information contained herein for educational purposes only.**
